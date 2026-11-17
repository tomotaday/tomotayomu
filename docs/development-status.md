# ともたよむ 開発状況インデックス

最終確認日：2026-11-17  
対象リポジトリ：tomotaday/tomotayomu  
対象ブランチ：main  
アプリ基準版：v3.8.1【2026/11/14】  
この文書の役割：資料室の入口。開発の現在地・優先作業・正本の所在を案内する。

> このページは開発状況の入口であり、個別仕様の詳細を重複して持たない。詳細は担当資料を正本として参照する。過去の記録と現行仕様が異なる場合は、現行コード・実機確認・決定履歴を照合して更新する。

## 1. 現在の開発状況

| 項目 | 現在の状態 | 根拠・注意 |
|---|---|---|
| アプリ基準版 | v3.8.1 | 2026-11-14。カクヨム・note連携対応版 |
| 新DB | 現行作品データの正本 | `tomotaYomuWorksDB` version 2。なろうbookmarkデータ整理を2026-11-15に実機完了。詳細はDB構成資料・移行記録 |
| 新DBの作品登録 | なろう・note・カクヨムを新DBへ保存する経路を確認 | 最新件数は実機診断で再確認。過去の3,600件を固定値にしない |
| 旧DB | 保全中 | `tomotaYomuDB` は通常本体から切り離し済み。削除・ストア削除は未承認 |
| カクヨム登録 | 専用ShortcutからActions起動・完了待ち・検証・新DB登録まで実装 | 2026-11-14、187/187話の取得、登録、カードリンク、しおり、既存作品の重複登録拒否をiPhone実機確認 |
| カクヨム作品編集 | 新DB読み書き | DOM ID重複修正後、編集・保存を実機確認 |
| カクヨム作者ハンドル | 初回取得・保存に対応 | `author.name` を@なしで保存。表示上の@と区別 |
| カクヨム・note専用棚の並び順 | 更新済み・実機確認済み | 最終更新日順と順序反転をiPhone実機で確認済み |
| あらすじ更新 | サイトごとに取得経路が異なる | カクヨムは初回取得＋手動編集。なろうはAPI更新経路あり。細部は各ガイド・コードを参照 |
| 資料室 | 内容・構成・INDEX導線確認完了 | GitHub mainの資料室リンク・Markdownリンク・HTML/Markdown対応・主要ガイド・構成資料を照合。INDEXの運用管理用棚からのリンクはiPhone実機で確認済み。資料内部の相対リンク全件の実タップ確認とは区別する |
| Shortcut連携 | 個別に確認 | 既存「とよむ+しおり」は維持。各Shortcutを未確認のまま正常扱いしない |

## 2. 現在の優先作業

1. なろう作品のトランスファーLabを独立LabDBで検証する。現行 `register.html`・本番DB・Shortcutは保護する。共通worksの日付2項目とカード表示はコード確認済み、iPhone実機確認待ち。詳細は [なろうトランスファー Lab 設計記録](narou-translator-lab.md) と [Lab README](../experiment/narou-transfer/README.md)。
2. なろうカードの読書状態を `reading` から整理済み `bookmark` へ切り替える作業は未着手。
3. 必要に応じてINDEXの資料室リンクをiPhone実機でタップ確認する。

## 3. カクヨムの現行仕様

- 専用Shortcutは共有シートのURLを変数 `work_url` に設定し、キーチェーンの `GitHub_PAT` を `token` として取得（未登録時は入力を求めて保存）する。
- `Generate UUID` でrequest_idを生成し、GitHub APIへPOST。`ref=main`、`inputs.work_url` は変数 `work_url`、`inputs.request_id` は生成UUID。
- Shortcutは `app/kakuyomu/kakuyomu_write.html?request_id={UUID}` を開く。
- Workflowが作品メタデータと目次を取得・検証し、request_idに対応する結果JSONを公開する。
- 登録ページは5秒間隔で最大60回（最大約5分）結果を確認する。これは段階処理ではなく完了待ちのポーリング。
- 検証成功後、登録ページで内容・登録先を確認し、明示操作で新DB `tomotaYomuWorksDB/works` に登録する。
- 作品IDは `kakuyomu:{work_id}`。作者ハンドルは@なしで `authorId` に保存する。
- あらすじは初回取得。既存作品の自動再取得・上書きは現行仕様にない。必要なら編集画面で手動修正。
- 登録専用Shortcutの画面確認記録は技術記録に掲載。HTTPヘッダはAuthorization（Bearer＋token）、Accept（application/vnd.github+json）、X-GitHub-Api-Version（2022-11-28）を画像確認済み。画面外の設定は未確認。
- 既存Shortcut「とよむ+しおり」は変更しない。

