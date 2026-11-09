# ともたよむ DB構成表・接続一覧

最終確認日：2026-11-09  
対象：GitHub main / iPhone Braveでの現行運用  
アプリ基準版：v3.8.0【2026/11/09】  
正本：`index.html` と各接続先HTML

> この資料はコード上の接続を整理したもの。ブラウザ内DBの実件数・全keyPathは、読み取り専用のDB診断ページで実機確認する。未確認値を推測で埋めない。

## 1. IndexedDB一覧

| DB名 | version | Object Store | 主キー・構造 | 現在の役割 |
|---|---:|---|---|---|
| `tomotaYomuWorksDB` | 2 | `works` | keyPath `id`。index: `site`, `workId`, `authorId`, `shelfId`（非unique） | 新しい共通作品DB。3,510作品を保持。なろう読書位置の読み書き先 |
| 同上 | 2 | `shelves` | keyPath `shelf_id` | 新しい共通棚マスター。棚名・表示順・登録先指定 |
| `tomotaYomuDB` | 1 | `shelf_names` | keyPath `shelf_id`（移行監査で確認） | 旧棚マスター。現行本体・管理画面の参照が残る |
| 同上 | 1 | `shelf_placement` | keyPath等はDB診断で確認 | 旧作品の棚配置。本体の棚表示・移動が参照 |
| 同上 | 1 | `works_cache` | keyPath等はDB診断で確認 | 旧なろう作品キャッシュ。本体の作品カード構築が参照 |
| 同上 | 1 | `authors` | keyPath等はDB診断で確認 | 作者情報。作者管理・Atom作者一覧等が参照 |
| 同上 | 1 | `reading_position` | keyPath等はDB診断で確認 | 旧読書位置ストア。新DB切替後の本体読書位置処理では参照しない。削除は未実施 |
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

本番DBはversion 2。works 3,510件、shelves 14件を初期移行時に確認。以後の最新件数は実機診断で確認する。

## 2. 接続一覧（画面・処理 → 保存先）

| 画面・処理 | 読み取り先 | 書き込み先 | 状態・注意 |
|---|---|---|---|
| ルート `index.html` の作品カード構築 | 旧DB `shelf_names`, `shelf_placement`, `works_cache`, `authors`。note / カクヨムはlocalStorage | note / カクヨムのしおり・情報を各localStorageへ保存 | 作品全体の新DB一本化は未完了 |
| `index.html` なろう読書位置 | 新DB `works` の `reading` | 新DB `works` の `reading` | 移行項目1。旧localStorage読書キー・旧 `reading_position` は本体の読書処理から切離し済み。旧データは保持 |
| `index.html` 棚移動 | 旧DB `shelf_placement` | 旧DB `shelf_placement` | 新DB `works.shelfId` への本体切替は未実施 |
| `index.html` 作者Atom表示・取込 | 旧DB `authors`、Atom DB `entries` / `meta`、公開JSON | Atom DB `entries` / `meta` | Atom DBは独立保持 |
| `index.html` 履歴 | localStorage `tomotaYomu_v330_reading_history` | 同キー | 3サイト共通。最大30件保存、画面表示最大10件 |
| `index.html` note作品 | localStorage `tomotaYomu_note_magazines_v1` | 同キー | 新DB作品レコードへの本体切替は未実施 |
| `index.html` カクヨム作品 | localStorage `tomotaYomu_kakuyomu_works_v1` | 同キー | 新DB作品レコードへの本体切替は未実施 |
| `app/shelf/shelf_manager.html` | 旧DB `shelf_names`, `shelf_placement`, `works_cache` | 旧DB `shelf_names` 等、localStorageの表示順・登録先設定 | 新DB棚マスターへの切替は未実施 |
| `app/author/author.html` | 旧DB `authors` 等 | 旧DB `authors` | 作者管理の移行は未実施 |
| `app/kakuyomu/kakuyomu_edit.html` | localStorage `tomotaYomu_kakuyomu_works_v1` | 同キー | カクヨム編集画面 |
| `app/memo/tomota_memo.html` | Memo DB `items` | Memo DB `items` | 作品DBとは独立 |
| `register.html` / `kakuyomu_add.html` / `note_magazine_add.html` | 旧DB・各サイトlocalStorage等 | 現行コード上はサイト別保存経路 | 新DBへの登録一本化は未実施。登録処理を変更する際は別途接続確認 |
| `tools/diagnostic/diagnostic_db.html` | 旧DB全ストア | なし | 読み取り専用 |
| `tools/diagnostic/work_db_production_audit.html` 等 | 新DB `works` / `shelves` | なし | 読み取り専用監査・プレビュー用 |
| GitHub Actions | `data/author-list.json` 等 | `data/atom/author-feeds.json`, `data/note-index-*.json`, `data/kakuyomu-toc/*.json` | ワークフローと生成ファイルの接続を維持 |

## 3. localStorageの主要接続

| キー | 用途 | 扱い |
|---|---|---|
| `tomotaYomu_note_magazines_v1` | noteマガジン情報・しおり | 新DB移行待ち |
| `tomotaYomu_kakuyomu_works_v1` | カクヨム作品情報・しおり | 新DB移行待ち |
| `tomotaYomu_v330_reading_history` | 3サイト共通の閲覧履歴 | 現行独立保存。最大30件 |
| `tomotaYomu_atom_display_days` | 作者更新の表示期間 | 表示設定として維持 |
| `tomotaYomu_mixed_shelf_order_v1` | 棚・システム棚の表示順 | 作品データとは別管理 |
| `tomotaYomu_search_excluded_ncodes_v1` | なろう検索除外Nコード | 将来の移行候補。現行独立保存 |
| `tomotaYomu_memo_shelf_label_v1` | ともためも棚の表示名・マーク | 表示設定として維持 |

※上記以外にも旧キー・診断用キーが存在する。削除前に現行コード参照を確認する。

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
4. 棚移動・本棚管理・作者管理は旧DB接続が残る。新DBへ切り替える前に画面単位で読み書き双方を検証する。
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
