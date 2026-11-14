# ともたよむ リポジトリ構成表

最終確認日：2026-11-14
対象リポジトリ：tomotaday/tomotayomu
対象ブランチ：main
現行アプリ基準版：v3.8.1【2026/11/14】
正本：ルートの `index.html`

冒頭の旧一覧は過去時点の構成記録を含む。現行の主要パスは末尾の「2026-11-14 現行ツリー・機能接続の追記」を参照し、ファイルの移動・追加・削除時はGitHub mainの実体を再確認すること。

## 1. リポジトリ全体

| パス | 役割・内容 | 備考 |
|---|---|---|
| `index.html` | ともたよむ本体 | GitHub Pagesの正本。IndexedDBを利用 |
| `register.html` | なろう作品登録の入口 | Shortcut等から `register.html?ncode=...` で呼び出すためルート固定 |
| `kakuyomu_add.html` | 旧カクヨム登録ページ | 現行登録Shortcutの入口ではない。参照元を確認するまで保持 |
| `note_magazine_add.html` | noteマガジン登録の入口 | 現役Shortcutの呼び出し先。ルート固定 |
| `README.md` | リポジトリ概要 | 現状は最小限の内容。今回の整理では変更しない |
| `.github/workflows/` | GitHub Actions | 自動取得・更新・検証処理 |
| `app/` | アプリ内の管理・補助画面 | 機能別に分類 |
| `data/` | アプリが参照するデータ | JSON等。用途ごとに分類 |
| `docs/` | 説明資料・ガイド | GitHub Pagesのアプリ本体とは分離 |
| `scripts/` | Actions等から実行するスクリプト | 本番処理と診断処理を分離 |
| `tools/` | 手動利用する診断・出力ツール | 本体機能とは独立 |
| `archive/delete_pending/` | 削除候補の一時保管場所 | 退避中。削除未実施 |

## 2. app（管理・補助画面）

| パス | 主なファイル | 役割 |
|---|---|---|
| `app/author/` | `author.html` | 作者管理 |
| `app/kakuyomu/` | `kakuyomu_edit.html` | カクヨム作品情報の編集 |
| `app/memo/` | `tomota_memo.html` | ともた用メモ |
| `app/register/` | `work_add.html` | 検索除外作品等の手動登録 |
| `app/register/` | `search_excluded_compare.html` | 取得失敗Nコード照合 |
| `app/register/` | `search_excluded_edit.html` | 検索除外作品情報の編集 |
| `app/settings/` | `color_studio.html` | 表示カラー設定 |
| `app/shelf/` | `shelf_manager.html` | 本棚管理 |
| `app/shelf/` | `synopsis_repair.html` | あらすじ修復 |

## 3. docs（説明資料）

| パス | 主なファイル | 役割 |
|---|---|---|
| `docs/guides/` | `kakuyomu_guide.html` | カクヨム利用ガイド |
| `docs/guides/` | `narou_register_guide.html` | なろう登録ガイド |
| `docs/guides/` | `note_magazine_guide.html` | noteマガジン登録ガイド |
| `docs/` | `repository-structure.md` | 本ファイル。リポジトリ構成表 |
| `docs/` | `database-structure.md` / `database-structure.html` | DB構成表・接続一覧 |

## 4. data（アプリ参照データ）

| パス | 内容 | 備考 |
|---|---|---|
| `data/author-list.json` | 作者一覧 | 作者管理・Atom対象作者情報 |
| `data/atom/author-feeds.json` | 作者Atomフィード取得結果 | GitHub Actionsが更新 |
| `data/kakuyomu-toc/` | カクヨム目次データ | 作品ID単位のJSON |
| `data/note-index-*.json` | noteマガジン目次データ | マガジン単位のJSON |

## 5. scripts（実行スクリプト）

| パス | 主なファイル | 役割 |
|---|---|---|
| `scripts/atom/` | `publish_author_atom_feeds.py` | 作者Atomフィードの本番取得・公開 |
| `scripts/diagnostics/atom/` | `benchmark_atom_conditional_get.py` | Atom条件付きGETの診断 |
| `scripts/diagnostics/atom/` | `benchmark_author_atom_fetch.py` | 作者Atom取得の診断 |
| `scripts/diagnostics/atom/` | `benchmark_author_atom_fetch_full.py` | 作者Atom全件取得の診断 |

本番スクリプトと診断スクリプトは混在させない。
本番Workflowから参照されるスクリプトの移動時は、Workflow側のパスも必ず確認する。

