"""Chrome / Chromium / Edge を使い、HTML を PDF へ変換する。"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def browser_candidates(platform, environment):
    if platform == "win32":
        for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            if environment.get(variable):
                for relative in (
                    "Google/Chrome/Application/chrome.exe",
                    "Microsoft/Edge/Application/msedge.exe",
                    "Chromium/Application/chrome.exe",
                ):
                    yield Path(environment[variable]) / relative
    elif platform == "darwin":
        for app, executable in (
            ("Google Chrome", "Google Chrome"),
            ("Google Chrome Canary", "Google Chrome Canary"),
            ("Chromium", "Chromium"),
            ("Microsoft Edge", "Microsoft Edge"),
        ):
            yield Path("/Applications") / f"{app}.app/Contents/MacOS/{executable}"


def find_browser(explicit=None):
    if explicit:
        resolved = shutil.which(explicit)
        candidate = Path(resolved or explicit).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        raise ValueError("指定されたブラウザー実行ファイルが見つかりません。")
    for name in (
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
        "microsoft-edge", "microsoft-edge-stable", "chrome", "msedge",
    ):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    for candidate in browser_candidates(sys.platform, os.environ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise ValueError("Chrome / Chromium / Edge が見つかりません。--browser で実行ファイルを指定してください。")


def render_pdf(source, output=None, browser=None, timeout=60):
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_file() or source.suffix.lower() not in (".html", ".htm"):
        raise ValueError("入力には .html または .htm の通常ファイルを指定してください。")
    destination = Path(output).expanduser().absolute() if output else source.with_suffix(".pdf")
    if destination.suffix.lower() != ".pdf":
        raise ValueError("出力先の拡張子は .pdf にしてください。")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("出力先が既に存在します。別の名前を指定してください。")
    if not destination.parent.is_dir():
        raise ValueError("出力先のディレクトリが存在しません。")
    if timeout <= 0:
        raise ValueError("タイムアウトは正の秒数で指定してください。")
    executable = find_browser(browser)
    with tempfile.TemporaryDirectory(prefix="skill-render-pdf-") as temporary:
        temporary = Path(temporary)
        generated = temporary / "rendered.pdf"
        command = [
            executable,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            "--no-pdf-header-footer",
            f"--user-data-dir={temporary / 'profile'}",
            f"--print-to-pdf={generated}",
            source.as_uri(),
        ]
        subprocess.run(command, check=True, timeout=timeout, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        with generated.open("rb") as rendered:
            if rendered.read(5) != b"%PDF-":
                raise ValueError("ブラウザーの出力がPDF形式ではありません。")
            rendered.seek(0)
            with destination.open("xb") as target:
                try:
                    shutil.copyfileobj(rendered, target)
                except BaseException:
                    target.close()
                    destination.unlink()
                    raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", help="入力HTMLのパス")
    parser.add_argument("--output", help="新規PDFの保存先（既定: 入力HTMLと同じ場所）")
    parser.add_argument("--browser", help="Chrome / Chromium / Edge の実行ファイル")
    parser.add_argument("--timeout", type=int, default=60, help="処理の制限時間（秒、既定: 60）")
    args = parser.parse_args()
    try:
        output = render_pdf(args.html, args.output, args.browser, args.timeout)
    except subprocess.TimeoutExpired:
        print("エラー: PDF生成が制限時間を超えました。", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"エラー: ブラウザーが終了コード {error.returncode} で失敗しました。サンドボックス等の実行条件を確認してください。", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 1
    print(f"PDFを保存しました: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())