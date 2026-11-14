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
| 検索除外作品の既存情報編集 | 対象の `works` レコード | `works` | `app/register/search_excluded_edit.html` |
| あらすじ補完 | 対象の `works` レコード | `works.synopsis` / `siteData.legacyFields` | `app/shelf/synopsis_repair.html` |
| noteマガジン登録 | `shelves`、既存作品確認に `works` | `works` | `note_magazine_add.html` |
| カクヨム登録 | `shelves`、Actions結果・TOC JSON | `works` | `app/kakuyomu/kakuyomu_write.html` |
| カクヨム作品編集 | 対象作品を `works` から取得 | `works` | `app/kakuyomu/kakuyomu_edit.html` |
| 判定センター | 新DB `works`、Atom公開JSON、検索除外リスト | 作品DBへの書き込みなし。進捗・作者確認・作品確認を診断専用localStorageへ保存 | `tools/diagnostic/ncode_extract.html` |

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
| `tools/diagnostic/storage_inventory.html` | IndexedDBの既知DB一覧、全ストア構造・件数、localStorageキー・概算容量 | 診断結果の画面表示、バックアップJSON出力。調査対象DBの内容は読み取り |
| `tools/diagnostic/ncode_extract.html` | 新DB `tomotaYomuWorksDB/works`、Atom公開JSON、検索除外リスト | 作品DBへの書き込みなし。診断進捗・確認記録を専用localStorageへ保存 |

`storage_inventory.html` はDBが存在しない場合に新規作成しないよう、`onupgradeneeded` でupgrade transactionを中止する実装を持つ。診断ページを使う場合も、対象ブラウザ・表示結果・実行操作を確認し、実機データの変更を伴う操作を行わない。

## 5. 補助画面・診断ページの接続

| ファイル | 読み取り | 書き込み・出力 |
|---|---|---|
| `app/register/search_excluded_edit.html` | 新DB `works` の対象なろう作品 | 同レコードの作品名・作者・あらすじ・話数・更新情報等を `works` へ保存 |
| `app/shelf/synopsis_repair.html` | 新DB `works` のなろう作品 | あらすじが空の作品に限り `synopsis` と互換用 `siteData.legacyFields.story` を補完 |
| `app/settings/color_studio.html` | テーマ・カスタム色・文字設定のlocalStorage | 表示設定キーのみ |
| `tools/export/export_ncodes.html` | 新DB `works` | Nコードのテキストファイルを出力。DB書き込みなし |
| `tools/diagnostic/work_db_production_card_audit.html` | 新DB `works` | なし。読み取り専用 |
| `tools/diagnostic/restore_test.html` | 利用者が選択したバックアップJSON | 専用名のテストDB・専用接頭辞のテスト用localStorageキーを作成し、全件照合 |

| `app/register/search_excluded_compare.html` | localStorage `tomotaYomu_search_excluded_ncodes_v1` | なし。取得失敗Nコードと検索除外リストを照合し、結果を画面表示。コピー操作時のみクリップボードへ出力 |
| `tools/diagnostic/bookmark_migration_audit.html` | 新DB `tomotaYomuWorksDB/works`（既存DBの存在・version 2・ストア構造を確認後、readonlyで全件取得）。カクヨム目次JSON・note目次JSON | なし。旧DB・localStorage・他DBには接続しない。作品レコードと目次の照合結果を画面表示 |
| `tools/diagnostic/work_shelf_id_check.html` | 新DB `tomotaYomuWorksDB/works`（既存DBを確認後、readonlyで指定Nコードの1件を取得） | なし。localStorage・他DBには接続しない |
| `tools/diagnostic/ncode_batch_test.html` | localStorage `tomotaYomu_search_excluded_ncodes_v1`（一括判定時のみ読み取り）、小説家になろう通常API・R18 API | なし。API取得結果と検索除外リストを照合して画面表示。IndexedDB・GitHub Actions・Shortcutには接続しない |

## 6. 運用上の原則

1. 作品本体の正本は `tomotaYomuWorksDB/works`、棚マスターは同DBの `shelves`。
2. Atom・ともためも・表示設定・閲覧履歴は、それぞれの用途に応じて独立管理する。
3. 同じ作品に関係する情報でも、作品本体・読書状態・しおり・更新候補・閲覧履歴を一括で統合・削除しない。
4. 旧DB・旧localStorageキーの削除は、全参照経路と保全要否を確認し、別途承認を得てから行う。
5. この資料の更新はコードの読み取り・資料編集に限定し、本番DB・localStorage・Shortcut・GitHub Actionsを変更しない。
6. コード確認とiPhone実機確認を区別し、実機未確認の事項を実機確認済みと記載しない。

