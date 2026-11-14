# 保存先・画面利用関係の調査メモ

調査日：2026-11-09  
対象リポジトリ：`tomotaday/tomotayomu`  
基準：main ブランチの現行コードを読み取り専用で確認  
目的：新しい作品データ構造への移行中に、既存機能の保存先を誤って切り離さないこと。

> **注意：このファイルの本文は2026-11-09以前の旧DB構成を含む調査履歴であり、現行仕様として使用しない。** 2026-11-14時点では新DB `tomotaYomuWorksDB` version 2 が作品データの正本。本文の画面別読み書き先は現行mainコードとの再照合が必要で、確認が済むまで旧DBの説明は履歴として扱う。現行の概略と更新履歴は `database-structure.md` および `data-migration-log.md` を参照する。

## 重要な前提

- 「運用管理棚（管理設定用）」というメニュー自体は、個々の作品レコードではない。
- メニューの表示・並び順は `localStorage` の `tomotaYomu_mixed_shelf_order_v1` で管理される。
- メニューから開く各画面は、それぞれ異なる保存先を利用する。
- **運用管理棚の移行・再編は、全データ移行と確認が終わった最後に行う。**
- それまで旧DB `tomotaYomuDB` と既存ストアを維持する。既存の読み書きを止めたり、ストアを削除したりしない。
- この文書は調査記録であり、DB・localStorage・本番コードを変更する指示ではない。

## 確認できた画面と保存先

| 画面・機能 | 読み取り | 書き込み | 作品レコードとの関係 |
|---|---|---|---|
| 管理設定用メニューの表示順 | localStorage: `tomotaYomu_mixed_shelf_order_v1` | 同キー | なし。メニューの並び順 |
| 本棚管理 | `shelf_names`, `shelf_placement`, `works_cache` | `shelf_names`。配置や登録先設定も操作 | あり。棚マスター・作品配置・作品表示を扱う |
| 作者整理 | `authors`、旧localStorage作者関連キー | `authors` | あり。現行はNコードで作品に紐づく作者行を扱う |
| カクヨム作品編集 | localStorage: `tomotaYomu_kakuyomu_works_v1` | 同キー | カクヨム作品データそのもの。なろう旧DBとは別保存 |
| 検索除外作品・新規登録 | `works_cache`, `shelf_names` 等 | `works_cache`, `shelf_placement`, `authors`, `shelf_names`、検索除外NコードのlocalStorage | あり。旧DBへ作品と配置等を登録 |
| DB診断 | `tomotaYomuDB` のストア構造・件数・配置キー | なし | 読み取り専用 |
| 孤立配置データ整理 | `shelf_placement`, `works_cache` | 明示操作時のみ `shelf_placement` | あり。削除対象を作品本体と照合する |

## 現行コードで確認した保存先の詳細

### 本棚管理

`app/shelf/shelf_manager.html`

- DB：`tomotaYomuDB` version 1
- ストア：`shelf_names`, `shelf_placement`, `works_cache`
- 棚ごとの作品数は `shelf_placement` を集計。
- 棚を開いたときの作品表示は、配置Nコードを `works_cache` と照合。
- 棚名・棚設定の変更は `shelf_names` に保存。
- したがって新DBへ移行する場合、本棚管理画面の移行は作品レコード移行とは別の画面対応作業として必要。ただし実施は最後。

### 作者整理

`app/author/author.html`

- DB：`tomotaYomuDB` version 1
- 主なストア：`authors`
- 作者管理名、ふりがな等を `authors` の該当行へ書き戻す。
- 現行の作者行はNコード単位で作品に結びついているため、作者マスターを新設する場合は、作者単位の重複統合と、この画面の読み書き先変更を別途設計する。
- Atom作者一覧との連携もあるため、作者データ移行だけで完了とはしない。

### カクヨム作品編集

`app/kakuyomu/kakuyomu_edit.html`

- localStorage：`tomotaYomu_kakuyomu_works_v1`
- IndexedDBのなろう旧DBとは別管理。
- 共通作品DBへ統合する際には、この編集画面の読み書き先も対応が必要。ただし運用管理棚の移行とは別作業。

### 作品の手動登録

`app/register/work_add.html`

- `works_cache`, `shelf_placement`, `authors`, `shelf_names` を使用。
- 新規作品の保存時に旧DBの複数ストアを同一トランザクションで更新する。
- 新DB導入後も旧DBを維持する期間は、既存登録経路を壊さないこと。二重保存や同期を導入する場合は、書き込み失敗時の整合性を別途設計・検証する。

