# ともたよむ DB構成表・接続一覧

最終確認日：2026-11-10  
対象：GitHub main / iPhone Braveでの現行運用  
アプリ基準版：v3.8.0【2026/11/09】  
正本：`index.html` と各接続先HTML

> この資料はコード上の接続を整理したもの。ブラウザ内DBの実件数・全keyPathは、読み取り専用のDB診断ページで実機確認する。未確認値を推測で埋めない。

## 1. IndexedDB一覧

| DB名 | version | Object Store | 主キー・構造 | 現在の役割 |
|---|---:|---|---|---|
| `tomotaYomuWorksDB` | 2 | `works` | keyPath `id`。index: `site`, `workId`, `authorId`, `shelfId`（非unique） | 正本の共通作品DB。2026-11-09時点で3,600作品（なろう3,596 / note2 / カクヨム2） |
| 同上 | 2 | `shelves` | keyPath `shelf_id` | 正本の共通棚マスター。14棚 |
| `tomotaYomuDB` | 1 | `shelf_names` | keyPath `shelf_id`（移行監査で確認） | 旧棚マスター。現行本体・通常管理画面からの参照は切離し済み。診断・保全用に保持 |
| 同上 | 1 | `shelf_placement` | keyPath等はDB診断で確認 | 旧棚配置。現行本体・本棚管理は新DB works.shelfIdを使用。旧データ保持 |
| 同上 | 1 | `works_cache` | keyPath等はDB診断で確認 | 旧なろう作品キャッシュ。現行本体の作品カード構築では参照しない。旧データ保持 |
| 同上 | 1 | `authors` | keyPath等はDB診断で確認 | 旧作者情報。現行作者管理・Atom作者一覧は新DB作品レコードを使用。旧DBストアは保持し、現行画面からは参照しない |
| 同上 | 1 | `reading_position` | keyPath `ncode` | 旧読書位置ストア。新DB切替後の本体読書位置処理では参照しない。旧DB内の作品・棚配置に存在しない孤立レコードが3件（N1351MD:10話、N5420MC:42話、N8546MG:13話）。削除は未実施 |
| `tomotaYomuAtomDB` | 1 | `entries` | keyPath `entryId` | 作者Atom取得結果 |
| 同上 | 1 | `meta` | keyPath `key` | Atom取得の補助メタデータ |
| `tomotaMemoDB` | 1 | `items` | keyPath `id`。index: `parentId`（非unique） | ともためも |
| `tomotaYomu_rebuild` | 診断ページで確認対象 | 実体を診断で確認 | 現行本体の参照は確認できていない | 過去の再構築作業用DB。削除・変更しない |

### 新DB works レコードの共通形

- 主キー：`id`。例：`narou:N1234AB`、`note:note-magazine:...`、`kakuyomu:1177...`。
- 共通識別：`site` / `workId`。
- 共通情報：作品名・作者名・`authorId`・`shelfId`。
- 読書状態：`reading.position` / `reading.isRead`。
- サイト固有しおり：`bookmark`。
- サイト固有情報：`siteData`。
- `reading` と `bookmark` は別用途。読書進捗とサイト上のしおりURL等を混同しない。
- 棚未所属は `shelfId` 空欄。未分類専用の作品棚IDは作らない。

### 新DB shelves レコード

| 項目 | 用途 |
|---|---|
| `shelf_id` | 固定棚ID・主キー |
| `shelf_name` | 表示名 |
| `display_order` | 表示順 |
| `work_add_target` | 新規登録先の指定 |

本番DBはversion 2。works 3,600件、shelves 14件を2026-11-09時点で確認。以後の最新件数は実機診断で確認する。

## 2. 接続一覧（画面・処理 → 保存先）

