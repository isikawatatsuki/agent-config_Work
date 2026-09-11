# Artifact Library

HTML・PDF生成物をローカルで一覧・プレビュー・検索・整理するWebアプリ。Python 3.10以上（SQLite 3.34以上のFTS5 trigram対応）、PyMuPDF、現行Chrome/Edge/Firefoxを使用する。LinuxとWindowsで同じPythonコードを実行する。Node.jsは利用時には不要。

## 起動

ワークスペースルートで実行する。初回のみ仮想環境と依存を準備する。既存の `.venv` は別OSへコピーせず作り直す。

Linux:

```bash
python3 -m venv .agents/artifact-explorer/.venv
.agents/artifact-explorer/.venv/bin/python -m pip install -r .agents/artifact-explorer/requirements.txt
.agents/artifact-explorer/.venv/bin/python .agents/artifact-explorer/server.py
```

`ensurepip` がない環境で、既存のpipが `--python` に対応している場合:

```bash
python3 -m venv --without-pip .agents/artifact-explorer/.venv
python3 -m pip --python .agents/artifact-explorer/.venv/bin/python install -r .agents/artifact-explorer/requirements.txt
```

Windows PowerShell:

```powershell
py -3 -m venv .agents/artifact-explorer/.venv
& .agents/artifact-explorer/.venv/Scripts/python.exe -m pip install -r .agents/artifact-explorer/requirements.txt
& .agents/artifact-explorer/.venv/Scripts/python.exe .agents/artifact-explorer/server.py
```

ブラウザーで <http://127.0.0.1:8765> を開く。手動起動を停止するには起動ターミナルで `Ctrl+C`。使用中なら `--port 8767` など空きポートを指定する。OS常駐サービスやOSログイン時の自動起動は設定しない。公開トンネル・LAN公開には対応しない。

### VS Codeを開いたときの自動起動

ワークスペースの [.vscode/tasks.json](../../.vscode/tasks.json) に `Artifact Library: 起動` を登録済み。ワークスペースを開いたときに `launch.py` を実行する。ブラウザーは自動では開かない。

1. 初回は上記の仮想環境と依存を準備する。Linuxでは `python3`、WindowsではPython Launcherの `py -3` がPATHから実行できることが必要。
2. 信頼するワークスペースで、コマンドパレットの `Tasks: Manage Automatic Tasks in Folder`（フォルダーの自動タスクを管理）から自動タスクを許可する。初回通知で許可してもよい。許可はフォルダー内の自動タスク全体に作用するため、タスク内容を確認してから行う。エージェントはこの許可やWorkspace Trustを変更しない。
3. ワークスペースを開き直す。すぐ使う場合は `Tasks: Run Task` → `Artifact Library: 起動` を実行する。
4. <http://127.0.0.1:8765> を開く。Remote/WSLではVS Codeの「ポート」に8765が転送されていることを確認する。自動転送が無効なら手動で8765を転送する。手元側も8765を使用し、公開範囲はlocalhostのままとする。

- **停止**: `Tasks: Terminate Task` → `Artifact Library: 起動`。タスク終了時はサーバープロセスを終了する。ログは専用ターミナルに表示し、ファイルへの永続ログ保存は行わない。
- **起動済みの場合**: 同じアプリ・成果物ルート・状態DBのサーバーなら、そのまま利用してタスクは終了する。この場合、元の起動ターミナルまたは元のVS Codeウィンドウのタスクで停止する。再利用タスクから既存プロセスを停止しない。
- **ポート衝突**: 別アプリ・別保存先・応答しないサーバー・まだ起動途中のプロセスの場合はエラー終了する。自動で別ポートへ切り替えず、既存プロセスも終了しない。状況を確認して再実行する。
- **依存不足**: 専用環境、Pythonバージョン、PyMuPDF、SQLite FTS5を確認し、不足時は案内を表示して終了する。自動インストールは行わない。
- **無効化**: このタスクの `runOptions.runOn` を `"default"` に変更する。他の自動タスクも含めて無効化するなら `Tasks: Manage Automatic Tasks in Folder` で許可を取り消す。

共通ランチャーはLinuxで `python3 .agents/artifact-explorer/launch.py`、Windowsで `py -3 .agents/artifact-explorer/launch.py` として手動実行もできる。ランチャーはサーバーを切り離して常駐させない。VS Code Remoteの切断や再接続によるターミナル保持はVS Code設定に依存するため、ウィンドウを閉じた直後の終了を保証しない。