詳細：[`カクヨム登録・しおりガイド`](guides/kakuyomu_guide.html) / [技術記録](kakuyomu-toc-registration-investigation.html)

- 重複登録時は登録ページが既存IDを検出して拒否することを2026-11-14に実機確認。元カード・しおり状態の事後確認は技術記録に分けて記載。

## 4. 資料室の正本・担当分担

| 資料 | 正本として扱う情報 | 状態・注意 |
|---|---|---|
| `development-status.md` | 開発の現在地、優先作業、資料案内 | 本ページ |
| `database-structure.md` | IndexedDB/localStorage、画面別接続先 | 2026-11-14の現行コードを基準に整理済み。実件数は実機診断で確認 |
| `data-store-usage-inventory.md` | 画面・機能別の保存先と読み書き経路 | 主要画面・登録画面・診断画面に加え、取得失敗Nコード照合・しおり移行監査・shelfId確認・Nコード一括テストを照合。未掲載画面の追加確認は必要時に実施 |
| `data-migration-log.md` | 移行の経緯、変更前記録、検査結果、判断履歴 | 履歴として保持 |
| `repository-structure.md` | ファイル配置・役割・依存関係 | 2026-11-14のGitHub main再帰ツリー96ファイル・29ディレクトリと照合。主要な記載誤り・重複を修正済み |
| `database-structure.html` | DB構成資料の閲覧用HTML | 現行要約・リンクをMarkdown正本に合わせて更新 |
| `repository-structure.html` | リポジトリ構成資料の閲覧用HTML | 現行要約・リンクをMarkdown正本に合わせて更新 |
| `guides/*.html` | 操作・復元・診断・サイト連携の手順 | なろう・note・カクヨム・診断・復元ガイドを確認。旧削除ツールの案内と重複記述を修正。未確認事項は各ガイドに明記 |

### 資料の運用ルール

- DB構造・接続先の詳細は `database-structure.md` に集約する。
- 画面別の読み書き経路は `data-store-usage-inventory.md` に集約する。
- 移行時の決定・作業・検査結果は `data-migration-log.md` に時系列で残す。
- ファイルの所在・役割・参照関係は `repository-structure.md` に集約する。
- 操作ガイドは利用者の手順を中心にし、内部DBの詳細は正本へリンクする。
- HTML版がある資料は、Markdownを原稿とする同期方法が確定するまで、更新時に両方を照合する。
- 古い記録は削除せず「当時の記録」「履歴」と明記し、現行サマリーと混在させない。

## 5. 記録ステータスの統一

| ステータス | 意味 |
|---|---|
| 未調査 | 対象をまだ確認していない |
| 調査中 | 確認作業を進めている |
| 仕様確定 | ともたとの合意により方針が決まった |
| コード確認済み | 対象コミットのコードで実装・接続を確認した |
| 実機確認済み | 対象環境・操作・結果を実機で確認した |
| 保留 | 意図的に作業を止めている |
| 廃止 | 現行運用から外した。履歴は保持する |

コード確認済みと実機確認済みを混同しない。確認記録には可能な限り対象ファイル・コミット・確認日・環境・操作・結果を添える。

## 6. 安全ルール

