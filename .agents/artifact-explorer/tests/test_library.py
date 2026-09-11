import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import pymupdf
from library import Library, valid_component


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "成果物"
        self.library = Library(self.root, Path(self.temporary.name) / "state/index.sqlite")
        self.addCleanup(self.library.close)
        (self.root / "資料.html").write_text("<title>設計資料</title><p>寄附連携APIの構成と検索対象です。</p><script>hiddenword</script>", encoding="utf-8")

    def test_japanese_full_text_and_short_search(self):
        self.library.scan()
        self.assertEqual(len(self.library.browse(query="寄附連携")['items']), 1)
        self.assertEqual(len(self.library.browse(query="寄附")['items']), 1)
        self.assertEqual(len(self.library.browse(query="hiddenword")['items']), 0)
        self.assertEqual(len(self.library.browse(query='" OR 1=1 --')['items']), 0)

    def test_metadata_survives_scan_and_move(self):
        self.library.scan()
        item = self.library.browse()['items'][0]
        self.library.metadata(item['id'], "個人用タイトル", "概要の検証", ["ふるまど"])
        self.library.mkdir("", "整理先")
        self.library.move("資料.html", "整理先/更新.html")
        self.library.scan()
        moved = self.library.browse(query="ふるまど")['items'][0]
        self.assertEqual(moved['id'], item['id'])
        self.assertEqual(moved['path'], "整理先/更新.html")
        self.assertEqual(moved['title'], "個人用タイトル")
        self.assertEqual(len(self.library.browse(folder="整理先", scope="folder")['items']), 1)

    def test_folder_move_preserves_assets(self):
        self.library.mkdir("", "bundle")
        (self.root / "bundle/asset.css").write_text("body{}")
        (self.root / "bundle/index.html").write_text('<link href="asset.css">')
        self.library.scan()
        self.library.move("bundle", "renamed")
        self.assertTrue((self.root / "renamed/asset.css").exists())
        self.assertEqual(len(self.library.browse(folder="renamed", scope="folder")['items']), 1)

    def test_paths_and_overwrite_rejected(self):
        for path in ("../outside", "/etc/passwd", "C:/Windows", "folder/../../outside", ".hidden", "folder\\file"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.library.resolve(path)
        for name in ("CON", "a:", "x/../y", "NUL.pdf", "bad."):
            with self.subTest(name=name), self.assertRaises(ValueError):
                valid_component(name)
        (self.root / "already.html").write_text("keep")
        with self.assertRaises(ValueError):
            self.library.move("資料.html", "already.html")
        self.assertEqual((self.root / "already.html").read_text(), "keep")

    def test_symlink_outside_is_not_indexed(self):
        outside = self.root.parent / "secret.html"
        outside.write_text("secret")
        try:
            (self.root / "link.html").symlink_to(outside)
        except OSError:
            self.skipTest("シンボリックリンクの作成権限なし")
        self.library.scan()
        self.assertEqual(self.library.last_scan['indexed'], 1)
        with self.assertRaises(ValueError):
            self.library.resolve("link.html")

    def test_pdf_text_and_preview(self):
        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text((50, 50), "Searchable PDF document")
            document.save(self.root / "sample.pdf")
        self.library.scan()
        self.assertEqual(len(self.library.browse(query="Searchable", kind="pdf")['items']), 1)
        image, pages = self.library.pdf_page("sample.pdf", 0)
        self.assertTrue(image.startswith(b"\x89PNG"))
        self.assertEqual(pages, 1)

    def test_deleted_file_removed_from_index(self):
        self.library.scan()
        (self.root / "資料.html").unlink()
        self.library.scan()
        self.assertEqual(self.library.browse()['stats']['total'], 0)

    def test_delete_and_restore_preserve_metadata_and_search(self):
        self.library.scan()
        item = self.library.browse()['items'][0]
        self.library.metadata(item['id'], "保存タイトル", "保存概要", ["重要"])
        identity = self.library.delete("資料.html")
        self.assertFalse((self.root / "資料.html").exists())
        self.assertEqual(self.library.browse(query="寄附")['items'], [])
        self.library.scan()
        self.assertEqual(self.library.browse()['stats']['total'], 0)
        self.assertEqual(self.library.trash_items()[0]['id'], identity)
        self.library.restore(identity)
        restored = self.library.browse(query="重要")['items'][0]
        self.assertEqual(restored['title'], "保存タイトル")
        self.assertEqual(restored['summary'], "保存概要")
        self.assertTrue((self.root / "資料.html").exists())
        self.assertEqual(self.library.trash_items(), [])

    def test_delete_folder_and_restore_assets(self):
        self.library.mkdir("", "bundle")
        (self.root / "bundle/asset.css").write_text("body{}")
        (self.root / "bundle/index.html").write_text("<title>Bundle</title>")
        self.library.scan()
        identity = self.library.delete("bundle")
        self.assertNotIn("bundle", self.library.directories())
        self.assertEqual(len(self.library.browse()['items']), 1)
        self.library.restore(identity)
        self.assertEqual((self.root / "bundle/asset.css").read_text(), "body{}")
        self.assertEqual(len(self.library.browse()['items']), 2)

    def test_trash_rejects_root_traversal_and_restore_collision(self):
        for source in ("", ".", "../", ".trash"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.library.delete(source)
        with self.assertRaises(ValueError):
            self.library.restore("../outside")
        self.library.scan()
        identity = self.library.delete("資料.html")
        (self.root / "資料.html").write_text("new file")
        with self.assertRaises(ValueError):
            self.library.restore(identity)
        self.assertEqual((self.root / "資料.html").read_text(), "new file")
        self.assertEqual(len(self.library.trash_items()), 1)

    def test_delete_and_restore_roll_back_on_index_failure(self):
        self.library.scan()
        with patch.object(self.library, "update_search", side_effect=RuntimeError("test failure")):
            with self.assertRaises(RuntimeError):
                self.library.delete("資料.html")
        self.assertTrue((self.root / "資料.html").exists())
        self.assertEqual(len(self.library.browse()['items']), 1)
        identity = self.library.delete("資料.html")
        with patch.object(self.library, "update_search", side_effect=RuntimeError("test failure")):
            with self.assertRaises(RuntimeError):
                self.library.restore(identity)
        self.assertFalse((self.root / "資料.html").exists())
        self.assertEqual(self.library.browse()['items'], [])
        self.assertEqual(len(self.library.trash_items()), 1)

    def test_trash_survives_new_library_instance(self):
        self.library.scan()
        identity = self.library.delete("資料.html")
        reopened = Library(self.root, self.root.parent / "state/index.sqlite")
        try:
            reopened.scan()
            self.assertEqual(reopened.trash_items()[0]['id'], identity)
            reopened.restore(identity)
            self.assertEqual(len(reopened.browse(query="寄附")['items']), 1)
        finally:
            reopened.close()

    def test_restore_requires_original_parent(self):
        self.library.mkdir("", "bundle")
        self.library.move("資料.html", "bundle/資料.html")
        self.library.scan()
        identity = self.library.delete("bundle/資料.html")
        folder_identity = self.library.delete("bundle")
        with self.assertRaises(ValueError):
            self.library.restore(identity)
        self.library.restore(folder_identity)
        self.library.restore(identity)
        self.assertTrue((self.root / "bundle/資料.html").exists())

    def test_trash_rejects_symlink_directory(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        try:
            (self.root / ".trash").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("シンボリックリンクの作成権限なし")
        with self.assertRaises(ValueError):
            self.library.delete("資料.html")
        self.assertTrue((self.root / "資料.html").exists())
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()