### 診断・メンテナンス

- `tools/diagnostic/diagnostic_db.html` は `tomotaYomuDB` の読み取り専用診断。
- `tools/maintenance/cleanup_orphan_placements.html` は、明示操作時に `shelf_placement` のみ削除するメンテナンス画面。通常の移行処理に組み込まない。

## 移行時の扱い

1. まず新しい共通作品データ構造を設計し、既存データとの対応表を作る。
2. 作品データを移行・照合する間、旧DBと旧ストアはそのまま残す。
3. 作品表示・登録・しおり・更新処理など、作品を扱う機能を段階的に対応させる。
4. 作者整理、本棚管理、各種メンテナンス画面は、個別に読み書き先を確認してから対応する。
5. 運用管理棚のメニュー構成・表示順の移行は最後。
6. 旧DBを削除・停止する判断は、全画面・全機能の移行と実機確認が完了した後に、別途承認を得て行う。

## 未確認・追加調査が必要な項目

- `tomotaYomuDB` の全ストアの正確な keyPath・index・生成時コード。
- Atom管理・Atom取込・作者JSON出力が `authors` を参照する全箇所。
- あらすじ補完、検索除外変更登録、Nコード出力など、メニュー内の全リンク先の読み書き先。
- note作品の編集・目次・しおりと共通作品レコードの統合方法。
- localStorageの読書位置とIndexedDB `reading_position` の二重保存の扱い。
- `latest_works` と `works_cache` の新旧関係・正本の決定。

調査は読み取り専用で継続する。上記の未確認項目を確認するまでは、旧DBの削除・ストア変更・既存書き込み停止を行わない。


## 2026-11-08 バックアップ実データ照合

対象バックアップ：`tomotayomu-backup-2026-11-08T15-48-44-271Z.json`  
エクスポート時刻：2026-11-08 15:48:44 UTC（日本時間 2026-11-09 00:48:44）  
照合はバックアップファイル内のデータに対して実施。ブラウザ内データ・本番DBへの変更は行っていない。

### 作品・作者

- `works_cache` 3,506件、`shelf_placement` 3,506件。Nコードの集合は完全一致し、欠落・余剰は0件。
- `authors` は2,410行。全行が作品Nコードに対応し、作者ID欠損は0件。
- 作者行の2,410件を `authorType + authorId` でまとめると776グループ（normal 122、r18 654）。
- 今回のデータでは、同じauthorIdがnormal/r18をまたぐ例は0件。
- 1,096作品には作者行がなく、作品側の `userid` もすべて0。新構造ではauthorId不明を許容する必要がある。
- 同一作者グループ内でwriter表記に差があるものが12グループ、authorName表記に差があるものが1グループ。代表名の決定規則は未決定。
- 現行AtomキーがauthorTypeを含むため、Narou作者マスターの識別子は `site + authorType + authorId` を暫定候補とし、確定前にコード側の利用箇所を再確認する。

### しおり・読書位置

- localStorage `tomotaYomu_v211_reading` は3,515キー。うち未読nullが3,101件、数値の読書位置が414件。
- IndexedDB `reading_position` は414件で、localStorageの数値414件と全件一致。
- 読書位置があるが作品本体が見つからないNコードが3件（N1351MD=10、N5420MC=42、N8546MG=13）。削除せず保留。
- localStorageにのみ存在する残り6キーはすべてnull。未読状態の記録とみられるが、移行時の扱いは未決定。
- どちらか一方を正本と決めたり、片方を削除したりしない。保存・復元テスト後に判断する。

### 更新管理

- localStorage `tomotaYomu_v214_latest_works` は79件で、すべて `works_cache` に存在。
- 79件中74件は `works_cache` と話数・更新日時・タイトル・完結状態のいずれかに差がある。最新情報を保持するケースがあるため、単純に古い作品本体で上書きしない。
- `tomotaYomu_v214_update_candidates` は33件で、全件が `latest_works` と `works_cache` の双方に存在。更新候補という独立した意味を持つため、作品本体への単純統合はしない。

### 再構築データ

- localStorage `tomotaYomu_v214_works_master` は2,104作品。2026-10-03作成の `rebuild-20261003` 版。
- 2,104作品すべてが現在の `works_cache` に含まれ、現在の本棚にのみ存在する作品は1,402件。
- IndexedDB `tomotaYomu_rebuild` の3レコードは、API再構築の第1便1,052件、第2便1,052件、統合版2,104件。
- これらが現在の画面・処理から参照されているかは未確認。歴史的な作業データと推定するが、削除・停止しない。

