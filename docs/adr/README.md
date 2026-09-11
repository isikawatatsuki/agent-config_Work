# ADRとセッション意思決定記録

Claude Code、GitHub Copilot、その他のAIエージェントが行うすべての依頼について、判断と検証結果をこのワークスペース内へ記録する。

## 保存先

```text
docs/adr/
├── README.md
├── NNNN-<short-title>.md
└── sessions/
    └── YYYY-MM-DD/
        └── <session-id>.md
```

- 全依頼の Session Decision Record: `docs/adr/sessions/YYYY-MM-DD/<session-id>.md`
- 永続的な判断のADR: `docs/adr/NNNN-<short-title>.md`
- 対象リポジトリ固有の既存ADR規約がある場合は、その規約を優先する。

## adrs CLI

正式ADRの作成、検索、状態変更、関連付け、診断には [`joshrotenberg/adrs`](https://github.com/joshrotenberg/adrs) を使用する。バージョンは `0.12.1` を基準とする。

```bash
cargo install adrs --version 0.12.1 --locked
adrs new "判断のタイトル"
adrs list
adrs search "検索語"
adrs doctor
```

プロジェクト設定はワークスペースルートの `adrs.toml` に置く。正式ADRを作成または変更した場合は、最終応答前に `adrs doctor` が成功することを確認する。

Claude Code向けの `.mcp.json` でのみ `adrs mcp serve` を登録している。MCP設定の再読込後、Claude CodeからADRの検索・作成・更新ができる。GitHub Copilotを含む他のAIエージェントにはMCPサーバーを登録しない。

## Session Decision Record

質問、調査、設計、実装、レビュー、運用、文書作成を含むすべての依頼で、1セッションにつき1件を作成する。

必須セクション:

- `Request`: 依頼と成功条件
- `Context and constraints`: 根拠、前提、制約、対象範囲
- `Decisions`: 選択、理由、代替案、影響
- `Actions`: 調査、設計、実装、レビューなど作業区分ごとの内容
- `Validation`: 実行した検証と結果
- `Outcome and follow-up`: 完了状態、残リスク、ADR昇格判断

最終応答前に未記入欄をなくし、`Status` を `completed` または `blocked` にする。

## ADRへの昇格

次の判断は正式なADRへ昇格する。

- アーキテクチャ、公開API、データモデル、セキュリティ、インフラ、運用方法を変更する
- 複数の合理的な選択肢から、将来の実装や運用を拘束する選択を行う
- チームが後から「なぜ」を参照する必要がある
- 既存ADRを置換、廃止、または例外扱いする

軽微な実装、判断を伴わない調査や質問回答、コード変更を伴わないレビュー所見は通常昇格しない。

## 機密情報

Secret、Credential、Token、個人情報、ユーザー入力の機微情報、ソースコード全文は記録しない。

## ADRの状態

- `proposed`: 提案中
- `accepted`: 採用済み
- `superseded`: 後続ADRに置換済み
- `deprecated`: 廃止済みで置換先なし

判断が変わった場合は既存ADRを書き換えず、新しいADRを作成して相互にリンクする。