1. 本番IndexedDB・localStorageを、資料整理や調査のために初期化・削除しない。
2. 旧DB・旧ストア・旧localStorageキーは、参照経路と保全要否が確定し、ともたの承認を得るまで削除しない。
3. GitHub Actions・Shortcut・Atom連携の入口や受け渡し形式を推測で変更しない。
4. 読み取り専用調査と、データを書き換える検証を明確に分ける。
5. 実装・資料更新は小さく分け、変更前SHAを記録する。
6. 実機未確認の事項は「未確認」と記載し、完了扱いしない。
7. 資料室整備を理由にアプリ本体の機能・バージョンを不用意に変更しない。
8. GitHub Pagesに秘密情報・PAT等を埋め込まない。

## 7. 保留・未完了事項

| 項目 | 状態 | 次に行うこと |
|---|---|---|
| DB構成資料のHTML/Markdown同期 | 要約・リンク照合済み | HTMLは要約ページ。Markdown正本へのリンク、要約内容、関連資料リンクを照合。完全自動同期ではないため、今後の更新時も両方を確認 |
| 保存先インベントリ | 現行HTMLの主要画面・登録画面・補助画面・診断ページを照合済み | 追加4ページのDB/localStorage接続・読み書き範囲を記録済み。未掲載ページが見つかった場合は追加確認 |
| リポジトリ構成表 | main全ツリー照合済み | 2026-11-14時点の96ファイル・29ディレクトリを照合。今後の変更時は再確認 |
| 操作ガイド・資料室リンク | 内容確認・参照先照合済み | 管理設定用棚の資料室リンク10件と資料ページ9件のローカル参照先をGitHub mainで照合。リンク先のiPhone実タップ確認は未実施 |
| 旧DBの最終保全・復元試験 | 保留 | DB整理・保全対象確定後、別領域で実施 |

## 8. 資料室リンク

- [DB構成表・接続一覧（Markdown）](database-structure.md)
- [保存先・画面利用関係の調査メモ](data-store-usage-inventory.md)
- [データ統合・参照先移行記録](data-migration-log.md)
- [リポジトリ構成表（Markdown）](repository-structure.md)
- [DB構成表・接続一覧（HTML）](database-structure.html)
- [リポジトリ構成表（HTML）](repository-structure.html)
- [バックアップ・復元ガイド](guides/backup_restore_guide.html)
- [判定センター運用ガイド](guides/diagnostic_center_guide.html)
- [なろう登録・更新・復旧ガイド](guides/narou_register_guide.html)
- [なろうトランスファー Lab 設計記録](narou-translator-lab.md)
- [なろうトランスファー Lab README](../experiment/narou-transfer/README.md)
- [カクヨム登録・しおりガイド](guides/kakuyomu_guide.html)
- [note登録・更新・復旧ガイド](guides/note_magazine_guide.html)
- [カクヨム登録・目次取得の技術記録](kakuyomu-toc-registration-investigation.html)
- [ともたよむ20：資料室整備・DB整理／復元計画](tomotayomu20-records-and-handover.md)

このページを資料室の入口とし、次スレッドへの引継ぎは本ページと各正本を参照して作成する。

## 9. 2026-11-14：v3.8.1 基準版の確定

- アプリ基準版を `v3.8.1【2026/11/14】` とする。補足表記は「カクヨム・note連携対応版」。
- ルート `index.html` のブラウザタイトルとトップ表示を同じ表記へ更新。commit `80d6eb19e1cb7e939e8523ea255a6dfa07d32fef`。
- カクヨム：専用Shortcutによる作品登録フローをiPhone実機で確認。187/187話の取得、登録、カードリンク・しおり、既存作品の重複登録拒否を確認。
- note：登録済み全マガジン目次との照合によるしおり取り込みを本番iPhoneで確認。記事URLが一意に一致した作品へ保存され、カードの続きリンクと進捗表示（94/106話）を確認。
- noteしおりの未一致・複数一致・目次取得失敗は専用テストページでシミュレーション確認済み。本番環境での各異常系は未実施。
- DB構成・保存先インベントリ・リポジトリ構成・主要ガイドを現行コードに合わせて更新。GitHub mainの全ツリー照合、資料室内のMarkdownリンク先照合、管理設定用棚の資料室リンク照合を実施。iPhoneでのリンク実タップ確認は未実施。

