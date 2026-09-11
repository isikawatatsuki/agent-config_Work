import argparse
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import socket
import threading
from urllib.parse import parse_qs, unquote, urlsplit

from library import Library, MAX_BYTES


APP_DIRECTORY = Path(__file__).resolve().parent
APP_CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
PREVIEW_CSP = "sandbox allow-scripts; default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'"
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".woff": "font/woff", ".woff2": "font/woff2"}


def instance_identity(root, state):
    paths = json.dumps([str(APP_DIRECTORY), str(root.resolve()), str(state.resolve())])
    return hashlib.sha256(paths.encode("utf-8")).hexdigest()


def matching_server(port, identity):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", "/api/health")
        response = connection.getresponse()
        body = response.read(4097)
        if response.status != 200 or len(body) > 4096:
            return False
        data = json.loads(body)
        return isinstance(data, dict) and data.get("app") == "artifact-library" and data.get("instance") == identity and data.get("ready") is True
    except (OSError, http.client.HTTPException, ValueError):
        return False
    finally:
        connection.close()


def serve(root, state, port, reuse_existing=False):
    identity = instance_identity(root, state)
    try:
        server = ExplorerServer(("127.0.0.1", port), None)
    except OSError:
        if reuse_existing and matching_server(port, identity):
            print(f"Artifact Library: 起動済み http://127.0.0.1:{port}", flush=True)
            return 0
        print(f"Artifact Library: ポート{port}を使用できません。別アプリ、別保存先、または起動途中の可能性があります。既存プロセスは停止しません。", flush=True)
        return 1
    library = None
    try:
        library = Library(root, state / "index.sqlite")
        library.scan()
        server.library = library
        server.identity = identity
        print(f"Artifact Library: http://127.0.0.1:{port}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if library is not None:
            library.close()
    return 0


class ExplorerServer(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        if os.name == "nt":
            self.allow_reuse_address = False
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def __init__(self, address, library):
        super().__init__(address, Handler)
        self.library = library
        self.identity = ""
        self.token = secrets.token_urlsafe(32)
        self.scan_lock = threading.Lock()
        self.scan_error = ""
        self.scan_running = False

    def start_scan(self):
        if not self.scan_lock.acquire(blocking=False):
            return
        self.scan_error = ""
        self.scan_running = True
        def run():
            try:
                self.library.scan()
            except Exception:
                self.scan_error = "索引更新に失敗しました。ファイルの状態と権限を確認してください。"
            finally:
                self.scan_running = False
                self.scan_lock.release()
        threading.Thread(target=run, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server_version = "ArtifactExplorer"

    def log_message(self, format, *args):
        pass

    def trusted_host(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

    def reply(self, status, data, content_type="application/json; charset=utf-8", preview=False, extra=None):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if isinstance(data, (dict, list)) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", PREVIEW_CSP if preview else APP_CSP)
        if extra:
            for name, value in extra.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.trusted_host():
            return self.reply(403, {"error": "localhostからアクセスしてください。"})
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        value = lambda key, fallback="": query.get(key, [fallback])[0]
        try:
            if parsed.path == "/api/health":
                return self.reply(200, {"app": "artifact-library", "instance": self.server.identity, "ready": self.server.library is not None})
            if parsed.path == "/api/bootstrap":
                return self.reply(200, {"token": self.server.token})
            if parsed.path == "/api/library":
                return self.reply(200, self.server.library.browse(value("q"), value("folder"), value("kind"), value("tag"), value("sort", "modified"), value("scope", "all")))
            if parsed.path == "/api/trash":
                return self.reply(200, {"items": self.server.library.trash_items()})
            if parsed.path == "/api/status":
                return self.reply(200, {"running": self.server.scan_running, "error": self.server.scan_error, **self.server.library.last_scan})
            if parsed.path == "/api/pdf-page":
                image, pages = self.server.library.pdf_page(value("path"), int(value("page", "0")))
                return self.reply(200, image, "image/png", extra={"X-Page-Count": str(pages)})
            if parsed.path == "/api/download":
                path = self.server.library.resolve(value("path"))
                if path.suffix.lower() not in (".html", ".htm", ".pdf") or path.stat().st_size > MAX_BYTES:
                    raise ValueError("このファイルはダウンロード対象外です。")
                from urllib.parse import quote
                return self.reply(200, path.read_bytes(), "application/octet-stream", extra={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(path.name)})
            if parsed.path.startswith("/content/"):
                path = self.server.library.resolve(unquote(parsed.path[len("/content/"):]))
                if path.suffix.lower() not in CONTENT_TYPES or not path.is_file() or path.stat().st_size > MAX_BYTES:
                    return self.reply(404, {"error": "プレビュー対象のファイルがありません。"})
                return self.reply(200, path.read_bytes(), CONTENT_TYPES[path.suffix.lower()], preview=True)
            allowed = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/vendor/lucide.js": "vendor/lucide.js", "/viewer.html": "viewer.html", "/viewer.js": "viewer.js", "/viewer.css": "viewer.css"}
            if parsed.path not in allowed:
                return self.reply(404, {"error": "ページが見つかりません。"})
            path = APP_DIRECTORY / "web" / allowed[parsed.path]
            return self.reply(200, path.read_bytes(), mimetypes.guess_type(str(path))[0] or "application/octet-stream")
        except (ValueError, OSError, RuntimeError):
            self.reply(400, {"error": "読み込めません。パス・形式・権限を確認してください。"})

    def do_POST(self):
        if not self.trusted_host() or not secrets.compare_digest(self.headers.get("X-Artifact-Token", ""), self.server.token):
            return self.reply(403, {"error": "操作を許可できません。画面を再読み込みしてください。"})
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
            return self.reply(403, {"error": "外部ページからの操作を拒否しました。"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16_384 or self.headers.get_content_type() != "application/json":
                raise ValueError("JSON形式の操作のみ受け付けます。")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("操作内容が不正です。")
            if self.path == "/api/scan":
                self.server.start_scan()
            elif self.path == "/api/metadata":
                self.server.library.metadata(int(data["id"]), data["title"], data["summary"], data["tags"])
            elif self.path == "/api/folder":
                self.server.library.mkdir(data["parent"], data["name"])
            elif self.path == "/api/move":
                self.server.library.move(data["source"], data["destination"])
            elif self.path == "/api/delete":
                self.server.library.delete(data["source"])
            elif self.path == "/api/restore":
                self.server.library.restore(data["id"])
            else:
                return self.reply(404, {"error": "操作が見つかりません。"})
            self.reply(200, {"ok": True})
        except (ValueError, KeyError, TypeError, OSError) as error:
            self.reply(400, {"error": str(error) if isinstance(error, ValueError) else "操作できません。入力内容とファイルの状態を確認してください。"})


def main():
    parser = argparse.ArgumentParser(description="HTML・PDFのローカル成果物エクスプローラー")
    parser.add_argument("--root", type=Path, default=APP_DIRECTORY.parent / "artifacts")
    parser.add_argument("--state", type=Path, default=APP_DIRECTORY / ".state")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--reuse-existing", action="store_true", help="同じ保存先で起動済みの場合はそのまま利用する")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("ポートは1〜65535で指定してください。")
    return serve(args.root, args.state, args.port, args.reuse_existing)


if __name__ == "__main__":
    raise SystemExit(main())