## 7. 参照資料

- DB構造・接続先：`database-structure.md`
- 移行の経緯・旧データ照合：`data-migration-log.md`
- リポジトリ内の配置：`repository-structure.md`
- 現在の作業状況：`development-status.md`

## 8. 旧DB参照の追加確認（2026-11-14）

### 現行ファイル・Workflow

- 現行の主要画面13ページと、今回追加で確認した登録ページ5ページでは、旧DB名 `tomotaYomuDB` および旧ストア名を直接指定する参照は確認できなかった。登録ページ5ページの `indexedDB.open(DB_NAME)` は、新DB名を定数から参照する実装である。
- 現行Workflow `.github/workflows/publish-author-atom-feeds.yml` に `"source": "tomotaYomuDB.authors"` という文字列が残る。これは生成する `data/author-list.json` の `source` メタデータであり、Workflowが旧IndexedDBへ接続・読み取りする処理ではない。Workflowは入力JSONまたは保存済み `data/author-list.json` を使ってAtom feedを生成する。
- 現行のカクヨム目次・note目次・作者Atom公開Workflowに、旧DBへの接続処理は確認できなかった。
- 実験用 `experiment/bookmark/` は独立した `tomotaYomuBookmarkLabDB` を使用し、本番DB・旧DB・localStorage・Shortcutを読み書きしない旨がREADMEに記載されている。

### 保管領域 `archive/delete_pending/`

- ここは現行画面からの通常導線ではなく、保管中のファイル群。ただしGitHub Pages上で公開され得るパスであり、ファイルを直接開いて操作する場合は注意する。
- `html/DELETE_author-export.html` は旧DB `tomotaYomuDB` を開き、作者情報を読み出す旧DB参照ページ。
- `html/DELETE_cleanup_manual_test_works.html` は旧DB `works_cache` の対象レコードを削除する操作を含む。
- `html/DELETE_maintenance_cleanup_deleted_works.html` は旧DBの `shelf_placement` / `works_cache` / `authors` / `reading_position` の4ストアを対象に、指定Nコード9件のレコードを削除する操作を含む。対象は N0747JE / N1351MD / N1632IO / N2184HF / N4411DT / N5420MC / N5909FO / N6158JM / N8546MG。
- この9件には、2026-11-14に旧DB退役時の削除対象と決定した N1351MD（10話）/ N5420MC（42話）/ N8546MG（13話）が含まれる。ただし、この保管ページは9件を旧DBの4ストアから一括削除する危険な旧ツールであり、他の6件も対象にする。**実行禁止・再利用禁止**。3件の削除は、旧DB退役時に対象を限定した安全な手順で別途行う。
- `DELETE_cleanup_manual_test_works.html` は旧DB `works_cache` の N0960MX / N7111BG / N9653IJ を削除する操作を含む。実行しない。
- これらは保管中であり、現行アプリの本番導線から利用するものではない。旧DB削除の判断前に、これらの保管ページを実行・再利用しないこと。ファイル自体の削除も、別途一覧提示・承認を経る。
- 今回確認した保管中の他HTML、Pythonスクリプト、Workflowには、旧DB名・旧ストア名・IndexedDB削除処理の直接一致は見つからなかった。ただし、これは確認した文字列による静的検索結果であり、動的生成・外部Shortcut・端末内に保存されたページ等の不存在を保証しない。

### この調査で確定していないこと

- iPhoneのShortcut、Safari/Braveの履歴・ホーム画面登録、端末に残る古いHTML、外部から呼び出すURLが旧DBを参照していないか。
- 旧DB内の孤立 `reading_position` 3件（N1351MD / N5420MC / N8546MG）は、2026-11-14にユーザーが新DBへ移行せず、旧DB退役時に削除する方針を決定済み。現時点では旧DB内に残存し、削除は未実施。
- iPhone実機上の現在のDB一覧・件数・バックアップファイルの保存状態。
- 現行コードの直接参照が見つからないことだけを根拠に、旧DBを削除してよいとは判断しない。

