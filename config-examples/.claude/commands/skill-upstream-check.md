---
description: 外部由来Skillの固定コミットと上流GitHubの最新を照合し、更新があれば差分を報告する
allowed-tools: Bash(.agents/scripts/skill-upstream-check.sh:*), Read, Grep
---

`.agents/skills/upstream.json` に登録された外部由来Skillについて、上流GitHubの更新を照合する。

## 手順

1. 照合を実行する。

   ```bash
   .agents/scripts/skill-upstream-check.sh
   ```

2. `[更新あり]` のSkillについて差分を確認する。引数は対象Skill名。

   ```bash
   .agents/scripts/skill-upstream-check.sh --diff <skill>
   ```

3. 差分をユーザーへ日本語で報告する。Skillごとに次を示す。
   - 固定コミットと上流の最新コミット
   - 上流での変更内容の要約（コミット件名と主な差分）
   - ローカルの日本語化・安全規則・統合との衝突有無
   - 反映すべきか、見送るべきかの推奨と理由

## 制約

- ローカルの `.agents/skills/` 配下を、このコマンド内で変更してはいけない。検出と報告のみを行う。
- 反映はユーザーが対象Skillを指定して明示的に依頼した場合のみ行う。その際も次を守る。
  - 上流をそのまま上書きしない。日本語化、ローカル安全規則、統合済みの依存スキル内容を維持する。
  - `.agents/skills/README.md` のセキュリティ確認項目を上流の新規記述に対して再監査する。
  - 反映後に `upstream.json` の `pinned`、`.agents/skills/README.md` の出典欄、対象 `SKILL.md` の出典欄を新しいコミットSHAへ更新する。
- 正本はベンダリングコピーとする。`eli5` の plugin は無効化済み。`diagram-design` は plugin のみが5コマンドを提供するため plugin を有効のまま残しており、二重管理を許容している。反映は常にベンダリング側へ行い、plugin 側を手で書き換えない。