### この照合で確定していないこと

- 作者名の代表値と、作者マスターの最終キー設計。
- 3件の孤立読書位置の由来・復旧要否。
- `latest_works` の更新・参照・書き戻しの全経路と正本ルール。
- `update_candidates` の保持期間・消去条件。
- `tomotaYomu_rebuild` および再構築localStorageキーの現行参照箇所。

以上はバックアップ時点の観測結果。実データの削除、DBスキーマ変更、既存書き込み停止は一切行っていない。


## 2026-11-09 現行コードの参照経路追加確認

対象：main `index.html`（取得時SHA `b8534fc60183f7ff91a46df7ba7962cd9969be35`）。コードは読み取り専用で確認。

### latest_works

- `getLatestWorks()` / `saveLatestWorks()` がlocalStorageの `tomotaYomu_v214_latest_works` を読み書きする。
- 起動時はIndexedDBから作品カードを構築した後、`restoreLatestWorks()` が該当Nコードのカードへ最新情報を反映する。
- 更新確認 `updateInfo()` はAPIから取得した更新作品を `slimWork()` で整形し、`latest_works` に保存してカードへ反映する。
- バックアップの79件はすべて `works_cache` に存在。比較した全項目のうち少なくとも1項目が異なる作品は79件。うち74件は `general_lastup` と `general_all_no` の両方に差がある。
- よって `latest_works` は単純な重複控えではなく、作品カード表示の上書きデータとして現行利用中。新DB移行時に無視・削除・旧データによる上書きをしない。

### update_candidates

- `getUpdateCandidates()` / `saveUpdateCandidates()` がlocalStorageの `tomotaYomu_v214_update_candidates` を読み書きする。
- `updateInfo()` が更新作品のうち棚登録済み作品を候補として登録し、未登録扱いの作品は候補から外す。
- `applyCardState()` と `buildUpdateView()` が候補情報を使って🆙表示・更新棚表示を判定する。
- バックアップの33件はすべて `works_cache` と `latest_works` に存在し、33件すべてがNコード単位で一致。
- 候補値は更新日時文字列。作品本体とは別の「更新確認状態」として保持する必要がある。

### 候補作品の再取得関数

- `hydrateCandidateWorks()` は定義されており、候補NコードをAPIで再取得して `latest_works` を更新する処理を持つ。
- main `index.html` 全体の呼び出し箇所を確認した範囲では、関数定義以外に呼び出しが見つからなかった。現行の通常起動・更新確認経路で実行されているとは判断しない。
- 未使用関数か、別経路から呼ぶ想定の残存関数かは追加確認事項。現段階で削除しない。

### 読書位置の実際の優先順位

- `buildV3CardsFromIndexedDB()` はIndexedDBの `reading_position` を読み、localStorageの `tomotaYomu_v211_reading` にある読書位置マップへ反映して保存する。
- したがって、起動時の読書位置復元ではIndexedDB側の数値がlocalStorage側を上書きする。
- `setReading()` はlocalStorageへ保存した後、`saveReadingToIndexedDB()` でIndexedDBにも保存する。
- これは二重保存であり、現在の実装ではIndexedDBが復元時の優先元。ただし書き込みは非同期で別処理のため、片方の失敗時に不整合となる可能性は残る。
- 移行ではこの挙動を再現・検証し、片方の保存先を早期に廃止しない。

### 修正・補足

- 前節のバックアップ照合について、`latest_works` 79件はすべて何らかの比較対象項目に差があり、そのうち74件は更新日時と話数にも差がある、という意味である。全79件が更新日時・話数とも異なるという意味ではない。
- この追記も調査記録のみ。本番コード・DB・localStorageの変更は行っていない。


### 再構築DB・旧作品マスターの参照確認

- main `index.html` には `tomotaYomu_rebuild` の参照は見つからなかった。
- GitHubコード検索でも、同じDB名を使用するコードは確認できなかった。ただし検索対象・インデックスの限界があるため、全リポジトリで絶対に未使用とは断定しない。
- `app/author/author.html` には旧作品マスターを読む処理が残っている。
- ただし画面側のキー定数は `tomotayomu_v214_works_master`（小文字の `y`）で、バックアップに存在するキー `tomotaYomu_v214_works_master`（大文字の `Y`）とは大文字・小文字が異なる。localStorageでは別キーとして扱われるため、今回のバックアップの旧作品マスターはこの処理から読み込めない可能性が高い。
- これは既存コードとバックアップの不一致として記録する。原因・影響範囲を確認するまで修正しない。データも削除しない。


