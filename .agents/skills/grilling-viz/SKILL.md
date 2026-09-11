---
name: grilling-viz
description: >
  要件整理や設計の確認質問を、選択肢と自由入力でまとめて回答し、コピーできる単独HTMLにする。質問票、回答フォーム、設計の選択肢をHTMLで可視化したい場合に使用する。
user-invocable: true
---

# 質問と回答のHTML化

目的・制約・未決定事項を整理し、各質問に論点、判断材料、選択肢を付けて下記に従って可視化する。
未導入の `grilling` Skill は必須にしない。既存の設計相談で確定した質問があればその内容を使う。

## 可視化

[部品見本と利用規範](./design-system/component-samples.html) を確認し、次を生成時の正本として使う。

- design-system/tokens.css：デザイン値と用途ラベル
- design-system/components.css：見た目
- scripts/components.js：部品構造
- scripts/answer.js：データ形式・回答処理

以下の `scripts/` は、このスキルのディレクトリからの相対パス。
生成スクリプトは Node.js の標準機能だけで動く。

```sh
node scripts/render.mjs questions.json output.html
node scripts/render.mjs --catalog component-samples.html
```

生成処理は質問データを検証し、JavaScript・CSSのコードテキストをHTML内に埋め込む。
部品見本も上記コマンドで生成してブラウザーで確認する。テンプレート自体を出力先にしない。
生成スクリプトを実行できない場合は、同じ正本を使ってエージェントが埋め込む。
保存先の明示指定がなければワークスペースルートの `.agents/artifacts/<topic>/<YYYY-MM-DD-slug>/index.html` に置く。関連資産は同じフォルダーの `assets/` にまとめる。既存資料は自動移動しない。[成果物エクスプローラー](../../artifact-explorer/README.md) の隔離プレビューでは `localStorage` を使用できないため、回答入力・保存は信頼性を確認したHTMLを別途開いて行う。

- 完成HTMLは、スキルの移動・削除後も単独で動くものにする。
- 回答用HTMLに部品見本や設計説明を混在させない。
- 回答の受渡しは、コピーと元の会話への貼り付けで行う。

## 回答を保持するための更新規則

- 新規生成では生成スクリプトがランダムな識別子をHTML内の `documentId` に書き込む。更新ではファイル名と既存のIDを保つ。
- 質問や選択肢の意味が変わる場合は質問IDを新しくし、旧回答を流用しない。
- 再生成だけを理由に、HTMLから外した質問の保存データを消さない。

更新前に既存データとハッシュを取得し、質問データを編集して同じファイルに生成する。
ハッシュが一致しなければ読み直して統合する。

```sh
node scripts/render.mjs --inspect output.html
node scripts/render.mjs questions.json output.html --if-match SHA256
```

## 確認

HTML単体・オフラインで、入力・コピー・再読み込み後の回答復元を確認する。
ブラウザーを利用できなければ、未確認の操作を報告する。

## 安全規則

- 生成先は依頼範囲内のディレクトリに限定する。`--if-match` の一致確認を省略せず、既存成果物の変更はユーザーの依頼範囲に従う。
- 質問・選択肢は構造化したJSONとして渡し、未信頼の文字列をJavaScriptやHTMLとして実行しない。
- 回答はブラウザーの `localStorage` に残る。共有端末での保存に注意し、パスワード、トークン、機密情報を質問・入力させない。
- 回答の削除はユーザー操作に限定する。HTML更新を理由に旧回答を削除しない。
- 外部通信、追加依存、外部Skillの自動取得を加えない。コピーはユーザー操作で行い、無断で外部送信しない。
- フォームの回答を外部操作の包括承認として扱わない。PR/MR等の承認は既存規約に従う。

## 出典

- 上流: https://github.com/mathbullet/skills
- 固定コミット: `5ab997fcb8a80da4938bacb0a86cbd568e1018a7`
- 上流パス: `plugins/grilling-viz/skills/grilling-viz`
- ライセンス: [MIT](./LICENSE)
- ローカル変更: 既存の日本語本文と同梱コード・資産を保持。未導入 `grilling` への必須依存を質問整理手順へ置換し、呼び出し条件と保存・回答・外部操作の安全規則を追加。
