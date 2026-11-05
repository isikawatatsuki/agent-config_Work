# Interactive Flow Dashboard Skill のGitHub登録

Status: completed

## Request
既存の interactive-flow-dashboard Skill をGitHubに登録する。既存の会話で指定された「親はSonnet 5.5、HTMLコーディングは下位のHaiku」の役割分担を反映する。

## Context and constraints
- 登録先は共通Agent Skill管理用の isikawatatsuki/agent-config_Work。
- 公開リポジトリのため、業務システム固有のコード、機密URL、認証情報は登録しない。
- 既存のSkillの思想（実際の処理順序、開発状態と統合・検証状態の区別、MR/PR根拠、インタラクション）を保持する。
- GitHubへの登録は今回のユーザーの明示依頼に基づく。PR/MRの新規作成やマージは依頼されていない。

## Decisions
- 登録先は .agents/skills/interactive-flow-dashboard/SKILL.md とする。共通Skillの正本を .agents/skills に置く既存構成に従う。
- 親エージェントはSonnet 5.5を優先し、コード調査・進捗判定・品質確認を担当する。HTML/CSS/JavaScript/SVGの実装は利用可能なHaiku系サブエージェントへ優先して委譲する。
- バージョン名や委譲ツールを仮定しない。実行環境にモデルがなければ制約を表示する。
- 独自Skillなので外部由来Skillの固定SHA台帳や外部LICENSEの追加は不要。

## Actions
- 調査：リポジトリの README、AGENTS.md、.agents/skills/README.md、ADR運用ルールを確認。
- 実装：新しいSkill定義を追加し、登録済みSkill一覧へ追記した。

### 引き継ぎメモ
- 目的・現在地：GitHub上の共通Skill一覧への登録が完了した。
- 判断：処理フローと根拠を親が確定し、見た目とHTML実装だけをHaikuに委譲する。
- 実装：.agents/skills/interactive-flow-dashboard/SKILL.md と .agents/skills/README.md を変更。
- 検証：GitHubへ書き込んだファイルを再取得し、内容・リンク・役割分担の記述を確認する。Claude Codeでの実際の認識・下位モデル起動は利用者環境で未検証。
- 次の一手：利用先のClaude CodeのSkill探索先へ登録し、/skills で認識を確認する。

## Validation
- GitHub Connectorによる登録とREADME更新が成功。
- Skillの画面生成・サブエージェント動作は実行していない（仕様書のみを登録）。

## Outcome and follow-up
- 公開リポジトリへ独自Skillを登録した。
- 実行環境のサブエージェントとモデル割当ては未検証。自動認識や実行済みとはみなさない。
- 正式ADRへの昇格は不要（既存Skills配置規約に従った追加であり、新たな横断運用原則の変更はない）。
