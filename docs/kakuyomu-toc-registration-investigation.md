# カクヨム登録・目次取得 技術記録

最終更新：2026-11-14  
対象リポジトリ：tomotaday/tomotayomu  
対象ブランチ：main  
対象機能：専用Shortcut → GitHub Actions → 登録ページ → 新DB  
位置づけ：現行実装の技術的な接続・検証記録。利用者向け手順は `docs/guides/kakuyomu_guide.html` を参照。

> 本書は2026-11-14時点のコードと実機確認を反映する。過去の設計案・旧実装は履歴として区別し、現行仕様として扱わない。実機未確認の項目は完了扱いしない。

## 1. 現行フロー

1. カクヨム登録専用ShortcutがUUID形式の `request_id` を生成する。
2. Shortcutが作品URL・request_idをGitHub Actions `kakuyomu-toc.yml` へ送る。
3. ShortcutがGitHub Pagesの登録ページを開く。

```text
https://tomotaday.github.io/tomotayomu/app/kakuyomu/kakuyomu_write.html?request_id={UUID}
```

4. Workflowがカクヨム作品情報と作品別目次を取得・検証する。
5. Workflowがrequest_idに対応する結果JSON・TOC JSONを公開する。
6. 登録ページは結果JSONを5秒間隔でポーリングし、最大60回（約5分）待つ。
7. 成功結果を受け取ると、request_id一致・TOC JSONの存在・作品ID・公表話数・抽出件数・連番・重複ID等を検証し、作品情報を画面へ表示する。
8. 利用者が内容・登録先を確認し、明示的に登録操作を行う。
9. 登録ページは新DBへ作品レコードを追加する。

ポーリング表示の `1/60` は確認回数であり、作品話数やWorkflowの処理段階数ではない。1回ごとに5秒待つ。成功・失敗の終端状態を受け取ればループを抜ける。

## 2. Workflow

対象：`.github/workflows/kakuyomu-toc.yml`

- トリガー：`workflow_dispatch`
- 入力：作品URLまたは作品ID、request_id
- request_id：UUID形式を検証し、結果ファイル名・実行グループの対応キーとして利用。
- 作品URL：カクヨムの `/works/{作品ID}` 形式を検証。
- 作品データ：カクヨムページの埋め込みデータを解析し、作品情報・目次を取得。
- 目次：`EmptyEpisode` と重複IDを除外し、順番付きepisodesを構成。
- 検証：公表総話数と抽出件数が一致しなければ失敗。episode番号の連番とIDの重複も登録ページ側で再検証。
- 作品メタデータ：title、author、author_handle、synopsis、tags、status、character_count、updated_at、published_at等を `work_metadata` として出力。
- 作者ハンドル：作者オブジェクトの `name` を採用。画面・DBでは `@` を付けずに保存する。
- 保存先：
  - `data/kakuyomu-toc-requests/{request_id}.json`：実行結果・作品メタデータ
  - `data/kakuyomu-toc-requests/{request_id}.toc.json`：登録要求ごとのTOC
  - `data/kakuyomu-toc/{work_id}.json`：本棚で参照する作品別TOC
- 成功・失敗の結果JSONを公開し、登録ページがポーリングで取得する。

## 3. 登録ページ

対象：`app/kakuyomu/kakuyomu_write.html`

- request_idをURLクエリから取得し、UUID形式を検証。
- GitHub上のrequest結果JSONを5秒間隔・最大60回確認する。
- 結果のrequest_id一致を確認。
- TOC JSONを取得し、作品ID・件数・episode番号・episode_idの重複を検証。
- Workflowが出力した `work_metadata` を画面へ反映。
- 新DB `tomotaYomuWorksDB` version 2 を開く。versionや `works` / `shelves` 構造が想定外なら中止し、勝手にDBを作成・更新しない。
- 作品レコードIDは `kakuyomu:{work_id}`。
- 登録時に既存IDを確認し、重複作品を追加しない。
- 利用者の明示操作で `works` に追加する。ページを開いたこと自体では登録しない。
- 作品情報には title、authorName、authorId、synopsis、status、episodeCount、characterCount、updatedAt、siteData等を保存。
- authorIdと `siteData.legacyFields.authorHandle` に作者ハンドルを `@` なしで保存する。
- TOCの総話数は検証済みepisodes件数を使用。

