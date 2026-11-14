# ともたよむ DB構成表・接続一覧

最終確認日：2026-11-14  
対象：GitHub main / アプリ基準版 v3.8.1【2026/11/14】  
コード上の正本：ルート `index.html` と各接続先HTML  
画面別の読み書き一覧：`data-store-usage-inventory.md`

> 本資料はコードから確認できるDB構造・接続を記録する。ブラウザ内の実件数・端末ごとの残存DB・localStorage全件は、対象端末で診断しない限り断定しない。コード確認とiPhone実機確認を区別する。

## 1. IndexedDB一覧

| DB名 | version | Object Store | 主キー・index | 用途・状態 |
|---|---:|---|---|---|
| `tomotaYomuWorksDB` | 2 | `works` | keyPath `id`。index `site` / `workId` / `authorId` / `shelfId`（非unique） | なろう・note・カクヨム共通の作品データ正本 |
| 同上 | 2 | `shelves` | keyPath `shelf_id` | 共通棚マスター |
| `tomotaYomuAtomDB` | 1 | `entries` | keyPath `entryId` | 作者Atom取得結果・既読状態 |
| 同上 | 1 | `meta` | keyPath `key` | 作者Atom取得時刻等の補助情報 |
| `tomotaMemoDB` | 1 | `items` | keyPath `id`。index `parentId`（非unique） | ともためも。作品DBとは独立 |
| `tomotaYomuDB` | 1（過去の診断記録） | `shelf_names` / `shelf_placement` / `works_cache` / `authors` / `reading_position` | ストアごとの詳細は過去の実機診断記録を参照 | 移行前の旧DB。現行通常画面の正本として扱わない。保持中 |
| `tomotaYomu_rebuild` | 端末・時点依存 | 診断対象 | 現行アプリからの利用は確認できていない | 過去の再構築作業に関係する可能性があるため、削除判断を保留 |

### 作品レコードの共通形

- 主キー `id` の例：`narou:N1234AB`、`note:...`、`kakuyomu:...`。
- 共通識別：`site` / `workId`。
- 共通情報：`title` / `authorName` / `authorId` / `shelfId` / `url` / `updatedAt` / `synopsis` 等。
- 読書状態：`reading.position` / `reading.isRead`。
- しおり：`bookmark`。読書状態とは別用途。
- サイト固有情報：`siteData`。
- 棚未所属は空の `shelfId`。未分類専用の作品棚IDは作らない。

### 棚レコード

| 項目 | 用途 |
|---|---|
| `shelf_id` | 棚ID・主キー |
| `shelf_name` | 表示名 |
| `display_order` | 表示順 |
| `work_add_target` | 新規登録先の指定 |

登録先として選択するのは通常棚。通常棚の `work_add_target===true` がある場合、その棚IDを新規作品へ設定する。通常棚にチェックがない場合は空の `shelfId` とし、未分類表示へ集約する。これは新規登録時の規則で、既存作品の棚IDを更新時に変更するものではない。

## 2. 現行画面・処理の接続

| 画面・処理 | 読み取り | 書き込み |
|---|---|---|
| `index.html` 本棚・カード | 新DB `works` / `shelves` | 新DB `works`（読書状態・しおり等） |
| なろう読書状態 | 新DB `works.reading` | 新DB `works.reading` |
| note・カクヨム作品 | 新DB `works` | 新DB `works` |
| 棚移動・本棚管理 | 新DB `works` / `shelves` | 新DB `works.shelfId` / `shelves` |
| 作者管理 | 新DB `works` | 新DB `works` の作者関連フィールド |
| なろう登録 | 新DB `shelves` / `works` | 新DB `works` |
| noteマガジン登録 | 新DB `shelves` / `works` | 新DB `works` |
| カクヨム登録・編集 | 新DB `shelves` / `works`、GitHub Actions結果・TOC JSON | 新DB `works` |
| 作者Atom | 新DB `works` のなろう作者情報、公開JSON、Atom DB | Atom DB `entries` / `meta` |
| ともためも | Memo DB `items` | Memo DB `items` |
| 保存領域診断 | 既知DB一覧・各ストア・localStorage | 診断結果の画面表示 |

個々のファイル名・操作別の詳細は `data-store-usage-inventory.md` に集約する。

## 3. localStorage・sessionStorage

### localStorage

