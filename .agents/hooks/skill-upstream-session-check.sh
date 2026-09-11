#!/usr/bin/env bash
# SessionStart Hook: 外部由来Skillの上流照合を1日1回だけ実行する。
#
# セッション起動を待たせないため、照合本体はバックグラウンドで走らせ、
# このHookは直前の照合結果（キャッシュ）だけを即座に返す。
# 更新が無い場合は何も出力しない。
set -uo pipefail

WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHECKER="$WORKSPACE/.agents/scripts/skill-upstream-check.sh"
CACHE_DIR="${HOME}/.claude/cache/skill-upstream-check"
RESULT="$CACHE_DIR/last-result.json"
STAMP="$CACHE_DIR/last-run"
MIN_INTERVAL=72000 # 20時間。日付境界のずれで走らない日が出ないよう24時間より短くする。

# Hookは失敗してもセッションを妨げない。
trap 'exit 0' ERR
mkdir -p "$CACHE_DIR" 2>/dev/null || exit 0
[[ -x "$CHECKER" ]] || exit 0

# 前回実行から MIN_INTERVAL 以上経っていればバックグラウンドで照合する。
now="$(date +%s)"
last="$(cat "$STAMP" 2>/dev/null || echo 0)"
if [[ "$((now - last))" -ge "$MIN_INTERVAL" ]]; then
  printf '%s' "$now" > "$STAMP"
  nohup bash -c '"$1" --json > "$2.tmp" 2>/dev/null && mv "$2.tmp" "$2"' _ \
    "$CHECKER" "$RESULT" >/dev/null 2>&1 &
  disown 2>/dev/null || true
fi

# 直前の結果に更新があれば、その要約だけをセッションへ渡す。
[[ -s "$RESULT" ]] || exit 0
command -v jq >/dev/null 2>&1 || exit 0

summary="$(jq -r '
  [.[] | select(.status=="outdated")] as $o
  | if ($o | length) == 0 then ""
    else
      "外部由来Skillの上流更新: " + (($o | length) | tostring) + "件\n"
      + ($o | map("- " + .name + " (" + .repo + "): " + .pinned[0:9] + " -> " + .head[0:9]) | join("\n"))
      + "\n確認は /skill-upstream-check。反映は明示依頼があるまで行わない。"
    end' "$RESULT" 2>/dev/null)"

[[ -n "$summary" ]] || exit 0

jq -n --arg ctx "$summary" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
