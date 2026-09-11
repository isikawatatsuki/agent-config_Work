#!/usr/bin/env bash
# .agents/skills/ の外部由来Skillについて、固定コミットと上流の最新を照合する。
# 検出と差分表示のみを行い、ローカルのSkillファイルは一切変更しない。
#
# Usage:
#   skill-upstream-check.sh                 # 全Skillを照合してレポート
#   skill-upstream-check.sh --json          # 機械可読な照合結果
#   skill-upstream-check.sh --diff <skill>  # 該当Skillの上流差分を表示
set -uo pipefail

WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MANIFEST="$WORKSPACE/.agents/skills/upstream.json"

for cmd in gh jq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "エラー: $cmd が必要です。" >&2; exit 2; }
done
[[ -f "$MANIFEST" ]] || { echo "エラー: $MANIFEST が見つかりません。" >&2; exit 2; }
gh auth status >/dev/null 2>&1 || { echo "エラー: gh が未認証です。'gh auth login' を実行してください。" >&2; exit 2; }

# パス（ディレクトリまたはファイル）の内容ハッシュを解決する。
tree_sha() {
  local repo="$1" rev="$2" path="$3" sha
  sha="$(gh api "repos/$repo/git/trees/$rev:$path" --jq '.sha' 2>/dev/null)"
  if [[ -z "$sha" ]]; then
    # ファイルパスの場合は blob の sha を使う
    sha="$(gh api "repos/$repo/contents/$path?ref=$rev" --jq 'if type=="object" then .sha else "" end' 2>/dev/null)"
  fi
  printf '%s' "${sha:-MISSING}"
}

# 照合結果をJSON行として標準出力へ流す。
collect() {
  local count idx
  count="$(jq '.skills | length' "$MANIFEST")"
  for ((idx = 0; idx < count; idx++)); do
    local name repo ref pinned notes head paths changed pcount pidx
    name="$(jq -r ".skills[$idx].name" "$MANIFEST")"
    repo="$(jq -r ".skills[$idx].repo" "$MANIFEST")"
    ref="$(jq -r ".skills[$idx].ref" "$MANIFEST")"
    pinned="$(jq -r ".skills[$idx].pinned" "$MANIFEST")"
    notes="$(jq -r ".skills[$idx].notes // \"\"" "$MANIFEST")"
    head="$(gh api "repos/$repo/commits/$ref" --jq '.sha' 2>/dev/null)"
    if [[ -z "$head" ]]; then
      jq -cn --arg name "$name" --arg repo "$repo" --arg ref "$ref" --arg pinned "$pinned" \
        '{name:$name, repo:$repo, ref:$ref, pinned:$pinned, status:"error", detail:"上流の取得に失敗"}'
      continue
    fi

    changed=()
    pcount="$(jq ".skills[$idx].paths | length" "$MANIFEST")"
    for ((pidx = 0; pidx < pcount; pidx++)); do
      local p old new
      p="$(jq -r ".skills[$idx].paths[$pidx]" "$MANIFEST")"
      old="$(tree_sha "$repo" "$pinned" "$p")"
      new="$(tree_sha "$repo" "$head" "$p")"
      [[ "$old" != "$new" ]] && changed+=("$p")
    done

    local status="current"
    [[ ${#changed[@]} -gt 0 ]] && status="outdated"
    jq -cn --arg name "$name" --arg repo "$repo" --arg ref "$ref" \
      --arg pinned "$pinned" --arg head "$head" --arg status "$status" --arg notes "$notes" \
      --argjson changed "$(printf '%s\n' "${changed[@]:-}" | jq -Rsc 'split("\n") | map(select(length>0))')" \
      '{name:$name, repo:$repo, ref:$ref, pinned:$pinned, head:$head, status:$status,
        changed_paths:$changed, notes:$notes,
        compare:("https://github.com/" + $repo + "/compare/" + $pinned + "..." + $head)}'
  done
}

# 上流差分を表示する。マニフェストのパス配下のみへ絞り込む。
show_diff() {
  local target="$1" entry repo pinned head
  entry="$(jq -c --arg n "$target" '.skills[] | select(.name==$n)' "$MANIFEST")"
  [[ -n "$entry" ]] || { echo "エラー: '$target' はマニフェストに存在しません。" >&2; exit 1; }
  repo="$(jq -r '.repo' <<<"$entry")"
  pinned="$(jq -r '.pinned' <<<"$entry")"
  head="$(gh api "repos/$repo/commits/$(jq -r '.ref' <<<"$entry")" --jq '.sha')"

  echo "# $target : $repo  $pinned -> $head"
  echo "# compare: https://github.com/$repo/compare/$pinned...$head"
  echo
  echo "## 対象パスに触れたコミット"
  while read -r p; do
    [[ -z "$p" ]] && continue
    echo "### $p"
    gh api "repos/$repo/commits?sha=$head&path=$p&per_page=20" \
      --jq '.[] | select(.sha != "'"$pinned"'") | "  " + .sha[0:9] + "  " + (.commit.message | split("\n")[0])' 2>/dev/null
  done < <(jq -r '.paths[]' <<<"$entry")
  echo
  echo "## 差分（マニフェストのパス配下のみ）"
  local prefixes
  prefixes="$(jq -r '.paths | join("|")' <<<"$entry")"
  gh api "repos/$repo/compare/$pinned...$head" -H "Accept: application/vnd.github.v3.diff" 2>/dev/null \
    | awk -v prefixes="$prefixes" '
        BEGIN { n = split(prefixes, pre, "|"); keep = 0 }
        /^diff --git / {
          keep = 0
          for (i = 1; i <= n; i++) {
            if (index($0, " a/" pre[i]) > 0 || index($0, " b/" pre[i]) > 0) { keep = 1; break }
          }
        }
        keep { print }
      '
}

report() {
  local results outdated
  results="$(collect | jq -sc '.')"
  outdated="$(jq '[.[] | select(.status=="outdated")] | length' <<<"$results")"

  echo "外部由来Skillの上流照合（マニフェスト: .agents/skills/upstream.json）"
  echo
  jq -r '.[] |
    (if .status=="outdated" then "[更新あり] " elif .status=="error" then "[照合失敗] " else "[最新    ] " end)
    + .name + "  " + .repo
    + (if .status=="outdated" then
        "\n            固定: " + .pinned[0:9] + " -> 上流: " + .head[0:9]
        + "\n            変更パス: " + (.changed_paths | join(", "))
        + "\n            compare: " + .compare
       else "" end)' <<<"$results"
  echo
  if [[ "$outdated" -gt 0 ]]; then
    echo "更新あり: ${outdated}件。差分の確認は次を実行する。"
    jq -r '.[] | select(.status=="outdated") | "  .agents/scripts/skill-upstream-check.sh --diff " + .name' <<<"$results"
    echo
    echo "反映は自動で行わない。日本語化とローカル安全規則を維持したまま手動でマージし、"
    echo "upstream.json の pinned と .agents/skills/README.md の出典欄を更新する。"
  else
    echo "すべて固定コミットの内容と一致している。対応は不要。"
  fi
}

case "${1:-}" in
  --json) collect | jq -s '.' ;;
  --diff) [[ -n "${2:-}" ]] || { echo "エラー: --diff にSkill名を指定してください。" >&2; exit 1; }; show_diff "$2" ;;
  "" ) report ;;
  -h|--help) sed -n '2,9p' "${BASH_SOURCE[0]}" ;;
  *) echo "エラー: 不明な引数 '$1'" >&2; exit 1 ;;
esac