| 画面・処理 | 読み取り先 | 書き込み先 | 状態・注意 |
|---|---|---|---|
| ルート `index.html` の作品カード構築 | 新DB `works` / `shelves` | 新DB `works`（読書位置・しおり・サイト情報等） | 新DBを正本として読込。note・カクヨムも切替済み |
| `index.html` なろう読書位置 | 新DB `works` の `reading` | 新DB `works` の `reading` | 移行項目1。旧localStorage読書キー・旧 `reading_position` は本体の読書処理から切離し済み。旧データは保持 |
| `index.html` 棚移動 | 新DB `works.shelfId` / `shelves` | 新DB `works.shelfId` | 切替済み |
| `index.html` 作者Atom表示・取込 | 新DB `works`（site=narou）の作者情報、Atom DB `entries` / `meta`、公開JSON | Atom DB `entries` / `meta` | 作者一覧は新DBから生成。Atom DBは独立保持 |
| `index.html` 履歴 | localStorage `tomotaYomu_v330_reading_history` | 同キー | 3サイト共通。最大30件保存、画面表示最大10件 |
| `index.html` note作品 | 新DB `works`（site=note） | 新DB `works` | 切替済み。localStorageは作品本体の正本ではない |
| `index.html` カクヨム作品 | 新DB `works`（site=kakuyomu） | 新DB `works` | 切替済み。localStorageは作品本体の正本ではない |
| `app/shelf/shelf_manager.html` | 新DB `works` / `shelves` | 新DB `works.shelfId` / `shelves` | 切替済み。localStorageは混在棚表示順等のUI設定のみ |
| `app/author/author.html` | 新DB `works` | 新DB `works` の作者フィールド | 新DB単独運用へ切替済み。旧作者localStorage台帳の参照・補完処理は切離し。旧キーは保管 |
| `app/kakuyomu/kakuyomu_edit.html` | 新DB `works`（site=kakuyomu） | 新DB `works` | 切替済み |
| `app/memo/tomota_memo.html` | Memo DB `items` | Memo DB `items` | 作品DBとは独立 |
| `register.html` / `app/register/work_add.html` / `kakuyomu_add.html` / `note_magazine_add.html` | 新DB `shelves` / `works` | 新DB `works` | なろう・カクヨム・noteの登録先は新DB。UIの登録先選択などはlocalStorage設定を利用 |
| `tools/diagnostic/diagnostic_db.html` | 旧DB全ストア | なし | 読み取り専用 |
| `tools/diagnostic/work_db_production_audit.html` 等 | 新DB `works` / `shelves` | なし | 読み取り専用監査・プレビュー用 |
| GitHub Actions | `data/author-list.json` 等 | `data/atom/author-feeds.json`, `data/note-index-*.json`, `data/kakuyomu-toc/*.json` | ワークフローと生成ファイルの接続を維持 |

## 3. localStorageの主要接続

作品本体・棚・しおりの正本は新DB。以下のキーは移行元の残存データ、表示設定、UI状態、一時受け渡しなどであり、用途を確認せず一括削除しない。

| キー | 用途 | 扱い |
|---|---|---|
| `tomotaYomu_note_magazines_v1` | noteマガジン情報・しおり | 移行元の残存データ。現行本体の正本ではない。削除は実機確認後 |
| `tomotaYomu_kakuyomu_works_v1` | カクヨム作品情報・しおり | 新DB移行待ち |
| `tomotaYomu_v330_reading_history` | 3サイト共通の閲覧履歴 | 現行独立保存。最大30件 |
| `tomotaYomu_atom_display_days` | 作者更新の表示期間 | 表示設定として維持 |
| `tomotaYomu_mixed_shelf_order_v1` | 棚・システム棚の表示順 | 作品データとは別管理 |
| `tomotaYomu_search_excluded_ncodes_v1` | なろう検索除外Nコード | 検索除外リストのUI状態として独立保存。作品メタデータは新DB |
| `tomotaYomu_memo_shelf_label_v1` | ともためも棚の表示名・マーク | 表示設定として維持 |

