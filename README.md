# Agent設定・スキル集

Claude CodeとGitHub Copilotで使う共通スキル、Agent定義、補助ツールをまとめた、リポジトリ登録用のコピーです。プロダクトのリポジトリや業務資料は含めません。

## 最初に見る場所

| 場所 | 内容 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | この設定集を扱うAgentの共通ルール |
| [CLAUDE.md](CLAUDE.md) | Claude Codeから共通ルールを読み込む入口 |
| [.agents/skills/README.md](.agents/skills/README.md) | スキルの一覧・追加手順 |
| `.github/agents/` | Copilot用のMAGI Agent定義 |
| `.agents/hooks/` | セッション記録・スキル更新確認のフック本体 |
| `.agents/scripts/` | スキルの上流更新を確認するスクリプト |
| [.agents/artifact-explorer/README.md](.agents/artifact-explorer/README.md) | HTML・PDF成果物を閲覧するローカルツール |
| `config-examples/` | Claude Code・Copilot・VS Codeの設定例 |
| [docs/adr/README.md](docs/adr/README.md) | 判断と作業記録の書き方 |

隠しディレクトリ名は、Agentの探索規則と既存の相対リンクを維持するために残しています。Linuxで一覧を見る場合は `ls -a` を使います。

## コピーと元の環境の関係

- 2026-09-11時点のワークスペース共通資産をコピーしています。元ファイルの移動・削除はしていません。
- 現在のClaude Codeの個人用リンク、稼働中の閲覧ツール、元のAgent設定は変更していません。
- このコピーは自動同期されません。現在の実行環境の正本は元のワークスペース側です。
- Gitの初期化、ステージング、コミット、リモート登録、pushは行っていません。このディレクトリの内容を登録先のリポジトリへ配置できます。
- コピー済みスキルの説明には元ワークスペースの運用例が残っています。個人用リンクの作成済みという記述は配布先には当てはまりません。

## 利用する場合

1. このディレクトリを新しい作業ルートとして配置し、[REPOSITORIES.md](REPOSITORIES.md) に必要な対象リポジトリを記載します。
2. Claude Codeでは、利用したい `.agents/skills/<skill-name>` へのリンクを、新しい作業ルートの `.claude/skills/<skill-name>` に登録します。既存エントリーを上書きしないでください。現在の `~/.claude/skills/` は元の環境を指しているため、このコピーへ自動では切り替わりません。
3. Copilotでは `.agents/skills/` と `.github/agents/` を利用します。MAGIには別途 `magi` CLIが必要です。スキルごとの依存・ライセンスも確認してください。
4. フックやVS Codeのタスクは `config-examples/` の内容を確認し、必要な項目だけ既存設定へ統合してください。設定ファイル全体を上書きしないでください。
5. 成果物閲覧ツールを使う場合は、そのREADMEに従って仮想環境を新しく作成します。成果物と索引DBは配布していません。

`config-examples/` は設定の保管場所であり、自動では有効になりません。上流更新確認フックは外部通信を行います。MAGIフックは `magi` CLI、セッション記録フックはBash・jq等を必要とします。Windowsネイティブでのフック動作は未検証です。VS Codeタスク例にはfolderOpen時の起動設定があるため、有効化前に確認してください。

## 含めないもの

プロダクトのソースコード、生成済みHTML・PDF、セッション履歴、既存ADR本文、回答データ、SQLite索引、仮想環境、依存インストール先、キャッシュ、ログ、秘密情報用ファイル、個人用設定、予約タスク、ホームディレクトリの設定、MCP接続設定はコピー対象外です。

公開前には組織名・内部URL・内部運用情報が残っていないか確認してください。秘密情報の網羅的監査を保証するものではありません。第三者由来のスキル・同梱ライブラリのLICENSEと出典は保持しています。配布条件は個別のライセンスに従います。# agent-config_Work
