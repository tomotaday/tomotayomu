# なろうトランスファー Lab

なろう作品の取得データを、ともたよむの共通 `works` 形式へ受け渡すための独立実験環境。

## 現在の構成

- 実験ページ：`narou_transfer_lab.html`
- LabDB：`tomotaYomuNarouTranslatorLabDB` version 1
- Object Store：`sourceWorks`（keyPath: `id`）
- 初期データ：利用者が選択した10作品サンプルJSON
- 保存内容：変換前の元レコード。現段階では変換・正規化しない。

## 現在の到達点

- GitHub Pages上で実験ページを表示
- 10作品サンプルJSONの取り込み
- LabDBへの保存と一覧表示
- iPhone実機で保存作品数10件、DB version 1、Object Store `sourceWorks` を確認

## Transferの役割分担

- **Transfer**：各サイトのデータを、ともたよむの共通形式へ受け渡す仕組み全体
- **Translator**：サイト固有データを共通形式へ変換する処理
- **Register**：変換済みデータを本棚へ登録する最終処理

この実験室では取得データの調査・変換設計・受け渡しまでを扱う。本番登録処理は扱わない。

## 安全境界

- 本番DB `tomotaYomuWorksDB`、旧DB、その他の本番IndexedDBには接続しない。
- 本番localStorage / sessionStorageを変更しない。
- 本番 `register.html` を変更しない。
- Shortcut・GitHub Actionsと連携・変更しない。
- 本番作品カード・本棚・本番データへ書き込まない。
- 選択したサンプルJSONは元レコードのままLabDBへ保存し、変換・正規化しない。
- この段階で本番バックアップ・復元・移行を行わない。

## 使い方

1. GitHub Pagesで実験ページを開く。
2. `tomotayomu-lab-samples-10works.json` をファイル選択する。
3. 「サンプルをLabDBへ取り込む」を押す。
4. 保存作品数と一覧、各レコードのJSONを確認する。

同じサンプルを再度取り込むと、同じ作品IDのレコードを上書きする（追加重複は作らない）。

## 次の工程

1. 10作品それぞれの全フィールドを棚卸しする。
2. フィールドの値・型・意味を整理する。
3. サンプルJSONと、なろうAPIから取得できる項目を区別する。
4. ともたよむ共通 `works` と照合する。
5. 共通項目・サイト固有 `siteData`・不採用項目を検討する。

取得可能性と実データを確認するまでは変換ルールを確定しない。本番登録・本番移行機能は追加しない。