## 6. .github/workflows（GitHub Actions）

2026-11-05時点の履歴一覧（現行一覧ではない）：

| ファイル | 役割・区分 |
|---|---|
| `publish-author-atom-feeds.yml` | 作者Atomフィード本番取得・公開 |
| `note-magazine-index.yml` | noteマガジン目次更新 |
| `kakuyomu-toc.yml` | カクヨム目次取得 |
| `benchmark-atom-conditional-get.yml` | Atom条件付きGETの検証 |
| `benchmark-author-atom-fetch.yml` | 作者Atom取得の検証 |
| `benchmark-author-atom-fetch-full.yml` | 作者Atom全件取得の検証 |
| `measure-author-atom-window.yml` | 作者Atom取得範囲・時間の計測 |

2026-11-14に管理設定棚と現行ガイドから参照される次の3本は、現行機能として個別に確認した：`publish-author-atom-feeds.yml`、`note-magazine-index.yml`、`kakuyomu-toc.yml`。上表の他のWorkflowが現在も存在するか・現役かは、この確認では網羅していない。

Workflowを変更・移動する場合は、参照するスクリプトのパス、トリガー、権限、生成データの保存先を確認する。
診断用Workflowは本番Workflowと区別し、実行確認が済んでいないものを正常確認済みと扱わない。

## 7. tools（手動利用ツール）

| パス | 主なファイル | 役割 |
|---|---|---|
| `tools/diagnostic/` | `storage_inventory.html`, `ncode_extract.html`, `work_db_production_card_audit.html`, `restore_test.html` | 保存領域調査、Nコード抽出、作品カード監査、バックアップ復元テスト |
| `tools/diagnostic/` | `work_db_*.html`, `shelf_master_*.html` | 新DB監査・プレビュー・移行検証 |
| `tools/diagnostic/` | `ncode_extract.html`, `restore_test.html` | Nコード抽出・専用領域への復元テスト |
| `tools/maintenance/` | 現行mainで該当ページの実在を確認できていない | 旧一覧の掲載を現行機能として扱わない |
| `tools/export/` | `export_ncodes.html` | Nコード出力 |

## 8. archive/delete_pending（削除保留ファイル）

削除候補を一時退避している場所。2026-11-05時点で合計19ファイル。

| パス | 件数 | 状態 |
|---|---:|---|
| `archive/delete_pending/html/` | 10 | HTML旧版・実験用ページ |
| `archive/delete_pending/scripts/` | 4 | Atom等の診断・実験用スクリプト |
| `archive/delete_pending/workflows/` | 5 | 旧診断用Workflow |
| **合計** | **19** | **削除未実施・保留中** |

注意：
- 退避ファイルは現役処理から切り離した削除候補であり、現役ファイルとして使用しない。
- 退避Workflowには古いスクリプトパスを参照するものがある。再利用する場合は、そのまま実行せず内容と参照先を再確認する。
- 削除は依存関係・必要性を確認し、別途判断してから行う。

## 9. ルートに残す入口ファイル

次のファイルは、外部から直接URLで呼び出されるため、原則としてルートに置く。

| ファイル | 残す理由 |
|---|---|
| `index.html` | GitHub Pagesの本体URL |
| `register.html` | なろう登録Shortcut等の呼び出し先 |
| `kakuyomu_add.html` | 旧カクヨム登録ページ。現行専用Shortcutの入口ではないため、参照元を確認するまで保持 |
| `note_magazine_add.html` | note登録Shortcutの呼び出し先 |
| `README.md` | GitHubリポジトリの標準説明ファイル |

移動する場合は、Shortcut・外部URL・アプリ内リンクの参照先を洗い出し、利用者側の変更も含めて事前に合意する。

## 10. 今後の整理ルール

1. 既存ファイルを移動する前に、リンク・相対パス・Workflow・Shortcut等の参照元を調べる。
2. 原則として一度に一つのファイルを移動する。
3. 移動先にファイルを作成し、内容を確認してから参照元を更新する。
4. 更新後はGitHub上の最新SHAを使って確認し、動作確認を行う。
5. 本番データ、IndexedDB、GitHub Actions、Shortcut、Atom連携を壊さないことを最優先とする。
6. 構成整理だけではアプリのバージョン番号を変更しない。
7. 古いファイルは即時削除せず、まず `archive/delete_pending/` に退避する。
8. ルートの入口ファイルは、外部呼び出しへの影響を確認せず移動しない。
9. この表は構成変更のたびに更新し、実際のGitHub構成と食い違わないようにする。

