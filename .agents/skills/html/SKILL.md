---
name: html
description: 概念・仕組み・調査内容を、HTML による視覚的な説明ドキュメントとして作成・編集する。
user-invocable: true
---

# HTML による説明ドキュメント

既存のサイトや成果物のデザイン指定、出力形式、上位指示がある場合はそちらを優先する。

## 文章

説明内容と日本語表現を補うため、次のスキルの併用を推奨する。

- `explain`：概念や仕組みを説明するときの用語定義、説明の粒度、構成
- [`japanese-tech-writing`](https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d)：日本語の技術文書、記事、解説文の構成と文章規範
- [`cognitive-rhythm-writing`](https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432)：読み物としての緩急が必要な長文の文章規範

いずれも推奨スキルであり、`html` の必須依存ではない。
未導入の Skill をリンク先から自動取得・実行しない。併用できない場合も、用語の初出定義、背景・仕組み・具体例の順序、根拠と推測の分離をこの Skill 単独で行う。

## 成果物

- HTML を作る
- ビルドなしでブラウザが直接描画できる状態にする
- 保存先の明示指定を優先する。指定がなければワークスペースルートの `.agents/artifacts/<topic>/<YYYY-MM-DD-slug>/index.html` に保存する。PDFは同じフォルダー、関連資産は `assets/` にまとめる。既存資料は自動移動しない。共通運用は [成果物エクスプローラー](../../artifact-explorer/README.md) を参照する。
- ファイル名は `{yyyymmdd}-{内容を表すケバブケース}.html` とする。既存ファイルの更新では名前を変えない
- 個別の文書管理システム、メタデータ、Viewer、公開先に関する規則は、このスキルを参照する上位スキルの指示に従う

## デザインシステム

作成前に `design-system/component-samples.html` を確認する。コンポーネント集は `design-system/document.css`、数式コピー機能は `design-system/math-copy.js` を正とする。

既定では、成果物と一緒に必要なファイルを配置し、次の相対パスで読み込む。上位スキルが共有アセットのパスを指定した場合は、その指定を優先する。

以下は上流のオンライン構成例であり、CDN利用の許可ではない。Google Fonts、jsDelivr、cdnjsへの通信が発生する。見本HTMLをブラウザーで開く場合も同様で、未信頼の外部JavaScriptはページ内容へアクセスできる。
外部通信が許可されていない場合や機密資料の場合は、外部参照を省き、ローカルの利用可能な字体・監査済みライブラリを使う。未導入ライブラリを自動取得しない。オフラインで数式やハイライトを描画できなければ制約を報告する。

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Ubuntu+Sans:wght@400;500;700&family=Noto+Sans+JP:wght@400;500;700&family=Ubuntu+Mono:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="./design-system/document.css">
<script src="./design-system/math-copy.js"></script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>
<script>document.addEventListener("DOMContentLoaded", () => hljs.highlightAll());</script>
```

主要規則は次のとおり。

- 背景は `#FAF9F6`。部品は白地、黒罫線、角丸を基本とする
- 自然言語は Ubuntu Sans と Noto Sans JP、コード・URL・日付は Ubuntu Mono を使う
- 有彩色はリンク青 `#2990DA` とアクセント赤 `#D63A2F` に限定する
- 赤い強調は原則として 1 ページ 1 箇所までとする
- シンタックスハイライトとコード差分の色は、意味を区別する機能色としてこの制限の対象外とする
- 余白は上下左右の均衡を保つ
- 引用は `.mb-quote` を使い、原文と訳文を同じ文字サイズ・色で上下に並べる
- `.mb-chip` は並列の固有名や分類名の列挙にだけ使う
- 絵文字や矢印文字を図記号として使わない。必要な記号はインライン SVG で描く
- 表は短い対応関係に使い、3 列までを基本とする
- 行見出しのセルには `.mb-rowlabel` を付け、語中の折り返しを防ぐ
- コード差分は `pre.mb-diff` を使い、変更理由を散文で説明してから必要な断片を示す
- ページ固有の `<style>` は図の配置調整など最小限にとどめる

## 構成とフォーマット

説明対象に合わせて、並置、図解、タイムライン、要約、折りたたみを使い分ける。
一方向の単純な手順を、必要性なくフローチャートにしない。

基本構成は次の順とする。

1. 背景と要点
2. 本論
3. 具体例
4. 補足・限界・関連事項

h1 とリード文の後に `.mb-toc` の目次を置き、各 h2 に対応する `id` を付ける。

### 用語リスト

専門用語は本文の初出で定義する。
用語リストは、複数箇所から参照する用語がある場合だけ設ける。
用語リストの位置は文書ごとに変更しない。
ブラウザ幅 1400px 以上では、本文右側の専用欄へ表示する。
ブラウザ幅 1399px 以下では、本文末尾へ表示する。
配置の切り替えは共有 CSS だけが担当し、用語リストによってヘッダー、リード、目次、要約、本文の幅を縮めてはならない。
マークアップは `aside.mb-glossary` と `dl`、`dt`、`dd` を使う。
正解例は `design-system/component-samples.html` を参照する。

## 図

- `.mb-figure` は、画像・SVGなどの視覚資料とキャプションを一つにまとめる外枠である。特定の図形や「矢印で結んだ箱」を意味しない
- `.mb-figure-frame` は視覚資料の表示面、`figcaption` は図番号・説明・出所の表示領域として使う
- 原典に重要な図がある場合は、出所を明示して引用する
- 原典の図があるのに模倣図を作らない
- 自作図はインライン SVG とし、アスキーアートを使わない
- 黒一色の線画を基本とし、`.mb-figure-frame` に載せる
- ノード数が多い場合は縦方向を優先する
- 矢印が交差する構成を避ける
- 単なる直列手順は番号付きの説明として表現する