### 2026-11-15 なろうbookmarkデータ整理

- なろう通常・R18作品3,597件を対象に、作品レコードのbookmarkを整理。実行前にworksストア全件のJSONバックアップを取得。
- bookmarkとreading.positionの数値を比較し、大きい方を採用。短編読了は `"R"`、未読は未設定。bookmark・reading.positionの数値0を整理。
- 実行後の全件再走査で、bookmarkの数値0：0件、reading.positionの数値0：0件、短編以外のR：0件、追加変更予定：0件を確認。短編読了70件を確認。
- bookmarkデータ整理は実機完了。カードはまだreading参照のまま。カード切替とreading廃止は別工程。詳細は `data-migration-log.md`。

### 2026-11-14 資料室整備の締め

- 資料室の入口・DB構成・保存先インベントリ・移行履歴・リポジトリ構成・各操作ガイド・カクヨム技術記録について、GitHub main上の記述と参照先を照合した。
- Markdownリンク監査では7資料・15リンクを確認し、欠落なし。HTML/Markdownの対応資料も内容・リンクを照合した。
- INDEXの運用管理用棚からのリンクは、ともたがiPhone実機で確認済み。今回のAtom取込（手動）ボタンの反応確認も、この導線確認の過程で発生した。資料内部の相対リンク全件を実機でタップしたという意味ではない。
- INDEXの「Atom取込（手動）」は通常運用上の重複操作としてメニューから除外。関連クリックイベント処理は保存先インベントリに削除候補として記録した。自動取込関数は現役のため削除しない。
- 資料室整備は一区切りとし、今後は新しい調査結果・実装変更が発生した資料だけを更新する。旧DB保全・復元試験は別工程として保留する。


## 2026-11-15：なろう通常作品 通訳レジスターLabの開始

- ともたとの合意により、なろう通常作品の取得データを共通 `works` 形式へ変換する仕組みを、独立した実験環境で設計・検証する。
- 実験ページ名は `narou_translator_lab.html`。`_lab` は開発・実験中の識別子であり、本番導入時に外す想定。最終名称・配置・Shortcut URL切替は完成後に判断する。
- 入口はショートカットURL、通訳ページはデータを永続保存しない通過点、作品データの出口・保存先は `works` のみとする。通訳ページを作品情報の正本・参照先にしない。
- 実験は独立LabDBで行い、本番DB・本番localStorage・現行Shortcut・本番カード表示を変更しない。現行 `register.html` は本番経路として保護し、読み取り・参考対象とする。
- 2026-11-15に現行 `register.html` を読み取り専用で確認。API取得データはページ内変数 `fetchedWork` に保持され、登録先確認に `shelves`、重複確認に `works` を読み、新規レコードを `works.add(record)` で登録する。確認したコード内に作品情報をsessionStorage/localStorageへ永続保存する処理は見当たらない。
- 現行コードでは共通項目への変換が一部にとどまり、取得データ全体を `siteData.legacyFields` に保持している。共通項目への具体的な変換ルールは未確定。API項目・欠損・値の意味を確認してから決める。
- 初期検証資料は、なろう10作品のサンプルJSON。カクヨム3作品・note2作品のサンプルは別資料として保持し、今回のなろうLabには混ぜない。
- この段階では実験ページ・LabDBをまだ作成していない。本番コード・本番データ・Shortcut・GitHub Actionsへの変更は行っていない。
- 詳細・未確定事項・手順は `narou-translator-lab.md` を正本とする。


## 2026-11-15：なろう通訳レジスターLabの実験環境を作成

- `experiment/narou-translator/narou_translator_lab.html` を作成。
- 独立DB `tomotaYomuNarouTranslatorLabDB` v1 / `sourceWorks` を実装。選択したサンプルJSONの10作品を変換せず保存する初期環境。
- JSON形式・10件・なろう作品・ID重複等を保存前に検証し、1トランザクションで登録する。作品一覧と元JSONを画面で確認できる。
- `experiment/narou-translator/README.md` に安全境界・使い方・次工程を記録。
- コード上、本番DB・旧DB・Atom DB・Memo DB・localStorage・sessionStorage・API・Shortcut・Actionsへの接続なしを確認。
- GitHub PagesのiPhone実機確認とサンプル10件の実取込は未実施。完了扱いにせず、次工程で実機確認する。
- 詳細は `narou-translator-lab.md` の「実験環境の初期実装」を参照。