## 11. 2026-11-05時点の整理状況

- 現役HTML管理画面・ガイド・ツールの機能別配置：一段落
- Atom本番スクリプトの移動：完了、移動後の本番Workflow実行成功
- Atom診断スクリプト・診断Workflowの配置整理：完了、診断Workflowの実行確認は保留
- 旧ファイル19件の退避：完了、削除は保留
- Atom取得：スケジュール実行・手動実行ともに取得完了を確認。失敗2件は退会作者によるものと確認
- アプリ現行基準版：v3.8.0【2026/11/09】

この時点で、現役ファイルの構成整理はいったん一段落とする。

## 12. 2026-11-09（v3.8.0）更新

- 新DBへの段階移行を開始。`tomotaYomuWorksDB` version 2（`works` / `shelves`）を追加。
- なろう読書位置の読み書きを新DB `works.reading` へ切替。旧読書位置データは削除せず保持。
- note・カクヨムを含む3サイト共通の履歴を実装。最大30件保存、最大10件表示。
- 資料室に `database-structure.html` / `database-structure.md`（DB構成表・接続一覧）を追加。
- 本ページとDB構成表は、GitHub mainの実ファイル・現行コード接続を基準に更新。
- 作者更新表示期間スライダーの初期化タイミングを修正。動的に管理メニューを構築した後にイベントを接続する。

## 13. 2026-11-10 追加確認：診断ページ整理とShortcut入口の保護

- 2026-11-10時点で、役目を終えたHTMLを累計16ファイル削除。削除前SHA照合、削除後404確認を実施した記録がある。削除対象はHTMLのみで、本番DB・localStorage・Atom DB・Memo DBは変更していない。
- `tools/diagnostic/ncode_extract.html` は新DB `tomotaYomuWorksDB` v2からなろう作品3,596件を抽出できることをiPhone / Braveで確認済み。独自の診断機能は残す。
- 残存診断・保守ページの最終整理は未完了。ファイルごとに最新SHA、DB接続先、version、読み書きの有無、用途を確認してから判断する。

### Shortcutから呼び出される入口ファイル

- `register.html`、`note_magazine_add.html` は現役の登録入口。`kakuyomu_add.html` は旧登録ページだが、過去リンクの有無を確認するまで削除・移動しない。
- iPhoneショートカットとの整合性確認は未実施。なろうの作者登録ショートカットでエラーが発生しているが、原因は未特定。他のショートカットも未確認。
- ShortcutのURL、入力形式、保存先、後続処理を照合するまで、入口ファイルの移動・改名・処理変更を行わない。

---

## 2026-11-14 現行ツリー・機能接続の追記

この資料の上部にある2026-11-05時点の一覧は当時の構成記録として保持する。現行のファイル配置はGitHub mainの実ツリーを優先する。以下は2026-11-14に確認した主要な現行パス。

### ルート入口

| パス | 役割 | 注意 |
|---|---|---|
| `index.html` | ともたよむ本体・本棚・管理設定棚 | GitHub Pagesの入口 |
| `register.html` | なろう作品登録入口 | Shortcut等から呼ばれるためルート固定 |
| `note_magazine_add.html` | note登録入口 | Shortcut等から呼ばれる可能性があるためルート固定 |
| `.github/workflows/kakuyomu-toc.yml` | カクヨム目次・作品情報取得Workflow | Shortcutから起動する現行フロー |
| `app/kakuyomu/kakuyomu_write.html` | カクヨム新規登録ページ | UUID付きrequest_idでActions結果を待つ |
| `app/kakuyomu/kakuyomu_edit.html` | カクヨム作品編集 | 新DBを読み書き |
| `kakuyomu_add.html` | 旧カクヨム登録ページ | 現行登録Shortcutの入口として扱わない。削除・移動は参照元確認後 |

### 現行の主要フォルダ

| パス | 主な内容 |
|---|---|
| `app/author/` | 作者管理 |
| `app/kakuyomu/` | カクヨム登録・編集 |
| `app/memo/` | ともためも |
| `app/register/` | 検索除外作品の手動登録・照合・編集 |
| `app/settings/` | カラー工房 |
| `app/shelf/` | 本棚管理・あらすじ補完 |
| `docs/` | 開発状況、構成資料、移行記録、技術記録 |
| `docs/guides/` | なろう・note・カクヨム・診断・バックアップの操作ガイド |
| `data/kakuyomu-toc/` | 作品ID別カクヨム目次JSON |
| `data/kakuyomu-toc-requests/` | request_id別の登録実行結果・一時TOC |
| `tools/diagnostic/` | 読み取り専用診断・監査・復元検証 |
| `tools/export/` | データ出力 |
| `tools/maintenance/` | 明示操作型メンテナンス |
| `scripts/` | Workflow等から呼び出すスクリプト |

