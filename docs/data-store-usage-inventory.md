# 保存先・画面利用関係（現行コード確認）

調査日：2026-11-14  
対象：GitHub main  
対象アプリ基準版：v3.8.1【2026/11/14】  
確認方法：現行HTML・JavaScriptを読み取り専用で確認。ブラウザ内データの実件数・実機動作は本資料だけでは保証しない。

> この資料は、2026-11-14時点で確認した現行コードの読み書き先をまとめる。移行前の調査値・旧DB時代の経緯は `data-migration-log.md` を参照する。旧データの削除や保存先変更を指示する資料ではない。

## 1. 保存領域の全体像

| 保存領域 | 主な用途 | 現行コードでの扱い |
|---|---|---|
| IndexedDB `tomotaYomuWorksDB` v2 | 3サイト共通の作品・棚マスター | 本棚・登録・編集・作者管理の正本 |
| IndexedDB `tomotaYomuAtomDB` v1 | 作者Atomの取得結果・既読状態 | 作品DBから独立 |
| IndexedDB `tomotaMemoDB` v1 | ともためものフォルダ・テキスト | 作品DBから独立 |
| localStorage | 更新検知、閲覧履歴、表示設定、検索除外、受信待ちURL | 用途ごとに独立管理 |
| sessionStorage | 作者AtomのActions完了待ち状態 | タブ／セッション単位の一時状態 |
| 旧IndexedDB `tomotaYomuDB`、再構築用DB等 | 移行前データ・調査対象 | 現行通常画面の正本として使用しない。保持・削除判断は別途 |

## 2. IndexedDBの読み書き

### 2-1. 共通作品DB

DB：`tomotaYomuWorksDB` version 2

| Object Store | 主キー | 主な役割 |
|---|---|---|
| `works` | `id` | なろう・note・カクヨムの作品レコード。読書状態・しおり・サイト固有情報を含む |
| `shelves` | `shelf_id` | 棚マスター。棚名・表示順・新規登録先設定等 |

主な画面・処理：

| 画面・機能 | 読み取り | 書き込み | 確認したファイル |
|---|---|---|---|
| 本棚・作品カード | `works` / `shelves` | `works`（読書状態・しおり等） | `index.html` |
| note・カクヨム作品データ | `works` | `works` | `index.html` |
| 本棚管理 | `works` / `shelves` | `works.shelfId` / `shelves` | `app/shelf/shelf_manager.html` |
| 作者管理 | `works` | `works` の作者関連フィールド | `app/author/author.html` |
| なろう登録 | `shelves`、既存作品確認に `works` | `works` | `register.html` |
| 手動登録・検索除外作品管理 | `works` / `shelves` | `works` | `app/register/work_add.html` |
| noteマガジン登録 | `shelves`、既存作品確認に `works` | `works` | `note_magazine_add.html` |
| カクヨム登録 | `shelves`、Actions結果・TOC JSON | `works` | `app/kakuyomu/kakuyomu_write.html` |
| カクヨム作品編集 | 対象作品を `works` から取得 | `works` | `app/kakuyomu/kakuyomu_edit.html` |
| 判定センター | `works` | 作品抽出処理内で必要な保存のみ | `tools/diagnostic/ncode_extract.html` |

作品IDの形式例：`narou:N...`、`note:...`、`kakuyomu:...`。サイト共通の項目は共通フィールド、サイト固有の情報は `siteData`、読書状態は `reading`、しおりは `bookmark` に分けて保持する。

### 2-2. 作者Atom DB

DB：`tomotaYomuAtomDB` version 1

| Object Store | 主キー | 用途 |
|---|---|---|
| `entries` | `entryId` | 作者Atom項目。既読状態を含む |
| `meta` | `key` | 公開データ取得時刻等 |

- 作者一覧の元データは新DB `works` のなろう作品から組み立てる。
- 公開JSON `data/atom/author-feeds.json` を取得し、Atom項目を `entries` に保存する。
- 直近7日分を表示対象とし、取得時に期間外項目を整理する処理がある。
- 作者Atom DBは作品本文・しおり・本棚の保存先ではない。
- 主な実装：ルート `index.html`。

### 2-3. ともためもDB

DB：`tomotaMemoDB` version 1  
Object Store：`items`（keyPath `id`、index `parentId`）

- フォルダ／テキスト項目、本文、親子関係、しおり状態等を保存する。
- 追加・編集・移動・削除・しおり操作は明示操作で `items` を読み書きする。
- 作品DBとは独立。
- 実装：`app/memo/tomota_memo.html`。

## 3. localStorage・sessionStorage

### 3-1. ルート本体で確認したlocalStorageキー

