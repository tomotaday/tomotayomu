# 保存先・画面利用関係の調査メモ

調査日：2026-11-09  
対象リポジトリ：`tomotaday/tomotayomu`  
基準：main ブランチの現行コードを読み取り専用で確認  
目的：新しい作品データ構造への移行中に、既存機能の保存先を誤って切り離さないこと。

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