Remote側でタスクを実行する。WSLの場合はWindowsネイティブの仮想環境ではなくLinuxの仮想環境を使用する。Windowsログイン時のWSL起動は対象外。ポートの属性は [.vscode/settings.json](../../.vscode/settings.json) の8765だけに設定しており、他ポートの転送設定は変更しない。

## 保存規約

既定ルートは `.agents/artifacts/`。Skillの場所は変更しない。保存先の明示指定と既存ファイルの編集依頼を優先し、既存資料を自動移動しない。

```text
.agents/artifacts/
  <topic>/
    <YYYY-MM-DD-slug>/
      index.html
      <slug>.pdf
      assets/
        figure.png
```

同じ成果物のHTML・PDF・画像等を1フォルダーにまとめる。Windowsで使えない記号、予約名、末尾の空白・ピリオド、隠し名を避ける。新規生成時は既存ファイルを上書きしない。HTMLの `<title>` を設定すると一覧のタイトルになる。

既存資料を登録するにはユーザーが必要なものだけ関連資産ごと共通保存先へコピーし、「索引を更新」を押す。新規生成後・外部エディターで変更後も同様。アプリ起動時にも索引を更新する。アップロード機能や自動監視はない。

## 機能

- フォルダー階層、全資料一覧、タイル表示、タイトル索引、HTML/PDF絞り込み、更新順・タイトル順・パス順。
- パス・タイトル・概要・タグ・HTML/PDF本文の検索。複数の語はAND。3文字以上はFTS5 trigram、短語は部分一致。日本語と英字の全角・半角等をNFKC正規化する。
- HTML隔離プレビュー、PDFページ画像と前後ページ切替、個別ダウンロード。
- フォルダー作成、ファイル・フォルダーの移動と名前変更、タイトル・概要・タグ編集。
- 確認付き削除、ごみ箱一覧、元の場所への復元。完全削除・自動消去は行わない。

一覧はフォルダーツリーとファイル一覧の2ペイン。単クリックは選択だけを行い、資料本体は読み込まない。選択後の「開く」、ダブルクリック、ファイル行でのEnterで独立した `/viewer.html?id=...` へ移動する。スマートフォンでは選択後に「開く」を押す。属性編集・移動・名前変更は一覧の操作バーから行う。

閲覧ページは資料と操作バーのみを表示する。「一覧へ戻る」で検索・フォルダー・表示形式・選択・スクロール位置を復元する。同じタブのsessionStorageに一覧状態だけを保存し、タブを閉じると破棄される。閲覧ページからはファイル情報、ダウンロード、PDFの前後ページ切替が利用できる。

フォルダー移動は画像・CSSも含む。個別HTMLだけの移動や名前変更で相対リンクが壊れる可能性がある。リンクは書き換えない。大文字・小文字だけの名前変更も衝突として拒否するため、一旦別名を経由する。

## データと制約

### 削除と復元

- ファイルを選択し、操作バーのごみ箱アイコンから削除する。フォルダーは対象フォルダーを開き、フォルダー削除アイコンから操作する。確認画面で対象パスを確認して「削除」を押す。保存先ルートは削除できない。
- 削除した項目は `.agents/artifacts/.trash/<id>/payload` へ移動し、一覧・検索・通常のファイル配信から除外する。OSのごみ箱ではなく、このアプリ専用のごみ箱。関連するタイトル・概要・タグ・本文索引は同じ場所の `manifest.json` に保存する。
- サイドバーの「ごみ箱」で、対象の復元アイコンを押す。資料本体と削除時に索引化されていた属性を復元する。索引に未登録だった資料や外部編集した資料は、復元後に「索引を更新」を行う。内部の資料IDは変わる場合があるため、古い閲覧URLではなく一覧から開き直す。
- 元の場所に同名項目があれば、大文字・小文字の違いも含めて上書きしない。親フォルダーがない場合は、親を先に復元または作成する。
- フォルダーの削除・復元は画像・CSSなども一緒に扱う。個別ファイルの削除では関連資産は残る。他の資料からのリンクは自動更新しない。
- ごみ箱にもファイルと本文・属性が残るため、**ディスク容量の解放や機密情報の消去にはならない**。バックアップには隠しフォルダー `.trash/` も含める。manifestやpayloadを手動で編集しない。
- 移動とDB更新の通常エラーでは元へ戻すが、電源断・強制終了をまたぐ完全な原子性は保証しない。ごみ箱とは別のバックアップを維持する。外部プロセスから同時に変更せず、別ファイルシステムのマウントを成果物フォルダー内に置かない。