### 更新基準・履歴・検索除外の独立データ

バックアップの値とmain `index.html` の参照経路を追加確認。

- `tomotaYomu_v214_global_baseline` と `tomotaYomu_v211_last_check` は、バックアップ時点で同じ時刻（`2026-11-07T22:01:21.437Z`）。現行の更新確認 `updateInfo()` は global baseline を検索期間の起点にし、完了時に両方を更新する。
- `tomotaYomu_v211_update_baseline` は2,104件。現行コードには初回同期用 `initializeBaseline()` があり、このキーへNコード別の最終更新日時を保存する。ただしmain `index.html` 内で関数呼び出しは確認できず、現在の通常経路で更新されるとは判断しない。削除しない。
- `tomotaYomu_v330_reading_history` は30件。作品クリック時にNコードと閲覧時刻を記録し、直近30件を履歴棚に表示する。作品のしおりとは異なる横断イベント履歴として独立保持する。
- `tomotaYomu_search_excluded_ncodes_v1` は33件。現行コードが検索除外判定・ボタン表示・登録操作に使用する。作品に関する属性だが、現在は独立localStorage配列として保存されているため、将来の作品レコード移行対象候補。
- `tomotaYomu_mixed_shelf_order_v1` は管理メニュー表示順であり、作品固有データとは別。運用管理棚自体の移行は最後という方針を維持する。

この段階では上記キーの削除・書き換え・統合を行わない。


---

## 2026-11-09 v3.8.0 現行接続の追記（旧記述の更新）

以下はv3.8.0のmainコードを再確認した現行状態。上記のバックアップ照合・過去調査時点の説明より、この節を優先する。

### 新しい共通作品DB

- DB：`tomotaYomuWorksDB` version 2
- `works`：keyPath `id`。index `site` / `workId` / `authorId` / `shelfId`。
- `shelves`：keyPath `shelf_id`。項目は `shelf_id` / `shelf_name` / `display_order` / `work_add_target`。
- 初期移行時の確認件数：works 3,510件、shelves 14件。
- 共通作品レコードは `id` / `site` / `workId` / `shelfId` / `reading` / `bookmark` / `siteData` 等を保持する。サイト固有情報は `siteData` に分け、読書進捗 `reading` とサイト固有しおり `bookmark` を混同しない。

### v3.8.0で新DBへ切り替えた機能

- なろう読書位置・短編既読状態：`works` の `reading.position` / `reading.isRead` を読み書きする。
- 旧localStorage読書位置キーと旧DB `reading_position` は、本体の読書位置処理から切り離した。旧データ自体は削除していない。
- note・カクヨムの作品情報やしおりは、現時点では引き続き各サイトのlocalStorageを利用する。
- 棚マスターは新DBへ14件コピー済みだが、現行indexの本棚表示・棚移動は旧DB `tomotaYomuDB` の `shelf_names` / `shelf_placement` 等を参照している。新DB棚マスターへの本体切替は未実施。
- 新DB `works.shelfId` への棚移動書き込みも未実施。旧DB側の棚配置を使用する。

### 履歴

- キー：`tomotaYomu_v330_reading_history`
- なろう・note・カクヨムの3サイト共通で記録。
- 最大30件を保存し、画面には直近10件を表示。
- 同じ作品を再度開くと履歴の先頭へ移動する。
- 作品の読書位置・サイトしおりとは別の閲覧イベント記録。

### 現行画面との接続

| 画面・処理 | 現行接続 |
|---|---|
| `index.html` 作品カード構築 | 旧DB `tomotaYomuDB` の `shelf_names` / `shelf_placement` / `works_cache` / `authors` |
| `index.html` なろう読書状態 | 新DB `tomotaYomuWorksDB/works` |
| `index.html` note作品 | localStorage `tomotaYomu_note_magazines_v1` |
| `index.html` カクヨム作品 | localStorage `tomotaYomu_kakuyomu_works_v1` |
| `index.html` 履歴 | localStorage `tomotaYomu_v330_reading_history` |
| 作者Atom | 旧DB `authors` + 独立DB `tomotaYomuAtomDB`（`entries` / `meta`） |
| ともためも | 独立DB `tomotaMemoDB/items` |
| 本棚管理 | 旧DB `shelf_names` / `shelf_placement` / `works_cache` |

