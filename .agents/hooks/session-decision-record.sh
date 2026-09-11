#!/usr/bin/env bash
set -u

EVENT="${1:-}"
INPUT="$(cat)"
DATE="$(date -u +%Y-%m-%d)"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

json_value() {
  local expression="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r "$expression // empty" 2>/dev/null
  fi
}

find_workspace_root() {
  local candidate="$1"
  candidate="$(cd "$candidate" 2>/dev/null && pwd -P)" || return 1

  while [[ "$candidate" != "/" ]]; do
    if [[ -f "$candidate/REPOSITORIES.md" && -f "$candidate/AGENTS.md" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
    candidate="$(dirname "$candidate")"
  done

  return 1
}

SESSION_ID="$(json_value '.session_id // .conversation_id')"
CWD="$(json_value '.cwd')"
CWD="${CWD:-$PWD}"

if [[ -z "$SESSION_ID" ]]; then
  SESSION_ID="$(printf '%s' "$(json_value '.transcript_path'):$CWD" | sha256sum | cut -c1-16)"
fi

SAFE_SESSION_ID="$(printf '%s' "$SESSION_ID" | tr -cd '[:alnum:]_.-')"
WORKSPACE_ROOT="$(find_workspace_root "$CWD" || true)"

if [[ -n "${SESSION_RECORD_ROOT:-}" ]]; then
  RECORD_ROOT="$SESSION_RECORD_ROOT"
elif [[ -n "$WORKSPACE_ROOT" ]]; then
  RECORD_ROOT="$WORKSPACE_ROOT/docs/adr/sessions"
else
  RECORD_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/agent-session-records"
fi

if [[ -n "$WORKSPACE_ROOT" ]]; then
  umask 022
else
  umask 077
fi

RECORD_DIR="$RECORD_ROOT/$DATE"
RECORD_PATH="$RECORD_DIR/$SAFE_SESSION_ID.md"

case "$EVENT" in
  session-start)
    mkdir -p "$RECORD_DIR"
    if [[ ! -f "$RECORD_PATH" ]]; then
      cat >"$RECORD_PATH" <<EOF
# Session Decision Record

- Session: $SESSION_ID
- Started: $TIMESTAMP
- Workspace: ${WORKSPACE_ROOT:-$CWD}
- Status: in-progress

## Request

<!-- Summarize the user's request without secrets or personal data. -->

## Context and constraints

<!-- Record relevant evidence, assumptions, scope, and constraints. -->

## Decisions

<!-- For each decision: choice, rationale, alternatives, and consequences. -->

## Actions

<!-- Record investigation, implementation, review, and commands by work section. -->

## Validation

<!-- Record checks performed and their results. -->

## Outcome and follow-up

<!-- Record completion status, residual risks, and ADR promotion decision. -->
EOF
    fi
    jq -n --arg path "$RECORD_PATH" '{systemMessage: ("セッション記録: " + $path + "。作業中に全セクションを更新し、永続的な判断はADRへ昇格してください。")}'
    ;;
  stop)
    if [[ ! -f "$RECORD_PATH" ]]; then
      jq -n --arg path "$RECORD_PATH" '{systemMessage: ("セッション記録がありません: " + $path + "。最終応答前に作成してください。")}'
      exit 0
    fi

    if grep -q '<!--' "$RECORD_PATH" || grep -q -- '- Status: in-progress' "$RECORD_PATH"; then
      jq -n --arg path "$RECORD_PATH" '{systemMessage: ("セッション記録が未完了です: " + $path + "。全セクション、完了状態、ADR昇格判断を記録してください。")}'
    fi
    ;;
  *)
    printf '%s\n' "不明なイベントです: $EVENT" >&2
    exit 1
    ;;
esac