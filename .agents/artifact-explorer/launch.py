import argparse
import os
from pathlib import Path
import subprocess
import sys


APP_DIRECTORY = Path(__file__).resolve().parent


def environment_python(directory=APP_DIRECTORY, platform=os.name):
    return directory / ".venv" / ("Scripts/python.exe" if platform == "nt" else "bin/python")


def main():
    parser = argparse.ArgumentParser(description="Artifact Libraryの専用環境で起動します")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("ポートは1〜65535で指定してください。")
    executable = environment_python()
    if not executable.is_file():
        print("Artifact Library: 専用Python環境がありません。.agents/artifact-explorer/README.md の初回準備を実行してください。", flush=True)
        return 1
    check = "import sys, sqlite3; assert sys.version_info >= (3, 10); import pymupdf; sqlite3.connect(':memory:').execute(\"CREATE VIRTUAL TABLE probe USING fts5(text, tokenize='trigram')\")"
    try:
        result = subprocess.run([str(executable), "-c", check], capture_output=True, timeout=15, check=False)
        if result.returncode:
            print("Artifact Library: Python 3.10以上、PyMuPDF、SQLite FTS5 trigramが必要です。READMEの依存準備を確認してください。自動インストールは行いません。", flush=True)
            return 1
        print("Artifact Library: 起動開始", flush=True)
        os.execv(str(executable), [str(executable), "-u", str(APP_DIRECTORY / "server.py"), "--reuse-existing", "--port", str(args.port)])
    except (OSError, subprocess.TimeoutExpired):
        print("Artifact Library: 専用Python環境を実行できません。権限・環境・READMEを確認してください。", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())