詳細なDB構造・画面別接続先は `database-structure.html` を参照する。

### 変更時の必須確認

1. 変更する画面・機能の読み取り先と書き込み先を両方確認する。
2. DB名・version・store・keyPath・indexを変更するときは、移行前後の件数・重複・再読込を照合する。
3. 作品本体、棚マスター、棚配置、作者、しおり、履歴は同じ「作品関連」でも保存先・役割が異なる。まとめて切り替えない。
4. 1機能ずつ新DBへ切り替え、Brave実機で表示・保存・再読み込みを確認する。
5. 全機能の切替完了までは旧DB・旧localStorageを削除しない。


---

## 2026-11-10 現行接続の再監査（旧記述より本節を優先）

本節は、2026-11-10時点の現行コードを確認した結果。上記の過去時点の棚卸し・移行前記録は履歴として残し、現行接続の判断には本節を優先する。

- `index.html` の本棚・作品カード・棚移動・読書位置・Atom作者一覧は、新DB `tomotaYomuWorksDB` を正本として使用。Atom取得結果は独立した `tomotaYomuAtomDB` に保持。
- 作者管理 `app/author/author.html` は新DB `works` のみを読み書きする。旧作者localStorage台帳の参照・補完処理は現行ファイルから切離し済み。旧キーはブラウザ内に残存している可能性があるため、削除せず保管。
- 本棚管理 `app/shelf/shelf_manager.html`、なろう・note・カクヨムの登録・編集ページは新DB `works` / `shelves` を使用。localStorageに残る登録先・表示順・色・文字設定等はUI設定であり、作品・棚データの正本ではない。
- 旧DB `tomotaYomuDB` を参照する現行ページは、診断・保全目的の `tools/diagnostic/diagnostic_db.html`、`tools/diagnostic/old_db_migration_audit.html`、保存領域一覧の `tools/diagnostic/storage_inventory.html`、および明示操作型メンテナンス `tools/maintenance/cleanup_orphan_placements.html`。通常の本棚・登録・作者管理処理からは参照しない。
- `tools/maintenance/cleanup_orphan_placements.html` は旧 `shelf_placement` を削除する機能を持つ。現時点では実行しない。診断ページも旧DBを削除しない。
- 旧DBの読み取り専用照合（2026-11-10実機結果）：`works_cache` 3,596件すべて新DBに存在、`shelf_placement` 3,596件すべて新DBの作品・棚IDと一致、`authors` 2,412件すべて作者ID一致、`shelf_names` 14件すべて新DB棚ID一致。
- 旧 `reading_position` は414件。411件は新DBに対応。残る3件（N1351MD episode 10、N5420MC episode 42、N8546MG episode 13）は旧 `works_cache` と旧 `shelf_placement` の双方に存在しない孤立読書位置。新DBへの作品追加対象とはしない。旧DB内の3レコードは保全のため残す。
- したがって、旧DBは現行アプリの通常処理から切離し済みだが、診断・保全・孤立読書位置の記録として保管中。旧DB削除は未実施・未承認。

## 2026-11-10 追加：Shortcut連携の確認待ち

新DB移行後のiPhoneショートカット整合性は、画面・DBの接続確認とは別に確認する必要がある。

| Shortcut | 呼び出し先 | 保存先 | 状態 |
|---|---|---|---|
| なろうの作者登録 | 未調査 | 未調査 | 実行時エラーあり。原因・影響範囲は未特定 |
| その他の現役Shortcut | 未調査 | 未調査 | 未確認 |

確認項目：
1. Shortcutが開くURL・HTMLページと、URLパラメータの内容。
2. クリップボード・共有シート等で受け渡すデータの形式。
3. 登録処理が実際に書き込むDB・Object Store・localStorage。
4. GitHub Actions、Atom更新、JSON公開等の後続処理。
5. 成功時の登録件数・更新内容と、失敗時のエラー表示。

なろうの作者登録エラーを最優先で再現・切り分けし、その後ほかの現役Shortcutも一つずつ確認する。確認前にShortcutや本番登録処理を推測で変更しない。未確認のShortcutは正常と記載しない。



---

## 2026-11-14 現行接続への追記（旧調査結果との優先関係）

この文書の前半は新DB移行前の調査メモであり、現行の保存先を示す正本としては使用しない。旧DB時代の経緯として保持する。以下は2026-11-14時点のmainコードで確認した現行接続を示す。

### 現行作品データの正本

