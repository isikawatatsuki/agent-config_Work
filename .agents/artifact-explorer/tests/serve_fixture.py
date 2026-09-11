from pathlib import Path
import sys
import tempfile

import pymupdf

sys.path.insert(0, str(Path(__file__).parents[1]))
from library import Library
from server import ExplorerServer


def main():
    with tempfile.TemporaryDirectory(prefix="artifact-explorer-preview-") as temporary:
        root = Path(temporary)
        library = Library(root / "artifacts", root / "state/index.sqlite")
        bundle = library.root / "sample"
        bundle.mkdir()
        (bundle / "index.html").write_text(
            '<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<title>検索検証資料</title><style>body{font:20px sans-serif;padding:24px;'
            'color:#176b55;background:#f5f7f6}img{width:80px}</style>'
            '<h1>検索検証資料</h1><p>自治体連携の索引テスト</p>'
            '<img src="sample.png" alt="検証用画像"></html>', encoding="utf-8"
        )
        with pymupdf.open() as document:
            first = document.new_page(width=400, height=500)
            first.insert_text((30, 60), "Artifact Explorer PDF - Page 1", fontsize=16)
            first.draw_rect(pymupdf.Rect(30, 100, 350, 250), color=(0.1, 0.5, 0.35), fill=(0.85, 0.95, 0.9))
            first.get_pixmap().save(bundle / "sample.png")
            second = document.new_page(width=400, height=500)
            second.insert_text((30, 60), "Searchable second page", fontsize=16)
            document.save(library.root / "sample.pdf")
        library.scan()
        with ExplorerServer(("127.0.0.1", 8766), library) as server:
            print("検証用ライブラリ: http://127.0.0.1:8766", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
        library.close()


if __name__ == "__main__":
    main()