| キー | 用途 | 主な操作・備考 |
|---|---|---|
| `tomotaYomu_v211_update_baseline` | 作品ごとの更新基準 | 初回同期・更新管理の補助データ |
| `tomotaYomu_v211_reading` | 旧読書位置用の定数名 | 現行 `index.html` ではキー定数の宣言のみ確認。読み書き処理での使用は確認できない。端末内に値が残るかは未確認 |
| `tomotaYomu_v211_last_check` | 更新確認時刻 | 更新管理 |
| `tomotaYomu_v214_global_baseline` | 全体更新確認の基準時刻 | 更新確認期間の起点 |
| `tomotaYomu_v214_update_candidates` | 更新候補 | 更新棚・🆙表示の判定 |
| `tomotaYomu_v214_latest_works` | 最新作品情報 | カード表示を補完する更新取得結果 |
| `tomotaYomu_v330_reading_history` | 3サイト共通の閲覧履歴 | 最大30件保存、画面表示は最大10件 |
| `tomotaYomu_pending_note_bookmark_v1` | 受信したnote記事URLの一時保留 | 登録済み全マガジン目次との一意照合と新DB保存が成功した後に削除 |
| `tomotaYomu_search_excluded_ncodes_v1` | なろう検索除外Nコード | 独立リスト。作品本体は新DB |
| `tomotaYomu_mixed_shelf_order_v1` | 棚・システム棚の表示順 | UI表示設定 |
| `tomotaYomu_memo_shelf_label_v1` | ともためも棚の表示名・マーク | UI表示設定 |
| `tomotaYomu_atom_display_days` | 作者Atom表示期間 | UI表示設定 |
| `tomotaYomu_font_size` | 文字サイズ | UI表示設定 |
| `tomotaYomu_font_family` | フォント | UI表示設定 |
| `tomotaYomu_custom_colors_v1` | カスタム配色 | UI表示設定 |
| `tomotaYomu_theme` | テーマ | UI表示設定 |
| `tomotaYomu_work_edit_overrides_v1` | 旧作品編集表示上書きデータ | 起動時に `index.html` が削除を試みる旧キー。作品本体の保存先ではない |

上表はルート `index.html` で確認したキー。各画面固有のキーやブラウザに残る旧キーを網羅した一覧ではない。ブラウザ内に実在するキーの全件は、対象端末の保存領域診断で確認する。

### 3-2. sessionStorage

| キー | 用途 |
|---|---|
| `tomotaYomu_atom_wait_after` | 作者AtomのActions実行前の取得時刻 |
| `tomotaYomu_atom_wait_started` | 作者AtomのActions起動待ち開始時刻 |

いずれも作者Atomの実行待ちに使う一時状態。作品データの正本ではない。

### 3-3. 移行前キー・旧データ

- `tomotaYomu_note_magazines_v1`、`tomotaYomu_kakuyomu_works_v1` 等は移行前の保存形式として記録されている。
- 現行の作品本体・しおりは新DB `works` を使用する。旧キーが端末に残っているかどうかは、コードだけでは断定しない。
- 旧DB・旧キーは、参照経路・保全要否・復元方法を確定し、別途承認するまで削除しない。

## 4. 診断・保全用ページ

| ファイル | 読み取り対象 | 書き込み |
|---|---|---|
| `tools/diagnostic/storage_inventory.html` | IndexedDBの既知DB一覧、全ストア構造・件数、localStorageキー・概算容量 | 診断結果の画面表示。調査対象DBの内容は読み取り |
| `tools/diagnostic/ncode_extract.html` | 新DB `tomotaYomuWorksDB/works` | 抽出結果の画面表示・必要な診断処理 |

`storage_inventory.html` はDBが存在しない場合に新規作成しないよう、`onupgradeneeded` でupgrade transactionを中止する実装を持つ。診断ページを使う場合も、対象ブラウザ・表示結果・実行操作を確認し、実機データの変更を伴う操作を行わない。

## 5. 運用上の原則

1. 作品本体の正本は `tomotaYomuWorksDB/works`、棚マスターは同DBの `shelves`。
2. Atom・ともためも・表示設定・閲覧履歴は、それぞれの用途に応じて独立管理する。
3. 同じ作品に関係する情報でも、作品本体・読書状態・しおり・更新候補・閲覧履歴を一括で統合・削除しない。
4. 旧DB・旧localStorageキーの削除は、全参照経路と保全要否を確認し、別途承認を得てから行う。
5. この資料の更新はコードの読み取り・資料編集に限定し、本番DB・localStorage・Shortcut・GitHub Actionsを変更しない。
6. コード確認とiPhone実機確認を区別し、実機未確認の事項を実機確認済みと記載しない。

## 6. 参照資料

- DB構造・接続先：`database-structure.md`
- 移行の経緯・旧データ照合：`data-migration-log.md`
- リポジトリ内の配置：`repository-structure.md`
- 現在の作業状況：`development-status.md`