- 共通作品レコード：IndexedDB `tomotaYomuWorksDB` version 2 / `works`。
- 棚マスター：同DB / `shelves`。
- なろう・note・カクヨムの作品本体は新DBへ保存する。
- カクヨム作品編集は `app/kakuyomu/kakuyomu_edit.html` が新DBの `works` を読み書きする。
- カクヨム登録は `app/kakuyomu/kakuyomu_write.html` がGitHub Actions結果を受け取り、利用者の明示操作後に新DB `works` へ追加する。
- 旧DB `tomotaYomuDB` と旧localStorage作品キーは移行履歴・保全対象として残す。残存データを現行本体の正本と誤認しない。削除は別途承認が必要。

### 管理設定棚・資料室リンクの役割

管理設定棚は作品データの保存先ではなく、管理画面・診断・GitHub Actions・資料室への入口である。メニューの表示順等のUI設定は作品データと分離する。各リンク先の保存先はリンク元メニューから推測せず、リンク先ページの実装で判断する。

2026-11-14時点の資料室リンクは、開発状況インデックス、なろう・note・カクヨム各ガイド、判定センター、バックアップ・復元、リポジトリ構成、DB構成等を案内する。カクヨム技術記録も資料室から参照できるよう追加する。

### 2026-11-14にコード確認した接続

| 画面・機能 | 読み取り | 書き込み | 注意 |
|---|---|---|---|
| カクヨム登録 | 新DB `shelves`、Actions結果・TOC JSON | 新DB `works` | UUIDでActions結果と照合 |
| カクヨム作品編集 | 新DB `works` | 新DB `works` | `kakuyomu:{work_id}` を対象 |
| カクヨム作品カード | 新DB `works`、GitHubの作品別TOC | 新DBの読書・しおり情報 | TOCで話数を照合 |
| note・なろう作品 | 新DB `works` | 新DB `works` | サイト固有フィールドは `siteData` 等に保持 |
| 本棚管理 | 新DB `works` / `shelves` | 新DB `works.shelfId` / `shelves` | 旧DB棚ストアは現行本棚の正本ではない |
| 作者管理 | 新DB `works` | 新DB `works` | 旧作者localStorage台帳は現行参照経路から切離し済み |
| ともためも | `tomotaMemoDB/items` | 同ストア | 作品DBとは独立 |
| 作者Atom | `tomotaYomuAtomDB` と公開JSON | Atom DB | 作品データとは別管理 |

### 継続調査・保全

- DB構造の詳細・localStorage主要キーは `database-structure.md` を参照。
- 移行の時系列・バックアップ照合・旧DBの孤立読書位置は `data-migration-log.md` を参照。
- 旧DB・旧localStorageの削除は、保存先の全参照経路・保全対象・復元テストの確定後に判断する。
- 本資料の更新は、ブラウザ内のDB・localStorageを変更しない。


## 2026-11-14 追加：カクヨム登録専用Shortcutの画面確認

利用者提供のiPhoneスクリーンショットで、カクヨム登録専用Shortcut「とよむ←カクヨム作品登録」の主要なアクションとGitHub Actionsへの入力対応を確認した。名称はショートカット一覧の表示枠に収めるため、「ともたよむ」ではなく短い「とよむ」を使用する。従来の「Shortcut連携の確認待ち」表は当時の未調査記録として保持し、カクヨム登録専用Shortcutについては本節の確認内容を優先する。

- 共有シートからURLを受け取り、変数 `work_url` にショートカット入力を設定。
- キーチェーンの `GitHub_PAT` を取得して `token` に設定。値がない場合はトークン入力を要求し、入力値を `token` に設定して `GitHub_PAT` として保存。
- `Generate UUID` でUUIDを生成。
- GitHub APIの `/repos/tomotaday/tomotayomu/actions/workflows/kakuyomu-toc.yml/dispatches` へPOST。画面で確認できた設定はPOST、Authorization（Bearer＋変数 `token`）、Accept（`application/vnd.github+json`）、X-GitHub-Api-Version（`2022-11-28`）、`ref=main`、本文JSON。
- `inputs` は2項目：`work_url` ← 変数 `work_url`、`request_id` ← 生成UUID。
- 登録ページURLに `request_id` を付けて開く。

HTTPリクエストのヘッダ詳細、画面に写っていないアクション・設定は未確認。PATの実値は記録しない。利用者向け手順と再構築時の注意は docs/kakuyomu-toc-registration-investigation.md を正本とする。今回の記録追加はShortcut本体・GitHub Actions・DB・localStorageを変更しない。