## 2026-11-15：なろうトランスファーLabの日付項目・作品カード整備

- 共通worksの日付項目を `publishedAt`（初回登録日）と `lastPublishedAt`（最終更新日）の2つに整理。値の取得可否とは独立して、項目枠を保持する方針を確定。
- Labの新規取込・既存レコード移行で2項目を保持し、旧 `updatedAt` は `lastPublishedAt` へ移行して削除する処理を実装。
- なろう作品カードに「初回登録」「最終更新」の2欄を追加。値がない場合は `—` を表示。項目診断にも2項目を追加。
- 対象ファイル：`experiment/narou-transfer/narou_transfer_lab.html`
- commit：`6a199cfcfb5fca89dcaadf69c738d41b9d8fa54e`
- GitHubから更新後ファイルを再取得し、項目保持・移行・カード表示・診断のコードを確認済み。
- **iPhone実機での更新後DB確認・10作品診断・カード表示は未確認。** 実機確認が終わるまでは完了扱いしない。
- 本番 `register.html`、INDEX、本番DB、Shortcut、GitHub Actionsへの変更なし。
- 詳細は [なろうトランスファー Lab 設計記録](narou-translator-lab.md) を正本とする。


## 2026-11-17：なろうTransfer／Translatorの共通works変換方針

- WEBサイト → iOSショートカットで元URLを受け取る → サイト別TranslatorでAPIデータを取得・共通形式へ変換 → 共通worksへ渡す → 作品カードがworksを参照、という全体経路を整理。
- Transferは受け渡し全体、Translatorはサイト固有データを共通works形式へ変換する処理、Registerは変換済みデータを本棚へ登録する最終処理として役割を整理。
- なろうTranslatorは全年齢API・R18 APIの項目名の違いを吸収し、同じ意味の情報を共通works項目へ統一する。
- `id` はともたよむ専用の一意キー。APIから取り込まず、既存作品の更新時も変更しない。作品IDは `workId`、作者IDは `authorId` と分ける。
- 元URLはShortcutから受け取り、生成・加工せず丸ごと保持する。
- ステータスは全年齢・R18共通で `novel_type` と `end` を使い、「短編」「完結」「連載中」の3種類に変換する。
- 日付は `publishedAt`（`general_firstup`：初回掲載日）と `lastPublishedAt`（`general_lastup`：最新話更新日）の2項目だけを使用する。
- 文字数 `length` は既存の `characterCount` へ、全話数 `general_all_no` は `episodeCount` へ、作者名 `writer` は `authorName` へ統一する。
- ジャンルは共通 `genres`（`categories` / `attributes`）にまとめ、全年齢の `biggenre`・`genre` とR18の `nocgenre`、各作品属性を保持する。内部の詳細スキーマ・`isr15` の扱いは未確定。
- API由来情報はAPIを正とし、ともたよむ独自情報（内部ID、本棚、しおり、検索除外、手動登録情報等）はAPIで上書きしない。APIに項目がない場合は既存値を維持し、空値・nullは項目ごとに扱いを決める。
- `time`、`novelupdated_at`、`updated_at`、`isstop`、`gensaku`、ポイント・評価系等は取り込まない。
- 作者かな情報は、現在値を消さず、別経路から流入した場合は受け取る。Transferで無理に取得する仕組みは追加しない。
- Translatorページには「何を、何から、どの共通形式へ変換するページか」を常設説明し、対応表・除外項目・更新履歴を残す。
- 詳細な項目対応・変換規則・未確定事項は [なろうトランスファー Lab 設計記録](narou-translator-lab.md) を正本とする。
- 今回は資料室の設計記録のみ更新。Labコード、本番DB、本番登録経路、Shortcut、GitHub Actionsは変更していない。