## コード

- Highlight.js を必ず読み込み、言語に応じたシンタックスハイライトを適用する
- `pre code` には `language-javascript`、`language-python`、`language-html` などの言語クラスを必ず付ける
- ハイライトしないテキストには `language-plaintext` を付ける
- 独自の色付けでコードを装飾せず、`document.css` の `.hljs-*` 規則を使う
- `pre.mb-diff code` には `nohighlight` を付け、差分専用の色と行頭記号を使う

## 数式

- MathJax 3 を使う
- インライン数式は `$...$`、ディスプレイ数式は `$$...$$` とする
- ベクトルと行列は `\boldsymbol{...}` を使う
- スカラー、添字、集合名は装飾しない
- 名前付きの演算は `\mathtt{...}`、標準 LaTeX コマンドはそのまま使う
- `math-copy.js` により、すべての数式から LaTeX 原文をコピーできるようにする
- ページ側で `window.MathJax` を再定義しない
- 未知のコマンドを別記法へ勝手に置換しない

## 印刷と PDF

印刷対応は `document.css` の `@media print` を使う。
PDF 化はユーザーから明示的に依頼された場合だけ [共通PDF生成CLI](./render-pdf.py) を実行する。Python 3.9以上と、インストール済みの Chrome / Chromium / Edge が必要。Python側に追加パッケージは不要。

以下はワークスペースルートからの実行例。実際の入力HTMLへ置き換える。

Linux・macOS:

```sh
python3 .agents/skills/html/render-pdf.py "docs/input.html"
```

Windows（PowerShellまたはコマンドプロンプト）:

```powershell
py -3 .agents/skills/html/render-pdf.py "docs/input.html"
```

Windowsで `py` がない場合は、Python 3を指す `python` を使う。PowerShellやGit Bashの追加導入は不要。既存の [Bash入口](./render-pdf.sh) も同じPython処理へ引数を渡す。

- ブラウザーはPATHから検出する。Windowsでは `PROGRAMFILES`、`PROGRAMFILES(X86)`、`LOCALAPPDATA` 配下のChrome・Edge・Chromiumも探す。macOSの `/Applications/` も引き続き対応する。
- 標準外の配置やPlaywrightのブラウザーキャッシュを使う場合は、`--browser "<browser-executable>"` で実行ファイルを明示する。スクリプトはブラウザーをダウンロードしない。
- 入力は `.html` または `.htm`。日本語・空白・`#` を含むパスはURIへ変換してブラウザーへ渡す。
- 既定では入力と同じ場所の同名 `.pdf` を新規作成する。`--output "docs/result.pdf"` で変更できる。親ディレクトリは事前に用意する。
- 既存ファイルやシンボリックリンクへの上書きを拒否する。既存PDFを更新したい場合も別名で生成し、置換は承認された別操作として行う。
- 制限時間は既定60秒。必要なら `--timeout 120` のように秒数を指定する。
- 一時的な専用ブラウザープロファイルを使い、普段のログイン情報は再利用しない。サンドボックスを無効化しない。
- Linuxではブラウザー本体に加えて共有ライブラリが必要。起動時に終了コード127となる場合はブラウザー単体を起動して不足を確認し、管理者の承認した方法で実行環境を整える。
- HTML内の外部参照は通信を発生させ得る。機密資料では監査済みのローカル資産だけを使う。このCLIはHTMLを無害化するツールでもネットワーク遮断ツールでもない。

検証コマンド（Windowsでは `python3` を `py -3` に読み替える）:

```sh
python3 -m unittest discover -s .agents/skills/html/tests -v
```

通常は実ブラウザーのテストをスキップする。承認済み環境にPyMuPDFを用意し、環境変数 `SKILL_TEST_BROWSER` にブラウザー実行ファイルを設定すると、実PDF内の文字と描画内容も検証する。
Linuxでは実Chromiumによる検証済み。Windows・macOSは検出処理のテストのみで、実機でのPDF生成は未検証。

## 安全規則と検証

- 保存は対象ワークスペースの依頼範囲内に限定し、同梱資産や既存成果物を無断で上書きしない。
- 外部テキストはエスケープし、引用元のHTMLやスクリプトをそのまま埋め込まない。
- 図表・画像の転載には出典と権利確認が必要。転載できない場合は言葉で説明して原典へリンクする。
- 外部送信、CDN、フォント、PDF処理の依存条件を確認する。認証情報や個人情報を埋め込まず、ブラウザーのサンドボックスを無効化しない。
- デスクトップとモバイルで本文、図、用語欄、コード、数式、コピー操作を確認し、未検証項目を報告する。

## 出典

- 上流: https://github.com/mathbullet/skills
- 固定コミット: `5ab997fcb8a80da4938bacb0a86cbd568e1018a7`
- 上流パス: `plugins/html/skills/html`
- ライセンス: [MIT](./LICENSE)
- ローカル変更: 既存の日本語とデザイン資産を保持。任意Skillの自動取得禁止、CDN・機密資料の注意を追加。PDF出力はLinux・Windows・macOS共通のPython CLIとBash互換入口へ変更し、ブラウザー検出、上書き拒否、タイムアウト、単体・実動作テストを追加。上流更新時はこれらのローカル変更を保持してマージする。
