# ともたよむ30 記録・次工程引継書

作成日：2026-11-23  
対象：v4.0.0新works正本DBへのなろうAPI生データ3,657件の直接反映、トップ操作列の整理

## 1. 今回の目的と到達点

- なろうAPI再取得データ3,657件を、v4.0.0の新works正本DB tomotaYomuWorksDB version 2 / works へ直接反映する。
- 旧worksは参照せず、旧worksからのコピーも行わない。旧works由来のbookmark・shelfId等は作業開始前に新worksへ移行済み。
- 使用JSON：narou-api-raw-audit-2026-11-22T13-49-54-892Z.json
  - API取得成功：3,657件
  - 通常：1,453件
  - R18：2,204件
  - 対象3,700件のうち未取得：43件
- 取込前検証：新works 3,705件、既存更新3,657件、新規追加0件、検証エラー0件。
- バックアップ取得済み。
- ともたが専用取込ページで一括反映を実行し、「いけた」と完了報告。
- 取込ページは works ストアのみを更新し、shelves とlocalStorageは変更しない設計。単一IndexedDB transactionで書き込み、失敗時は全体を取り消す。
- 詳細な実装・検証結果は [data-migration-log.md](data-migration-log.md) の2026-11-23記録を参照。

## 2. 専用取込ページ

- ファイル：app/transfer/narou_import.html
- URL：https://tomotaday.github.io/tomotayomu/app/transfer/narou_import.html
- 作成commit：fa751bafe3c49b6d75bf83b36a01af95f3315932
- JSONファイルをiPhoneから選択して読み込み、件数・通常/R18内訳・Nコード重複・既存新worksとの照合を行う。
- 検証結果は3,657件全て既存更新、新規追加0、エラー0。
- API由来の最新情報で更新し、既存のshelfId・bookmark・作者かな等を維持する設計。
- novel_type/endの状態判定、通常API userid、日時、keywords・genres、bookmarkとepisodeCountの整合性検査を実装コードで確認済み。

## 3. 実施済みと未確認を分ける

### 実施済み
- API生データJSONをiPhone上で取込ページに読み込み。
- 取込前検証成功（3,657件／通常1,453／R18 2,204／既存更新3,657／新規0／エラー0）。
- 事前バックアップ取得。
- ともた操作で一括反映を実行し、完了報告あり。
- 旧worksは参照・コピーしない方針を維持。

### まだ独立確認が必要
- 書き込み後のworks総件数が3,705件であること。
- API対象3,657件の主要項目が期待どおりに保存されていること。
- 既存shelfId・bookmark・作者かな等が維持されていること。
- shelvesストア・localStorageが変更されていないことの事後確認。
- 作品カードに最新の作品名・作者・あらすじ・状態・総話数・最新話更新日が反映されていること。
- API未取得43件と非対象のカクヨム・note作品が保持されていること。

## 4. トップページ操作列

ともたの依頼により、index.html のトップ操作列を従来の4操作に整理する。

1. 🔄 本棚更新
2. ① JSONコピー
3. ② Atom更新
4. 🔃 順序反転

API応答診断、R18 API応答診断、最新話更新日取得、更新日データ診断、R18判定診断の実験・診断ボタンはトップ操作列から外す。診断処理のコードを削除することとは区別する。

## 5. 安全境界・次の作業

- 本番IndexedDBを壊さない。検証のために追加書き込みを行わない。
- localStorage、shelves、GitHub Actions、Shortcut連携は勝手に変更しない。
- 旧worksは参照・コピーしない。
- まず読み取り専用の事後監査で、件数・管理情報・API更新項目を確認する。
- 事後監査後にiPhoneで作品カード表示を確認する。
- 監査で不一致があれば、対象・差分・復旧方法を明確にし、独断で再取込しない。