## 4. 作品編集

対象：`app/kakuyomu/kakuyomu_edit.html`

- 新DB `tomotaYomuWorksDB` version 2 の `works` から `kakuyomu:{work_id}` を読み込む。
- タイトル、作者表示名、作者ハンドル、あらすじ、作品状態、総話数、文字数、最終更新日、タグ等を編集可能。
- 保存は新DB `works` へのput。
- 2026-11-14、保存ボタンが反応しない問題を確認。作品状態inputと保存メッセージ領域に同じDOM ID `status` があったため、inputを `workStatus`、保存メッセージを `saveStatus` に分離。読み込み・保存参照も修正した。
- 修正後、利用者が編集・保存の実機動作を確認済み。

## 5. 作品情報の更新方針

- あらすじは初回登録時にWorkflowから取得し、新DBへ保存する。
- 現行コードには、既存作品のあらすじを定期的・自動的に再取得して上書きする経路は確認していない。
- あらすじ変更が必要な場合は作品編集画面で手動修正する。
- 作者ハンドルは初回取得値を保存し、通常の目次再取得で上書きしない。必要な変更は編集画面で行う。
- 目次JSONの取得・更新と、既存作品メタデータの自動更新は別機能として扱う。

## 6. しおりと話数表示

- 既存Shortcut「とよむ+しおり」は変更せず、カクヨムURLの受け渡しを維持する。
- 本棚側は作品ID・episodeId・episode URLを作品レコードへ保存する。
- 作品別TOC JSONのepisode_idと保存済みepisodeIdを照合して話数を求める。
- TOC取得失敗・ID不一致は、正しい話数を確定できない状態として扱う。貼り付けテキスト由来のepisodeCountをTOCの代わりに根拠としない。

## 7. 2026-11-14の実機確認・変更記録

| 対象 | 結果 |
|---|---|
| Workflow取得 | 作品ID `1177354054892870623`、187話／187話で成功 |
| request_id | `E2EBC0CA-9F18-492A-B2A2-6A62EA1A72F0` の実行記録あり |
| 登録ページ | Shortcutから開き、作品情報・作者ハンドルを取得できることを確認 |
| 新DB登録 | 利用者が登録成功を確認 |
| カードリンク | カクヨム作品ページへのリンクを確認 |
| しおり | 既存Shortcut経由のしおり動作を確認 |
| 作者ハンドル | `author.name` を `@` なしで保存。画面表示上の@とは区別 |
| 作品編集 | DOM ID重複修正後、編集・保存を確認 |
| 専用棚の並び順 | 2026-11-14、カクヨム・note専用棚を最終更新日順へ変更。コード反映済み。実機最終確認は別途 |

### 関連コミット

- Workflowへ作品メタデータ追加：`a0c025a3f4ed2941207646a96fee45fbd791c466`
- 作者ハンドル取得元を `author.name` に修正：`0bdb462a9360caa7fee7f75a430d425782e418e6`
- 登録ページを新DB登録・取得結果待ちへ対応：`ea94b9f14692fef8e8ec8a480bf16fcde282c594`
- 作品編集のDOM ID重複修正：`db92533b2643f0d45da4f0d13fc9c80c7a5f897e`
- カクヨム・note専用棚を最終更新日順へ統一：`5a1020b1e9e675bff34e0cb7876fa7a6732feb13`

## 8. 保留・注意事項

- カクヨム専用棚・note専用棚の並び順変更はコード反映済み。実機で最新順・反転動作を最終確認する。
- Workflow結果ファイル・TOC JSONの保持期間や古いrequest結果の整理は、依存関係を確認してから判断する。
- 本番IndexedDB・localStorage、既存Shortcut、GitHub Actionsの入出力形式を、資料整理を理由に変更・削除しない。
- PAT等の秘密情報をGitHub PagesのJavaScriptへ埋め込まない。
- この資料の更新は、アプリ機能・DBデータの変更を意味しない。
