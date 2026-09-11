from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import threading
import time
import unicodedata
import uuid

import pymupdf


DOCUMENT_TYPES = {".html": "html", ".htm": "html", ".pdf": "pdf"}
MAX_BYTES = 50 * 1024 * 1024


class DocumentText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.in_title = False
        self.title = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if not self.hidden:
            self.parts.append(data)


def normalized(value):
    return unicodedata.normalize("NFKC", value).casefold()


def valid_component(name):
    if not isinstance(name, str) or not name or len(name) > 160:
        raise ValueError("名前は1〜160文字で指定してください。")
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', name) or name.startswith(".") or name.endswith((".", " ")):
        raise ValueError("この名前はLinux・Windows共通では使用できません。")
    if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{number}" for number in range(1, 10)), *(f"LPT{number}" for number in range(1, 10))}:
        raise ValueError("Windowsの予約名は使用できません。")
    return name


class Library:
    def __init__(self, root, database):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, kind TEXT NOT NULL,
                title TEXT NOT NULL, summary TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '[]',
                body TEXT NOT NULL, size INTEGER NOT NULL, modified INTEGER NOT NULL,
                signature TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', custom_title INTEGER NOT NULL DEFAULT 0
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(text, tokenize='trigram');
        """)
        self.last_scan = {"indexed": 0, "errors": 0}

    def close(self):
        self.connection.close()

    def resolve(self, relative, allow_root=False):
        if not isinstance(relative, str) or "\\" in relative or "\x00" in relative or ":" in relative:
            raise ValueError("保存先の指定が不正です。")
        path = PurePosixPath(relative)
        if path.is_absolute() or any(part in ("..", ".") or part.startswith(".") for part in path.parts):
            raise ValueError("管理フォルダー外のパスは使用できません。")
        current = self.root
        for part in path.parts:
            current /= part
            if current.is_symlink():
                raise ValueError("シンボリックリンクは使用できません。")
        resolved = current.resolve()
        if not resolved.is_relative_to(self.root) or (resolved == self.root and not allow_root):
            raise ValueError("管理フォルダー外のパスは使用できません。")
        return resolved

    def directories(self):
        result = [""]
        for parent, folders, _ in os.walk(self.root, followlinks=False):
            folders[:] = sorted(name for name in folders if not name.startswith(".") and not (Path(parent) / name).is_symlink())
            result.extend((Path(parent) / name).relative_to(self.root).as_posix() for name in folders)
        return result

    def extract(self, path):
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("50MBを超える資料は本文索引・プレビューの対象外です。")
        if path.suffix.lower() == ".pdf":
            with pymupdf.open(path) as document:
                if document.needs_pass:
                    raise ValueError("パスワード付きPDFの本文は読み込めません。")
                if len(document) > 300:
                    raise ValueError("300ページを超えるPDFは本文索引の対象外です。")
                body = "\n".join(page.get_text() for page in document)
                title = document.metadata.get("title") or path.stem
                if not body.strip():
                    return title, "", "本文テキストがありません。スキャンPDFのOCRには未対応です。"
                return title, body[:2_000_000], ""
        parser = DocumentText()
        parser.feed(path.read_bytes().decode("utf-8-sig", errors="replace"))
        return " ".join(parser.title).strip() or path.stem, " ".join(parser.parts)[:2_000_000], ""

    def update_search(self, identity):
        row = self.connection.execute("SELECT * FROM documents WHERE id=?", (identity,)).fetchone()
        self.connection.execute("DELETE FROM search WHERE rowid=?", (identity,))
        if row:
            text = "\n".join((row["path"], row["title"], row["summary"], " ".join(json.loads(row["tags"])), row["body"]))
            self.connection.execute("INSERT INTO search(rowid,text) VALUES(?,?)", (identity, normalized(text)))

    def scan(self):
        with self.lock, self.connection:
            found = set()
            errors = 0
            for directory in self.directories():
                for path in sorted(self.resolve(directory, allow_root=True).iterdir()):
                    if path.is_symlink() or not path.is_file() or path.name.startswith(".") or path.suffix.lower() not in DOCUMENT_TYPES:
                        continue
                    relative = path.relative_to(self.root).as_posix()
                    found.add(relative)
                    stat = path.stat()
                    signature = f"{stat.st_mtime_ns}:{stat.st_size}"
                    previous = self.connection.execute("SELECT * FROM documents WHERE path=?", (relative,)).fetchone()
                    if previous and previous["signature"] == signature:
                        errors += bool(previous["error"])
                        continue
                    try:
                        title, body, error = self.extract(path)
                    except Exception:
                        title, body, error = path.stem, "", "本文を索引化できません。形式・サイズ・暗号化を確認してください。"
                    errors += bool(error)
                    if previous:
                        self.connection.execute("UPDATE documents SET title=?,body=?,size=?,modified=?,signature=?,error=? WHERE id=?", (previous["title"] if previous["custom_title"] else title, body, stat.st_size, stat.st_mtime_ns, signature, error, previous["id"]))
                        identity = previous["id"]
                    else:
                        cursor = self.connection.execute("INSERT INTO documents(path,kind,title,body,size,modified,signature,error) VALUES(?,?,?,?,?,?,?,?)", (relative, DOCUMENT_TYPES[path.suffix.lower()], title, body, stat.st_size, stat.st_mtime_ns, signature, error))
                        identity = cursor.lastrowid
                    self.update_search(identity)
            for row in self.connection.execute("SELECT id,path FROM documents").fetchall():
                if row["path"] not in found:
                    self.connection.execute("DELETE FROM documents WHERE id=?", (row["id"],))
                    self.update_search(row["id"])
            self.last_scan = {"indexed": len(found), "errors": errors}
            return self.last_scan

    def public(self, row, query=""):
        item = dict(row)
        body = item.pop("body")
        item.pop("signature")
        item.pop("custom_title")
        item["tags"] = json.loads(item["tags"])
        item["modified"] //= 1_000_000
        position = normalized(body).find(normalized(query.split()[0])) if query.split() else -1
        item["excerpt"] = re.sub(r"\s+", " ", body[max(0, position - 50):max(0, position - 50) + 200]).strip()
        return item

    def browse(self, query="", folder="", kind="", tag="", sort="modified", scope="all"):
        if len(query) > 512:
            raise ValueError("検索語は512文字以内で指定してください。")
        self.resolve(folder, allow_root=True)
        with self.lock:
            parameters = []
            conditions = []
            terms = normalized(query).split()
            long_terms = [term for term in terms if len(term) >= 3]
            if long_terms:
                conditions.append("id IN (SELECT rowid FROM search WHERE search MATCH ?)")
                parameters.append(" AND ".join('"' + term.replace('"', '""') + '"' for term in long_terms))
            for term in (term for term in terms if len(term) < 3):
                conditions.append("id IN (SELECT rowid FROM search WHERE instr(text,?)>0)")
                parameters.append(term)
            if kind in ("html", "pdf"):
                conditions.append("kind=?")
                parameters.append(kind)
            statement = "SELECT * FROM documents" + (" WHERE " + " AND ".join(conditions) if conditions else "")
            order = {"modified": "modified DESC", "title": "title COLLATE NOCASE", "path": "path COLLATE NOCASE"}.get(sort, "modified DESC")
            rows = self.connection.execute(statement + " ORDER BY " + order, parameters).fetchall()
            items = []
            for row in rows:
                parent = str(PurePosixPath(row["path"]).parent)
                parent = "" if parent == "." else parent
                if scope == "folder" and parent != folder:
                    continue
                if tag and tag not in json.loads(row["tags"]):
                    continue
                items.append(self.public(row, query))
            all_rows = self.connection.execute("SELECT kind,tags,error FROM documents").fetchall()
            tags = sorted({label for row in all_rows for label in json.loads(row["tags"])})
            return {"items": items, "folders": self.directories(), "tags": tags, "stats": {"total": len(all_rows), "html": sum(row["kind"] == "html" for row in all_rows), "pdf": sum(row["kind"] == "pdf" for row in all_rows), "errors": sum(bool(row["error"]) for row in all_rows)}, "root": ".agents/artifacts"}

    def metadata(self, identity, title, summary, tags):
        if not isinstance(title, str) or not title.strip() or len(title) > 200 or not isinstance(summary, str) or len(summary) > 2000:
            raise ValueError("タイトルは1〜200文字、概要は2000文字以内で指定してください。")
        if not isinstance(tags, list) or len(tags) > 20 or any(not isinstance(tag, str) or not tag.strip() or len(tag) > 40 for tag in tags):
            raise ValueError("タグは各40文字以内、最大20個で指定してください。")
        with self.lock, self.connection:
            cursor = self.connection.execute("UPDATE documents SET title=?,summary=?,tags=?,custom_title=1 WHERE id=?", (title.strip(), summary, json.dumps(list(dict.fromkeys(tag.strip() for tag in tags)), ensure_ascii=False), identity))
            if not cursor.rowcount:
                raise ValueError("資料が見つかりません。索引を更新してください。")
            self.update_search(identity)

    def mkdir(self, parent, name):
        valid_component(name)
        with self.lock:
            directory = self.resolve(parent, allow_root=True)
            if not directory.is_dir():
                raise ValueError("親フォルダーが存在しません。")
            if any(child.name.casefold() == name.casefold() for child in directory.iterdir()):
                raise ValueError("同名の項目が既に存在します。")
            (directory / name).mkdir()

    def move(self, source, destination):
        with self.lock:
            original = self.resolve(source)
            target = self.resolve(destination)
            for part in PurePosixPath(destination).parts:
                valid_component(part)
            if not original.exists() or not target.parent.is_dir():
                raise ValueError("移動元または移動先フォルダーが見つかりません。")
            if source == destination:
                return
            if target.is_relative_to(original):
                raise ValueError("自分自身の配下には移動できません。")
            if any(child.name.casefold() == target.name.casefold() for child in target.parent.iterdir()):
                raise ValueError("移動先に同名の項目が存在します。")
            if original.is_file() and (original.suffix.lower() not in DOCUMENT_TYPES or original.suffix.lower() != target.suffix.lower()):
                raise ValueError("資料の拡張子は変更できません。")
            rows = self.connection.execute("SELECT id,path FROM documents").fetchall()
            updates = [(destination + row["path"][len(source):], row["id"]) for row in rows if row["path"] == source or row["path"].startswith(source + "/")]
            original.rename(target)
            try:
                with self.connection:
                    for new_path, identity in updates:
                        self.connection.execute("UPDATE documents SET path=? WHERE id=?", (new_path, identity))
                        self.update_search(identity)
            except Exception:
                target.rename(original)
                raise

    def trash_directory(self):
        directory = self.root / ".trash"
        if directory.is_symlink():
            raise ValueError("ごみ箱にシンボリックリンクは使用できません。")
        directory.mkdir(exist_ok=True)
        return directory

    def trash_entry(self, identity):
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9a-f]{32}", identity):
            raise ValueError("ごみ箱の指定が不正です。")
        entry = self.trash_directory() / identity
        if entry.is_symlink() or (entry / "manifest.json").is_symlink() or (entry / "payload").is_symlink():
            raise ValueError("ごみ箱にシンボリックリンクは使用できません。")
        return entry

    def trash_items(self):
        with self.lock:
            items = []
            for directory in self.trash_directory().iterdir():
                try:
                    entry = self.trash_entry(directory.name)
                    if not (entry / "payload").exists():
                        continue
                    manifest = json.loads((entry / "manifest.json").read_text(encoding="utf-8"))
                    items.append({"id": directory.name, "path": manifest["path"], "deleted": manifest["deleted"], "folder": manifest["folder"]})
                except (OSError, ValueError, KeyError, TypeError):
                    continue
            return sorted(items, key=lambda item: item["deleted"], reverse=True)

    def delete(self, source):
        with self.lock:
            original = self.resolve(source)
            source = original.relative_to(self.root).as_posix()
            if not original.exists() or not (original.is_dir() or original.suffix.lower() in DOCUMENT_TYPES):
                raise ValueError("削除対象の資料またはフォルダーが見つかりません。")
            records = [dict(row) for row in self.connection.execute("SELECT * FROM documents").fetchall() if row["path"] == source or row["path"].startswith(source + "/")]
            identity = uuid.uuid4().hex
            entry = self.trash_entry(identity)
            entry.mkdir()
            manifest = {"path": source, "deleted": int(time.time() * 1000), "folder": original.is_dir(), "records": records}
            try:
                with (entry / "manifest.json").open("x", encoding="utf-8") as output:
                    json.dump(manifest, output, ensure_ascii=False)
                original.rename(entry / "payload")
                try:
                    with self.connection:
                        for record in records:
                            self.connection.execute("DELETE FROM documents WHERE id=?", (record["id"],))
                            self.update_search(record["id"])
                except Exception:
                    (entry / "payload").rename(original)
                    raise
            except Exception:
                if not (entry / "payload").exists():
                    (entry / "manifest.json").unlink(missing_ok=True)
                    entry.rmdir()
                raise
            return identity

    def restore(self, identity):
        with self.lock:
            entry = self.trash_entry(identity)
            manifest = json.loads((entry / "manifest.json").read_text(encoding="utf-8"))
            target = self.resolve(manifest["path"])
            if not target.parent.is_dir():
                raise ValueError("元の親フォルダーを先に復元または作成してください。")
            if any(child.name.casefold() == target.name.casefold() for child in target.parent.iterdir()):
                raise ValueError("元の場所に同名の項目があります。上書きせず復元を中止しました。")
            source = target.relative_to(self.root).as_posix()
            columns = ("path", "kind", "title", "summary", "tags", "body", "size", "modified", "signature", "error", "custom_title")
            values = []
            for record in manifest["records"]:
                path = self.resolve(record["path"]).relative_to(self.root).as_posix()
                if path != source and not path.startswith(source + "/"):
                    raise ValueError("復元情報のパスが不正です。")
                values.append(tuple(record[column] for column in columns))
            (entry / "payload").rename(target)
            try:
                with self.connection:
                    for record in values:
                        cursor = self.connection.execute("INSERT INTO documents(path,kind,title,summary,tags,body,size,modified,signature,error,custom_title) VALUES(?,?,?,?,?,?,?,?,?,?,?)", record)
                        self.update_search(cursor.lastrowid)
            except Exception:
                target.rename(entry / "payload")
                raise
            try:
                (entry / "manifest.json").unlink()
                entry.rmdir()
            except OSError:
                pass

    def pdf_page(self, relative, page_number):
        path = self.resolve(relative)
        if path.suffix.lower() != ".pdf" or path.stat().st_size > MAX_BYTES:
            raise ValueError("このファイルはPDFプレビューの対象外です。")
        with pymupdf.open(path) as document:
            if document.needs_pass or not 0 <= page_number < len(document):
                raise ValueError("ページを表示できません。")
            page = document[page_number]
            scale = min(1.5, 1800 / max(page.rect.width, page.rect.height))
            return page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).tobytes("png"), len(document)