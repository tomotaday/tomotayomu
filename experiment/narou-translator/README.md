# なろう通訳レジスター Lab

なろう通常作品の取得データを共通 `works` 形式へ変換する仕組みを設計・検証する独立実験環境。

## 現在の段階

- 実験ページ：`narou_translator_lab.html`
- LabDB：`tomotaYomuNarouTranslatorLabDB` version 1
- Object Store：`sourceWorks`（keyPath: `id`）
- 初期データ：利用者が選択した10作品サンプルJSON
- 保存内容：変換前の元レコード。現段階では変換・正規化しない。

## 安全境界

- 本番 `tomotaYomuWorksDB`、旧DB、その他のIndexedDBには接続しない。
- localStorage / sessionStorageを使用しない。
- なろうAPI等の外部通信を行わない。
- Shortcut・GitHub Actionsと連携しない。
- 本番 `register.html` を変更しない。
- 本番作品カード・本番データへ書き込まない。

## 使い方

1. GitHub PagesでこのHTMLを開く。
2. `tomotayomu-lab-samples-10works.json` をファイル選択する。
3. 「サンプルをLabDBへ取り込む」を押す。
4. 保存作品数が10件になり、一覧と各レコードのJSONを確認できることを確認する。

同じサンプルを再度取り込むと、同じ作品IDのレコードを上書きする（追加重複は作らない）。

## 次の工程

1. LabDBへの取り込み・読込のiPhone実機確認
2. 元データの項目一覧・欠損状況の棚卸し
3. 共通 `works` 項目との対応設計
4. 変換処理の実装・検証

変換仕様が決まる前に、本番DB接続・本番移行機能を追加しない。