### 現行資料室ファイル

- `docs/development-status.md`：資料室入口・開発状況
- `docs/database-structure.md` / `database-structure.html`：DB構成・接続先
- `docs/data-store-usage-inventory.md`：画面・機能別の保存先調査
- `docs/data-migration-log.md`：移行履歴
- `docs/repository-structure.md` / `repository-structure.html`：ファイル構成
- `docs/kakuyomu-toc-registration-investigation.html`：カクヨム登録・目次取得の技術記録
- `docs/guides/diagnostic_center_guide.html`：判定センター運用・判定基準
- `docs/guides/backup_restore_guide.html`：バックアップ・復元手順
- `docs/guides/`：なろう・note・カクヨム等の利用者向けガイド

### 2026-11-14 実在確認した主要ファイル

| パス | 役割・確認範囲 |
|---|---|
| `index.html` | 本棚本体、共通作品DB読込、読書・しおり・更新・履歴・作者Atom |
| `register.html` | なろう登録入口 |
| `note_magazine_add.html` | note登録入口 |
| `kakuyomu_add.html` | 旧カクヨム登録ページ。現行専用Shortcutの入口ではない |
| `app/shelf/shelf_manager.html` | 新DBの棚マスター・作品棚ID管理 |
| `app/author/author.html` | 新DB作品の作者情報管理 |
| `app/kakuyomu/kakuyomu_write.html` | カクヨム新規登録 |
| `app/kakuyomu/kakuyomu_edit.html` | カクヨム作品編集 |
| `app/register/work_add.html` | 手動登録・検索除外作品管理 |
| `app/register/search_excluded_edit.html` | 検索除外作品情報編集 |
| `app/register/search_excluded_compare.html` | 取得失敗Nコード照合 |
| `app/settings/color_studio.html` | カラー工房 |
| `app/shelf/synopsis_repair.html` | あらすじ補完 |
| `app/memo/tomota_memo.html` | ともためも |
| `tools/diagnostic/storage_inventory.html` | IndexedDB・localStorage保存領域診断 |
| `tools/diagnostic/ncode_extract.html` | 新DBからのNコード抽出・判定 |
| `tools/diagnostic/work_db_production_card_audit.html` | 新DB作品カード監査 |

※上表はこの作業で個別にGitHub main上の実在を確認した主要ファイルであり、リポジトリ全ファイルの完全な一覧ではない。

### カクヨムWorkflowのデータ経路

- `.github/workflows/kakuyomu-toc.yml` が `workflow_dispatch` で起動される。
- request_id別の結果JSON・TOC JSONを `data/kakuyomu-toc-requests/` に出力する。
- 作品別TOCを `data/kakuyomu-toc/{work_id}.json` に保存する。
- 登録ページ `app/kakuyomu/kakuyomu_write.html` はrequest_idで結果を照合し、検証成功後に新DBへ登録する。
- 既存Shortcut「とよむ+しおり」は別経路として維持する。

### 構成表の更新ルール

1. ファイルを移動・改名・削除する前に、index・Shortcut・Workflow・相対リンクの参照元を確認する。
2. 現在のGitHub mainツリーとこの資料を照合し、実在しないファイルを現役として掲載しない。
3. MarkdownとHTMLの両方がある資料は、更新時に双方の内容とリンクを照合する。
4. 構成整理だけではアプリのバージョン番号を変更しない。
5. 本番DB・localStorage・Shortcut・Actionsを壊さないことを最優先とする。

## 2026-11-14：v3.8.1基準版の更新

- 現行アプリ基準版を `v3.8.1【2026/11/14】`「カクヨム・note連携対応版」とする。
- ルート `index.html` のバージョン表示・ブラウザタイトルを更新した。commit `80d6eb19e1cb7e939e8523ea255a6dfa07d32fef`。
- noteしおりの本番受信処理はルート `index.html` に実装され、登録済み全マガジン目次との一意照合後に新DBへ保存する。
- `experiment/note-bookmark/index.html` は動作確認後に削除済み。既存 `experiment/bookmark/` は維持。