### 索引とバックアップ

索引と編集属性は `.agents/artifact-explorer/.state/index.sqlite` に保存する。バックアップはサーバー停止後に `.agents/artifacts/` と `.state/` の両方を取得する。索引を削除すると手入力の概要・タグ・タイトルを失う。内容索引は再生成できる。外部ツールでの移動は新規ファイルとして認識され、編集属性は継承されないためアプリ内から移動する。

索引化は1ファイル50MBまで、300ページを超えるPDFは本文索引の対象外、本文は最大200万文字。画像だけのPDFのOCR、暗号化PDFの解除は行わない。HTMLはUTF-8前提。抽出できない場合も一覧に注意を表示する。大量ファイルや短語検索では走査・応答に時間がかかる。単一ユーザーのローカル利用が対象であり、大規模共有ストレージ向けではない。

## 安全性

127.0.0.1のみで待ち受け、Host/Origin検証と変更APIのCSRFトークン、パストラバーサル・シンボリックリンクの拒否を行う。外部へのアップロードはしない。HTMLのタイトル・本文は画面へHTMLとして挿入せずテキスト表示する。

HTMLは `sandbox="allow-scripts"` とCSPで隔離し、親画面へのアクセス、外部通信、フォーム送信、埋め込みフレーム等を制限する。CDN、外部フォント、fetch、localStorage依存の資料は完全動作しない。grilling-vizの回答保存も対象。制約を解除しない。必要なら信頼性を確認したファイルを別途開くが、その場合は隔離されない。PDFはブラウザーのPDFスクリプトを動かさず、PyMuPDFでページ画像にする。

OSの同一ユーザーや悪意あるローカルプロセスとの間の認証・サンドボックスではない。信頼できないファイルの解析にはPyMuPDFやブラウザー自体の脆弱性・資源消費リスクが残る。管理権限で起動せず、不審なファイルを取り込まない。別プロセスで同時にファイルを変更しない。共有・インターネット公開には別途設計が必要。

## 検証と依存

```bash
.agents/artifact-explorer/.venv/bin/python -m unittest discover -s .agents/artifact-explorer/tests -v
node --check .agents/artifact-explorer/web/app.js
```

WindowsではPython実行パスを `.venv/Scripts/python.exe` に置き換える。`tests/serve_fixture.py` はポート8766に一時HTML/PDFライブラリを作成するブラウザー検証用サーバー。終了すると一時データを破棄する。

Lucide 0.468.0のブラウザー配布物とISCライセンスを `web/vendor/` に同梱する。更新時のみ `npm ci --ignore-scripts` 後、`node_modules/lucide/dist/umd/lucide.min.js` とLICENSEを再配置する。PyMuPDF 1.28.2はAGPLまたは商用ライセンスの対象。配布・共有サービスへの転用前に適用条件を確認する。

LinuxでAPI/索引/ランチャー計28件のテスト、およびランチャーによる実起動と起動済み再利用を確認。VS Codeタスクの設定は機械検証済みだが、ユーザーの初回許可を伴うfolderOpenイベントは未検証。Windowsのパスと排他的ポート確保は模擬検証で、実機検証は未実施。

削除機能は一時ライブラリでキャンセル、ファイル・フォルダー削除、復元、同名衝突エラーと画像保持をブラウザーのDOMイベントで確認した。390pxで確認ダイアログの横はみ出しなしを寸法検証。今回のスクリーンショット取得では古い画像の返却・タイムアウトがあり、モバイルの画像確認は未完了。実ユーザー資料は削除していない。

実ブラウザーによる日本語検索、属性編集、フォルダー作成・移動、名前変更、再索引、画像表示、PDFページ切替を確認済み。一覧と閲覧の独立配信、選択時にiframeが生成されないこと、一覧条件の復元、デスクトップ/モバイルの表示も確認した。ブラウザー連携の物理入力待機が不安定だったため操作検証はDOMイベントも併用した。