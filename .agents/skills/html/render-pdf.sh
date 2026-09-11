#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python 3.9以上が必要です。Windowsでは py -3 render-pdf.py を使用してください。' >&2
  exit 69
fi

exec python3 "$SCRIPT_DIR/render-pdf.py" "$@"
