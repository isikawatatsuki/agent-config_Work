# ワークスペース Skills

このディレクトリでは、このワークスペースで共有する Agent Skill を管理する。

## 構成

Skill ごとに独立したディレクトリを作成する。

```text
.agents/skills/
├── README.md
└── <skill-name>/
    ├── SKILL.md          # 必須
    ├── LICENSE           # 外部由来の場合
    ├── references/       # 必要な場合のみ
    ├── scripts/          # 監査済み実行ファイルのみ
    └── assets/           # テンプレートなど
```

`SKILL.md` の `name` とディレクトリ名は一致させる。Skill 間でファイルを共有せず、
必要な資料は各ディレクトリ内に置く。

### Claude Codeへの登録

この端末では、`~/.claude/skills/<skill-name>` からワークスペースの `.agents/skills/<skill-name>` へのシンボリックリンクで共通Skillを登録しています。Skill本体の正本は `.agents/skills/` のままです。追加時は個人用探索先にもリンクを登録し、既存エントリーは上書きしないでください。個人用登録なので、この端末の他プロジェクトでも利用できます。

`.agents/skills/` への配置だけではClaude Codeへの登録確認になりません。[公式の探索先とリンク対応](https://code.claude.com/docs/en/skills#where-skills-live)を参照してください。リンク先の `SKILL.md` を読み取れることを確認し、Claude Code 2.1.233以降では `claude plugin validate .agents/skills` で定義を検証します。最後にClaude Codeの `/skills` で表示を確認してください。反映されない場合はセッションを再起動してください。

## 登録済み Skill

| Skill | 用途 | 出典 | 状態 |
|---|---|---|---|
| `show-me` | 図やHTML資料による視覚的な説明 | `humanlayer/skills@6ab9013` | 日本語化・安全規則追加済み |
| `hve-code-review` | 複数観点とリスク深度によるコードレビュー | `microsoft/hve-core@f97a38c` | 単体化・日本語化・安全規則追加済み |
| `two-axis-code-review` | 規約と仕様の2軸コードレビュー | `mattpocock/skills@5c89081` | 日本語化・外部取得制限・安全規則追加済み |
| `magi-council` | 3人格の独立評価と決定論的な採決 | `isikawatatsuki/magi-council-skill@e3c57abc2cd74f13cde47886d77e6d606961df2f` | Copilot Custom Agent・Hook対応、監査済み |
| `diagram-design` | 編集品質の図表作成とdraw.io・Mermaidの再描画 | `cathrynlavery/diagram-design@2724fd2efd8c6737f6fa704fbf5da52d67375497` | `SKILL.md`日本語化済み |
| `eli5` | 大きな図と少ない言葉による初学者向け解説 | `anthropics/claude-plugins-community@a727be1c7bd6064419b6f60d71993a19198adc17` | 日本語化済み |
| `implementation-handoff` | 実装時の個人用引き継ぎ記録と、明示承認を必須とするPR/MR下書き・登録 | ワークスペース独自 | 日本語・自動呼び出し対応・外部書き込み承認必須 |
| `grill-with-docs` | 質問による設計の具体化と用語集・ADRの記録 | `mattpocock/skills@3cca18b368ae95cdbdebbff572ccafa662551015` | 日本語化・依存手順統合・既存ADR規約対応・安全規則追加済み |
| `documenting-with-sources` | 出典を伴う文書の引用・参照・事実性の規約 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 日本語化・単体化・安全規則追加済み |
| `explain` | 用語集とMermaid図を備えた概念・システム解説 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 日本語化・安全規則追加済み |
| `grilling-viz` | 選択肢と自由入力を備えた単独HTML質問票 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 単体化・同梱コード監査・安全規則追加済み |
| `html` | デザイン資産を使ったHTML解説資料 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 日本語・監査済み・Linux/Windows共通PDF CLI対応 |
| `ja-text-communication` | 日本語の技術文書・報告の作成と推敲 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 日本語・用途別呼び出し・安全規則追加済み |
| `paper-details` | 数式・図表・実験を含む論文の詳細解説 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 日本語化・単体化・Linux/Windows手順とUTF-8画像抽出対応 |
| `survey` | 論文・記事・SNS・業界動向の横断調査 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 日本語化・単体化・安全規則追加済み |
| `writing-quotation` | 原文と日本語訳を併記する引用書式 | `mathbullet/skills@5ab997fcb8a80da4938bacb0a86cbd568e1018a7` | 日本語化・著作権/外部入力の安全規則追加済み |

### mathbullet由来Skillの利用上の注意

- 各Skillは `/html`、`/survey`、`/grilling-viz` などの名前で呼び出す。認識されない場合はチャットを新規作成し、必要ならウィンドウを再読み込みする。
- `html` の見本は外部フォント・CDNを参照する。機密資料や通信制限のある環境では外部参照を使わない。PDF出力は [共通Python CLI](./html/render-pdf.py) をLinuxで `python3`、Windowsで `py -3` により起動する。Python 3.9以上とChrome/Chromium/Edgeが必要。既存PDFの上書きは拒否する。詳細は [htmlの手順](./html/SKILL.md) を参照。
- `paper-details` の画像抽出にはPython 3.9以上とPyMuPDF 1.24.3以上が必要。Linux・Windowsの仮想環境と起動手順は [paper-details](./paper-details/SKILL.md) を参照。依存は自動導入しない。スクリプトは同名出力を上書きし得るため、空の専用出力先を指定する。manifestはUTF-8で出力する。
- PDF生成と画像抽出はLinuxで実処理を検証済み。Windowsはブラウザー検出の模擬テストまでで、実機での検証は未実施。
- `grilling-viz` の生成と回答処理は外部依存なし。回答はブラウザーのlocalStorageに保存されるため、機密情報を入力しない。
- `ja-text-communication` は常時読み込みを強制せず、日本語文書の作成・推敲時に使用する。既存のSkillやユーザー指定の書式を置き換えない。

## HTML/PDFの共通保存先

HTML/PDF生成物は、明示された保存先がなければワークスペースルートの `.agents/artifacts/<topic>/<YYYY-MM-DD-slug>/` に保存する。HTMLは `index.html`、PDFと関連資産も同じ成果物フォルダーにまとめる。対象は `html`、`show-me`、`eli5`、`diagram-design`、`grilling-viz`、`paper-details` のHTML/PDF出力。既存資料・入力PDF・Markdownレポート・Skill本体は自動移動しない。

[資料エクスプローラー](../artifact-explorer/README.md) で一覧・プレビュー・全文検索・タグ編集・移動を行う。生成後は「索引を更新」を押す。隔離プレビューはCDN・外部通信・localStorageを制限するため、grilling-vizの回答保存は信頼性を確認したファイルを別途開く必要がある。上流更新時もこのローカル保存規約を維持する。

## 追加手順

1. 取得元をコミットSHAまたはリリースタグで固定する。
2. Skill 配下の全ファイルを読み、命令、スクリプト、フック、依存関係を監査する。
3. 必要なファイルだけを `<skill-name>/` に配置する。インストーラーを無条件に実行しない。
4. 外部由来の場合はライセンスと出典、固定したバージョンを残す。
5. 新規作成、外部導入、更新のいずれでも、登録前に `SKILL.md` の `description`、本文、およびユーザー向け参照資料を日本語化する。更新時も既存の日本語化を維持し、英語へ戻さない。
6. コード、識別子、コマンド、パス、ログ、API名、製品名、リンク先、アンカーは正確性を優先して原文を維持する。
7. フロントマター、参照先、実行ファイル、安全規則を検証してから利用する。
8. この README の一覧を更新する。
9. 外部由来の場合は `upstream.json` へ取得元リポジトリ、参照ブランチ、固定SHA、上流パスを登録する。
10. Claude Codeでも利用する場合は、上記「Claude Codeへの登録」に従って探索先へのリンクと認識を確認する。

## 上流更新の追従

外部由来Skillは `upstream.json` を機械可読な追従台帳として扱う。照合は次で行う。

```bash
.agents/scripts/skill-upstream-check.sh            # 全Skillの照合レポート
.agents/scripts/skill-upstream-check.sh --json     # 機械可読な照合結果
.agents/scripts/skill-upstream-check.sh --diff <skill>  # 上流差分の表示
```

照合は固定SHAと参照ブランチ先端における上流パスのツリーハッシュを比較する。Claude Code では
`/skill-upstream-check` から実行できる。

定期照合は `.agents/hooks/skill-upstream-session-check.sh` を `SessionStart` Hook に登録して行う。
照合本体はバックグラウンドで実行し、Hookは直前の結果だけを即座に返すため起動を待たせない。
実行間隔は20時間で、更新が無い場合は何も出力しない。結果は
`~/.claude/cache/skill-upstream-check/last-result.json` に保持する。

外部由来Skillを plugin としても導入している場合、正本はベンダリングコピーとし、plugin は無効化する。
plugin の更新は日本語化を英語へ戻すため、`AGENTS.md` の日本語化維持ルールを満たせない。
ただし plugin のみが提供するコマンドがある場合は、そのSkillに限り plugin を有効のまま残し、
二重管理を許容する。その場合もSkill本体の正本はベンダリングコピーとし、上流更新はそちらへ反映する。

スクリプトは検出と差分表示のみを行い、Skillファイルを変更しない。日本語化とローカル安全規則を
上流の上書きで失わないため、反映は差分を監査した上で手動マージとする。反映後は `upstream.json` の
`pinned`、この README の出典欄、対象 `SKILL.md` の出典欄を新しいコミットSHAへ揃える。

## セキュリティ確認

- 外部通信先と送信データが明確で、必要最小限か。
- 秘密情報、認証情報、個人情報を読み取りまたは出力する命令がないか。
- シェルコマンド、フック、スクリプトに破壊的操作や権限昇格がないか。
- ユーザー入力をコマンド、HTML、SQL、パスへ安全でない形で埋め込まないか。
- ワークスペース外への書き込みや既存ファイルの無断上書きがないか。
- 外部スクリプトや依存パッケージを実行時に無条件で取得しないか。
- Skill 内の命令が既存の上位指示や承認要件を迂回しないか。

問題がある命令は削除または制約を追加し、変更内容を `SKILL.md` の出典欄へ記録する。

## フロントマター

```yaml
---
name: skill-name
description: "何を行い、どの依頼で使用するかを日本語で具体的に記載する。"
user-invocable: true
---
```

自動呼び出しを禁止する場合は `disable-model-invocation: true`、スラッシュコマンドからの
呼び出しを禁止する場合は `user-invocable: false` を明示する。