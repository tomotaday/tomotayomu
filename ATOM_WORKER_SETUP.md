# ともたよむ Atom Worker 公開手順

## 目的
GitHub Pages上のともたよむから、なろう公式Atomを読み込めるようにするための中継Workerを公開します。
Cloudflareの編集画面でコードを組み立て直す必要はありません。GitHubにある `atom_worker.js` の全内容を一度だけ貼り付けます。

## 公開手順（iPadで単発作業）
1. Cloudflareにログインし、Workers & Pagesを開きます。
2. 既存の `tomotayomu-atom-test` を開き、編集画面へ進みます。
3. エディタ内のコードをすべて選択し、GitHubの `atom_worker.js` の全内容に置き換えます。
   - GitHubファイル: https://github.com/tomotaday/tomotayomu/blob/main/atom_worker.js
4. 保存・デプロイします。
5. 公開されたWorkerのベースURL（例: `https://名前.アカウント.workers.dev`）を控えます。末尾に `/feed` は付けません。

## 公開確認
ブラウザで次のようなURLを開きます。作者IDは動作確認済みの実在IDに置き換えてください。

- 通常作者の作品更新: `https://WORKERのベースURL/feed?type=novel&id=通常作者ID`
- R18作者の作品更新: `https://WORKERのベースURL/feed?type=novel&id=x8754cq`
- R18作者の活動報告: `https://WORKERのベースURL/feed?type=activity&id=x8754cq`

取得できた場合、Atom XMLが表示されます。エラーの場合は、画面のHTTP状態やエラー文を記録してください。

## ともたよむ本体への登録
1. ともたよむを再読み込みします。
2. 「作者更新」を開きます。
3. 「Atom取得Worker URL」にベースURLを入力し、「Worker URLを保存」を押します。
4. 「作者更新を確認（次の10人）」を押します。
5. 表示された取得件数・失敗件数を確認します。

通常作者・R18作者とも、登録済み作者を1回最大10人ずつ順番に処理します。作者数が多い場合は複数回の手動確認が必要です。連続した大量アクセスを避けるため、連打はしないでください。

## 注意
- Workerの公開と本体連携は、この手順を実行するまでは未完了です。
- Workerは任意URLを取得せず、なろう公式Atomの2つのエンドポイントだけを使います。
- Atomに活動報告がない作者は空のフィードになる場合があります。
