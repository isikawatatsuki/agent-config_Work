import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("render_pdf", Path(__file__).parents[1] / "render-pdf.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class RenderPdfTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "日本語 test #1.html"
        self.source.write_text("<!doctype html><title>Test</title><p>PDF test</p>", encoding="utf-8")

    def fake_browser(self, command, **options):
        self.assertIn("--headless=new", command)
        self.assertNotIn("--no-sandbox", command)
        self.assertEqual(command[-1], self.source.as_uri())
        self.assertNotIn("shell", options)
        self.assertEqual(options["timeout"], 60)
        generated = Path(next(argument.split("=", 1)[1] for argument in command if argument.startswith("--print-to-pdf=")))
        generated.write_bytes(b"%PDF-1.7\nTest fixture\n")

    def test_render_uses_uri_and_separate_profile(self):
        with patch.object(renderer, "find_browser", return_value="browser"), patch.object(renderer.subprocess, "run", side_effect=self.fake_browser):
            result = renderer.render_pdf(self.source)
        self.assertEqual(result.read_bytes(), b"%PDF-1.7\nTest fixture\n")

    def test_existing_output_is_never_overwritten(self):
        output = self.source.with_suffix(".pdf")
        output.write_bytes(b"existing")
        with patch.object(renderer.subprocess, "run") as process:
            with self.assertRaises(FileExistsError):
                renderer.render_pdf(self.source)
            process.assert_not_called()
        self.assertEqual(output.read_bytes(), b"existing")

    def test_concurrent_output_creation_is_preserved(self):
        output = self.source.with_suffix(".pdf")
        def competing_browser(command, **options):
            self.fake_browser(command, **options)
            output.write_bytes(b"other writer")
        with patch.object(renderer, "find_browser", return_value="browser"), patch.object(renderer.subprocess, "run", side_effect=competing_browser):
            with self.assertRaises(FileExistsError):
                renderer.render_pdf(self.source)
        self.assertEqual(output.read_bytes(), b"other writer")

    def test_failure_timeout_and_invalid_pdf_leave_no_output(self):
        for failure in (subprocess.TimeoutExpired("browser", 60), subprocess.CalledProcessError(1, "browser")):
            with self.subTest(failure=failure), patch.object(renderer, "find_browser", return_value="browser"), patch.object(renderer.subprocess, "run", side_effect=failure):
                with self.assertRaises(type(failure)):
                    renderer.render_pdf(self.source)
                self.assertFalse(self.source.with_suffix(".pdf").exists())
        def invalid_browser(command, **options):
            self.fake_browser(command, **options)
            Path(next(argument.split("=", 1)[1] for argument in command if argument.startswith("--print-to-pdf="))).write_bytes(b"invalid")
        with patch.object(renderer, "find_browser", return_value="browser"), patch.object(renderer.subprocess, "run", side_effect=invalid_browser):
            with self.assertRaises(ValueError):
                renderer.render_pdf(self.source)
        self.assertFalse(self.source.with_suffix(".pdf").exists())

    def test_linux_path_discovery(self):
        with patch.object(renderer.shutil, "which", side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None):
            self.assertEqual(renderer.find_browser(), "/usr/bin/chromium")

    def test_windows_edge_discovery(self):
        edge = self.root / "Microsoft/Edge/Application/msedge.exe"
        edge.parent.mkdir(parents=True)
        edge.touch()
        with patch.object(renderer.sys, "platform", "win32"), patch.dict(renderer.os.environ, {"PROGRAMFILES": str(self.root)}, clear=True), patch.object(renderer.shutil, "which", return_value=None), patch.object(renderer.os, "access", return_value=True):
            self.assertEqual(renderer.find_browser(), str(edge))

    def test_macos_candidates_retained(self):
        candidates = list(renderer.browser_candidates("darwin", {}))
        self.assertIn(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"), candidates)

    def test_explicit_browser_and_missing_browser(self):
        with patch.object(renderer.shutil, "which", return_value=None):
            with self.assertRaises(ValueError):
                renderer.find_browser(str(self.root / "missing"))
        with patch.object(renderer.shutil, "which", return_value=None), patch.object(renderer, "browser_candidates", return_value=[]):
            with self.assertRaises(ValueError):
                renderer.find_browser()

    def test_invalid_inputs(self):
        for output, timeout in ((self.root / "bad.html", 60), (self.root / "out.pdf", 0)):
            with self.subTest(output=output, timeout=timeout), self.assertRaises(ValueError):
                renderer.render_pdf(self.source, output, timeout=timeout)

    @unittest.skipUnless(os.environ.get("SKILL_TEST_BROWSER") and importlib.util.find_spec("pymupdf"), "実ブラウザーとPyMuPDFが必要です")
    def test_real_browser_pdf_content(self):
        import pymupdf
        output = self.root / "日本語 出力.pdf"
        result = subprocess.run(
            [renderer.sys.executable, str(Path(renderer.__file__)), str(self.source), "--output", str(output), "--browser", os.environ["SKILL_TEST_BROWSER"]],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with pymupdf.open(output) as document:
            self.assertEqual(len(document), 1)
            self.assertIn("PDF test", document[0].get_text())
            self.assertGreater(len(set(document[0].get_pixmap().samples)), 1)


if __name__ == "__main__":
    unittest.main()