作者管理の旧localStorage台帳（`tomotayomu_v214_works_master`、`tomotaYomu_authors`、`tomotaYomu_author_links`、`tomotaYomu_v215_author_registry`、`tomotaYomu_v215_author_done_ncodes`）は、読取専用診断で新DBへの補完候補0件・既存一致2,104件・不一致0件を確認。作者管理画面からの参照・補完処理は切離し済み。旧キー自体は削除せず保管中。

## 4. GitHub上のJSON・接続先

| ファイル | 生成・利用 |
|---|---|
| `data/author-list.json` | 作者管理・Atom取得対象 |
| `data/atom/author-feeds.json` | `publish-author-atom-feeds.yml` が生成。indexが取得・表示 |
| `data/note-index-*.json` | `note-magazine-index.yml` が生成。indexがnote目次に利用 |
| `data/kakuyomu-toc/*.json` | `kakuyomu-toc.yml` が生成。indexがカクヨム目次に利用 |

## 5. 移行状況と変更時のルール

1. 新DB `tomotaYomuWorksDB` はversion 2。worksとshelvesを保持する。
2. なろう読書位置は新DBへ切替済み。Brave実機で読書位置・短編既読状態・再読込保持を確認する。
3. note / カクヨムの作品本体、しおり、目次はサイト別保存経路が残る。共通作品DBへの切替は今後1項目ずつ実施する。
4. 棚移動・本棚管理・作者管理は新DBへ切替済み。作者管理の旧localStorage台帳参照・補完処理は切離し済み。旧キーは削除せず保管する。旧DBの読書位置には作品・棚配置が存在しない孤立レコード3件が残るため、旧DB本体は引き続き保持する。
5. Atom DB・Memo DB・履歴・表示設定は作品DBと別目的の保存先。安易に統合しない。
6. 旧DB・旧localStorageは、全接続先の移行と実機確認が終わるまで削除しない。
7. DB名・ストア名・keyPath・index・接続画面を変更したら、この資料と `data-store-usage-inventory.md`、`data-migration-log.md` を同じ作業で更新する。
8. 不明なkeyPathや未確認の接続は「未確認」と記載し、推測で埋めない。

## 6. 実機診断の入口

- 旧DB：`tools/diagnostic/diagnostic_db.html`
- 保存領域全体：`tools/diagnostic/storage_inventory.html`
- 新DB作品・棚：`tools/diagnostic/work_db_production_audit.html`
- 新DB作品カード：`tools/diagnostic/work_db_production_card_audit.html`

これらは読み取り専用を基本とし、診断のためにDBを新規作成・更新しない。

## 7. 2026-11-10 追加確認：判定センター・ショートカット連携

### 判定センター

- `tools/diagnostic/ncode_extract.html` は `tomotaYomuWorksDB` v2 の `works` を参照する構造へ変更済み。
- iPhone / Braveで、なろう作品3,596件の抽出成功を確認。形式不正0件、重複Nコード0件。
- 新DB接続への切替は完了。ただしAPI一括・全件判定、Atom取得失敗作者の確認等の独自機能は別途確認対象。

### iPhoneショートカットとの接続（未確認）

| ショートカット／連携 | 呼び出し先・保存先 | 現在の状態 |
|---|---|---|
| なろうの作者登録 | 詳細なURL・受け渡し形式・保存先は未調査 | **実行時にエラー発生。原因未特定。最優先で調査** |
| その他の現役ショートカット | 個別の呼び出し先・保存先は未照合 | 未確認。正常扱いしない |

- ショートカットはiPhone側の実行手順も含めて確認する。GitHub上のページが新DB対応済みであっても、ショートカットから渡すデータ形式や呼び出しURLが一致するとは限らない。
- 各ショートカットについて、呼び出し先URL／ページ、入力データ、保存先DB・Store、GitHub Actions等の後続処理、実機結果を確認してから接続一覧を確定する。
- エラー原因が判明する前に、登録ページ・Shortcut・本番DBを推測で変更しない。

