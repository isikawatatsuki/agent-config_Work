# grill-with-docs 日本語ガイド

出典: [原文（固定コミット）](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/docs/engineering/grill-with-docs.md)

> 以下はリンク先の説明文の日本語訳。報告済みの不具合や他スキルへの評価は原文の記述であり、この環境で再現確認した事実ではない。末尾の「このワークスペースでの違い」はローカル版の補足である。

## 何をするか

`grill-with-docs` は、計画や設計について、ユーザーと[エージェント](https://www.aihero.dev/ai-coding-dictionary/agent)が同じ理解に達するまで質問する。その過程で用語と重要な判断をリポジトリへ書き込む。[grill-me](https://aihero.dev/skills-grill-me) と同じ、質問を提示し、回答を待ち、次の質問に進む対話を、コードベースに向けて行う。

これは**[状態を持つ](https://www.aihero.dev/ai-coding-dictionary/stateful)**スキルである。ほかの質問スキルが[セッション](https://www.aihero.dev/ai-coding-dictionary/session)の内容を頭の中に残すのに対し、このスキルはディスク上にファイルを残す。用語は意味が確定した瞬間に `CONTEXT.md` へ記録し、最後にまとめて書かない。判断は3条件を通過するとADRになる。この違いこそが特徴であり、問題の原因にもなる。成果物は実際のリポジトリ内のファイルなので、期待したのに生成されなかったり、複数人で書くうちに内容がずれたりする。

## いつ使うか

`/grill-with-docs` と入力して呼び出す。エージェントは自動では使わない。

リポジトリで変更を始める際、計画がまだ曖昧で、対象を表す言葉も定まっていないときに使う。単一セッション向けの道具であり、状況によって使うスキルは異なる。

| 状況 | 使うスキル |
| --- | --- |
| 作業ディレクトリで作業していない | [grill-me](https://aihero.dev/skills-grill-me) |
| リポジトリがあり、1セッションで整理できる変更 | `grill-with-docs` |
| 新規開発や大規模機能など、1セッションに収まらない取り組み | [wayfinder](https://aihero.dev/skills-wayfinder) |
| ドメイン文書がなく、特定の機能変更も念頭にないリポジトリ | 変更ではなくリポジトリ全体を対象とした `grill-with-docs` |
| 他人しか知らない情報が必要で判断できない | [to-questionnaire](https://aihero.dev/skills-to-questionnaire) |

`/grill-with-docs` と `/wayfinder` の違いは、計画を単一セッションで扱うか、複数セッションで扱うかにある。

## 前提条件

このスキルはリポジトリへ書き込むため、安全に書き込める場所で使う必要がある。確定した用語はルートの `CONTEXT.md` へ入る。ルートの `CONTEXT-MAP.md` が複数コンテキストの構成を示していれば、該当コンテキストの `CONTEXT.md` へ入る。判断は `docs/adr/` に記録する。いずれも必要になってから作成するため、最初の用語や判断が確定する前にひな形を用意する必要はない。

原版は2つのスキルも必要とする。自身の `SKILL.md` が、それらへ委譲する1行だけだからである。[grilling](https://aihero.dev/skills-grilling) が質問を、[domain-modeling](https://aihero.dev/skills-domain-modeling) が文書化を担当する。原版の `grill-with-docs` だけを導入しても動作しない。

## 記録として残るもの

セッションから生まれるものは3種類あり、同じ扱いではない。

| 確定した内容 | 保存先 |
| --- | --- |
| プロジェクト固有の言葉である用語 | 確定した瞬間に `CONTEXT.md` |
| 元に戻しにくく、背景なしでは意外で、実際のトレードオフを伴う判断 | `docs/adr/` のADR |
| それ以外の判断 | 会話内のみ |

3行目が見落とされやすい。`CONTEXT.md` は意図的に用語集だけとし、実装詳細、[仕様](https://www.aihero.dev/ai-coding-dictionary/spec)、作業メモを含めない。ADRは3条件すべてを満たす必要があるため、大半の判断は対象にならず、多くのセッションでは1件も作られない。用語集が明確になり、ADRはゼロという結果も設計どおりである。ただし、その場合、合意した内容の多くはその[コンテキストウィンドウ](https://www.aihero.dev/ai-coding-dictionary/context-window)にしか存在しない。[会話を消去](https://www.aihero.dev/ai-coding-dictionary/clearing)せず、そのまま [to-spec](https://aihero.dev/skills-to-spec) へ渡す。

中心となるのは用語集である。このスキルが実際に作るのはドメインの言葉であり、プロジェクト固有の語彙を一度合意することで、ユーザー、エージェント、同僚が毎回定義し直さずに済む。ただし、それによってエージェントの性能が上がるという点には異論もある。用語と平易な英語による説明で[モデル](https://www.aihero.dev/ai-coding-dictionary/model)の結果は変わらず、語彙の効果は人間同士のコミュニケーションを短くすることだ、という反論である。この解釈でも用語集の価値は残り、価値の所在が変わるだけである。

## よくある質問

### これと /wayfinder のどちらを使うべきか

範囲で決まる。1セッションで整理できるならこちらを使う。収まらないなら [wayfinder](https://aihero.dev/skills-wayfinder) を使い、まず決定の[チケット](https://www.aihero.dev/ai-coding-dictionary/ticket)を地図に整理する。Wayfinder は時間がかかり情報量も多いため、範囲が明確な機能に使うのはよくある誤りである。こちらを置き換えるものではなく、地図の一部について質問セッションへ移ることもできる。

### 実行したのに CONTEXT.md もADRも作られない

既知の原因は2つある。単純なのは、記録対象がなかった場合である。ADRには3条件が必要で、新しい語彙もなければ何も書く必要はない。

もう1つは不具合である。仕様駆動開発のラッパー、マルチエージェント基盤、別の処理の一段階として呼び出す規則など、ほかの制御層の内部で実行すると、質問は行われてもファイル書き込みが通知なく行われないという報告がある。原文では報告済み・未修正とされている。その構成では、成果を信頼する前に作業ディレクトリを確認する。

### 一度にすべてを質問し、推奨回答も CONTEXT.md の説明もなかった

2つの依存スキルを読み込めていない状態である。`SKILL.md` は1行の委譲なので、[grilling](https://aihero.dev/skills-grilling) と [domain-modeling](https://aihero.dev/skills-domain-modeling) を取得できないエージェントは、質問の意味を推測し、整理されていない質問を一括で提示してしまう。

一部だけ読み込まれると、さらに分かりにくい。`grilling` だけが読み込まれると、対話は適切でも記録が残らない。原文ではモデルや[推論の労力設定](https://www.aihero.dev/ai-coding-dictionary/effort)との関連が指摘され、このスキルで最も多く報告される問題とされている。疑わしい場合は、どのスキルを読み込んだか直接質問する。

### それ以外の判断はどこへ行ったのか

会話内にしか残らない。これが最も本質的な未解決の不満である。用語集は仕様ではなく、ほとんどの回答はADRにならず、各回答から仕様、チケット、テストまでをつなぐ台帳もない。順序保証、行わないこと、数値の既定値などの正確な回答が、後段で曖昧な文章になり、完成したように見えて実際の合意が抜け落ちることがある。現在の対策は、同じセッションを [to-spec](https://aihero.dev/skills-to-spec) へ直接渡し、自分の回答と仕様を読み比べ、すべて記録されたと思い込まないことである。

### 文書がまったくない既存リポジトリにも使えるか

使える。ADR、ドメインの言葉、設計原則がないコードベースに適している。呼び出して「リポジトリの文書化を手伝って」と伝える。コミュニティでは [improve-codebase-architecture](https://aihero.dev/skills-improve-codebase-architecture) と組み合わせて `CONTEXT.md` を作成・修復する使い方もある。エージェントはコードを読み、見つけたものについて質問するため、既存のどの言葉が適切なのかをユーザーが判断して方向付ける。

### セッションが終わったら何をするか

終了メッセージが次の行動を明確にしない傾向は、既知の改善点である。基本の流れでは、同じ会話で [to-spec](https://aihero.dev/skills-to-spec) に進む。すぐに実装できるほど小さな変更なら [implement](https://aihero.dev/skills-implement) へ進む。

### なぜこの名前なのか

原文では、名前には誰も満足しておらず、動作をより正確に表す `grill-domain-model` への改名提案があるが、進展はないとしている。改名が実現すれば文書ページも移動し、URLも変わる。

## 正しく機能している目安

- `CONTEXT.md` が最後にまとめて現れるのではなく、セッション中に用語ごとに更新される。
- 用語集は短く正確な定義だけで構成され、実装詳細や仕様のような文章がない。
- コードベースで分かることはユーザーに尋ねず、コードベースを読んで解決する。
- ADRは少数またはゼロで、作成されるものは再議論を避けたい判断である。
- ユーザーが使った言葉が既存用語集と違えば、その違いを指摘する。

## 全体の流れでの位置

`grill-with-docs` は主要な開発フローの先頭にある。

```text
grill-with-docs → to-spec → to-tickets → implement → code-review
```

仕様を書く前に共通理解と確定した語彙を作り、[to-spec](https://aihero.dev/skills-to-spec) が追加の聞き取りなしにまとめられるようにする。近いスキルは、リポジトリやファイルなしで同じ対話をする [grill-me](https://aihero.dev/skills-grill-me) と、用語集・ADRの規律を担う [domain-modeling](https://aihero.dev/skills-domain-modeling) である。両方の質問スキルは [grilling](https://aihero.dev/skills-grilling) を基盤とする。上流の [wayfinder](https://aihero.dev/skills-wayfinder) は単一セッションに収まらない取り組みを整理し、地図の一部をこちらへ渡せる。どのスキルや流れが適切か不明な場合は [ask-matt](https://aihero.dev/skills-ask-matt) が案内する。

## このワークスペースでの違い

- 依存スキルの手順を本体に統合しているため、`grilling` と `domain-modeling` の別途導入は不要。
- Session Decision Record が必須であり、原版の「その他の判断は会話内のみ」と異なり、依頼・判断・検証結果を既存規約に従って記録する。
- 正式ADRの昇格条件と書式も既存規約が優先。原版の3条件を理由に必須記録を省略しない。
- 記載した後続スキルは今回導入していない。後続作業はユーザーの指示と、実際に利用できるスキルに応じて進める。
- 質問と文書化は日本語で行い、コード、識別子、コマンド、パス、URLは原文を維持する。