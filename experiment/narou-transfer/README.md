# なろうトランスファー Lab

各サイトの作品データを、ともたよむの共通 `works` 形式へ受け渡すための独立実験環境。

## 現在の構成

- 実験ページ：`narou_transfer_lab.html`
- LabDB：`tomotaYomuNarouTranslatorLabDB` version 4
- Object Store：`cleanWorks`（keyPath: `id`）、`labShelves`（keyPath: `id`）
- 旧 `sourceWorks` ストアはversion 4への更新時に削除済み
- 初期データ：利用者が選択する10作品サンプルJSON
- 保存内容：共通works形式の検討・表示用に整理したレコード。元JSONを無加工で保存する設計ではない

## Transferの役割分担

- **Transfer**：各サイトのデータを、ともたよむの共通形式へ受け渡す仕組み全体
- **Translator**：サイト固有データを共通形式へ変換する処理
- **Register**：変換済みデータを本棚へ登録する最終処理

この実験室では取得データの調査・変換設計・受け渡しまでを扱う。本番登録処理は扱わない。

## 共通worksの日付項目

| 項目 | 意味 | 方針 |
|---|---|---|
| `publishedAt` | 初回登録日 | 値がなくても項目枠を保持 |
| `lastPublishedAt` | 最終更新日 | 値がなくても項目枠を保持 |

旧 `updatedAt` は `lastPublishedAt` へ移行し、旧項目名は残さない。APIから値を取得できるかどうかは項目枠の有無とは別に検証する。

## 作品カード

Labのなろう作品カードは、初回登録日（`publishedAt`）と最終更新日（`lastPublishedAt`）を別々に表示する。値がない場合は `—`。項目診断でも両方を確認できる。

## 安全境界

- 本番DB `tomotaYomuWorksDB`、旧DB、その他の本番IndexedDBには接続しない。
- 本番localStorage / sessionStorageを変更しない。
- 本番 `register.html` とINDEXを変更しない。
- Shortcut・GitHub Actionsと連携・変更しない。
- 本番作品カード・本棚・本番データへ書き込まない。
- 実験対象は独立LabDBのみ。
- この段階で本番バックアップ・復元・移行を行わない。

## 現在の到達点

- 独立LabDB version 4と `cleanWorks` を使用。
- 10作品サンプルの取込・項目調査・カード表示機能を実装。
- 日付項目2つ（`publishedAt`、`lastPublishedAt`）の保持・旧 `updatedAt` 移行処理を実装。
- カードに初回登録日・最終更新日の表示欄を実装。
- GitHubコード確認済み。commit：`6a199cfcfb5fca89dcaadf69c738d41b9d8fa54e`
- iPhone実機での更新後DB確認・10作品診断・カード表示は未確認。

## 実機確認手順

1. GitHub Pagesで実験ページを開く。
2. 「保存内容を再読込」を押す。
3. 「現在のworksでカードを表示」を押す。
4. 10作品すべてに初回登録日・最終更新日の2欄が表示されることを確認する。
5. 日付がない作品では `—` と表示されることを確認する。
6. 「10作品の項目を調査」を実行し、`publishedAt` と `lastPublishedAt` の項目パスを確認する。

実機確認前に「実機確認済み」と扱わない。

## 次の工程

1. iPhone実機で上記手順を確認する。
2. 調査結果を資料室の設計記録へ反映する。
3. API取得可能性と各サイトの日時の意味を別途検証する。
4. 共通項目・サイト固有 `siteData`・不採用項目を検討する。
5. 本番導入の可否は別途判断する。