| キー | 用途 | 現行の扱い |
|---|---|---|
| `tomotaYomu_v211_update_baseline` | 作品ごとの更新基準 | 更新管理用 |
| `tomotaYomu_v211_reading` | 旧読書位置互換キー | 現行読書状態の正本は新DB。旧キーは保全対象 |
| `tomotaYomu_v211_last_check` | 更新確認時刻 | 更新管理用 |
| `tomotaYomu_v214_global_baseline` | 全体更新確認の基準時刻 | 更新管理用 |
| `tomotaYomu_v214_update_candidates` | 更新候補 | 更新棚・🆙表示の判定 |
| `tomotaYomu_v214_latest_works` | 最新作品情報 | カード表示の補完情報 |
| `tomotaYomu_v330_reading_history` | 3サイト共通の閲覧履歴 | 最大30件保存、最大10件表示 |
| `tomotaYomu_pending_note_bookmark_v1` | 受信したnote記事URL | 一意照合と新DB保存の成功後に削除する一時保留 |
| `tomotaYomu_search_excluded_ncodes_v1` | なろう検索除外Nコード | 作品本体と分離した独立リスト |
| `tomotaYomu_mixed_shelf_order_v1` | 棚・システム棚の表示順 | UI設定 |
| `tomotaYomu_memo_shelf_label_v1` | ともためも棚の表示名・マーク | UI設定 |
| `tomotaYomu_atom_display_days` | 作者Atom表示期間 | UI設定 |
| `tomotaYomu_font_size` / `tomotaYomu_font_family` | 文字サイズ・フォント | UI設定 |
| `tomotaYomu_custom_colors_v1` / `tomotaYomu_theme` | 配色・テーマ | UI設定 |

上表はルート `index.html` で確認した主なキーであり、全ページ・全ブラウザのキーを網羅するものではない。

### sessionStorage

| キー | 用途 |
|---|---|
| `tomotaYomu_atom_wait_after` | 作者AtomのActions実行前の取得時刻 |
| `tomotaYomu_atom_wait_started` | 作者AtomのActions起動待ち開始時刻 |

### 移行前キー

- `tomotaYomu_note_magazines_v1`、`tomotaYomu_kakuyomu_works_v1` 等は移行前の保存形式として過去資料に記録されている。
- 現行の作品本体・しおりは新DB `works` を使用する。
- 旧キーが各端末に残存しているかはコードだけでは断定しない。旧DB・旧キーの削除は別途の参照経路確認・保全判断・承認が必要。

## 4. GitHub上のJSON・外部データ

| パス | 用途・接続 |
|---|---|
| `data/author-list.json` | 作者一覧関連データ |
| `data/atom/author-feeds.json` | 作者Atom公開JSON。ルート本体が取得してAtom DBへ反映 |
| `data/note-index-*.json` | noteマガジン目次。note記事URL照合に利用 |
| `data/kakuyomu-toc/{work_id}.json` | カクヨム作品別目次 |
| `data/kakuyomu-toc-requests/{request_id}.json` / `.toc.json` | カクヨム登録要求ごとの処理結果・一時目次 |

## 5. 旧DB・保全上の注意

- 旧DB `tomotaYomuDB` は現行通常画面の作品・棚・作者の正本ではない。過去の移行監査で旧ストアと新DBの照合を行った記録がある。
- 旧 `reading_position` に、旧作品・棚配置に対応しない孤立レコード3件（N1351MD：10話、N5420MC：42話、N8546MG：13話）が残ると過去の実機調査で確認した。現時点で削除したとは扱わない。
- 旧DB・旧localStorageキー・再構築用DBは、参照経路・保全要否・復元方法が確定し、別途承認されるまで削除・変更しない。
- `tools/diagnostic/storage_inventory.html` は既知DB（Works / 旧DB / Atom / Memo / rebuild）とlocalStorageを調査する。DBが存在しない場合は `onupgradeneeded` でupgrade transactionを中止し、新規DBを作らない実装である。

## 6. 実機確認の位置づけ

- 2026-11-09時点で新DB works 3,600件、shelves 14件（なろう3,596 / note2 / カクヨム2）の確認記録がある。
- 2026-11-10、iPhone Braveで判定センターから新DBのなろう作品3,596件を抽出し、形式不正0・重複Nコード0を確認した記録がある。
- これらは当時の確認値であり、2026-11-14現在の件数を保証しない。最新件数は実機診断で確認する。

## 7. 変更・保全ルール

1. DB名・version・Object Store・keyPath・indexを変更する前に、接続する全画面・Workflow・データ形式を確認する。
2. 作品本体、読書状態、しおり、更新候補、閲覧履歴、Atom、Memo、表示設定を同一視しない。
3. 旧DB・旧localStorageの削除や書き込み停止は、参照経路・保全対象・復元方法を確定してから別途承認を得る。
4. 診断は読み取り専用で行い、本番DB・localStorageを調査目的で初期化・変更しない。
5. コード確認と実機確認を分け、未確認の値を推測で補わない。

## 8. 関連資料

- 画面別の読み書き先：`data-store-usage-inventory.md`
- 移行の経緯・照合結果：`data-migration-log.md`
- ファイル配置：`repository-structure.md`
- 現在の作業状況：`development-status.md`
