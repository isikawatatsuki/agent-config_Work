import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import extract_images


class DependencyTests(unittest.TestCase):
    def test_missing_dependency_has_actionable_error(self):
        with patch.object(extract_images, "fitz", None):
            with self.assertRaisesRegex(RuntimeError, "PyMuPDF"):
                extract_images.extract("unused.pdf", "unused-output", 300)


@unittest.skipUnless(importlib.util.find_spec("pymupdf"), "PyMuPDFが必要です")
class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.pdf = self.root / "日本語 論文.pdf"
        self.output = self.root / "抽出 画像"
        with extract_images.fitz.open() as document:
            page = document.new_page()
            page.draw_rect(extract_images.fitz.Rect(80, 80, 240, 160), color=(0, 0, 0), fill=(0.2, 0.5, 0.8))
            page.insert_text((80, 190), "Figure 1 Example")
            page = document.new_page()
            for height in (80, 110, 140):
                page.draw_line((80, height), (240, height))
            page.insert_text((90, 100), "Name   Value")
            page.insert_text((90, 130), "Test   42")
            page.insert_text((80, 170), "Table 1 Results")
            document.save(self.pdf)

    def test_real_extraction_and_utf8_manifest(self):
        result = extract_images.extract(self.pdf, self.output, 144)
        self.assertEqual([(entry["label"], entry["num"]) for entry in result], [("Figure", 1), ("Table", 1)])
        manifest = self.output / "日本語 論文-manifest.json"
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8")), result)
        for entry in result:
            image = extract_images.fitz.Pixmap(str(self.output / entry["file"]))
            self.assertEqual([image.width, image.height], entry["px"])
            self.assertGreater(image.width, 30)
            self.assertGreater(image.height, 10)
            self.assertGreater(len(set(image.samples)), 1)
        self.pdf.unlink()

    def test_invalid_dpi_creates_no_output(self):
        with self.assertRaises(ValueError):
            extract_images.extract(self.pdf, self.output, 0)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()