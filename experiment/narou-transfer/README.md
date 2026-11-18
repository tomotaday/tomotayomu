# なろうトランスファー Lab

各サイトの作品データを、ともたよむの共通 `works` 形式へ受け渡すための独立実験環境。現在は、なろう全年齢API・R18 APIの取得データを調査し、共通形式へ変換するTranslatorの検証を行う。

## 現在の構成

- 実験ページ：`narou_transfer_lab.html`
- LabDB：`tomotaYomuNarouTranslatorLabDB` version 7
- Object Store：
  - `sourceWorks`（keyPath: `id`）：初期サンプル原本用ストア。現行画面のTranslatorプレビューでは参照・更新しない
  - `cleanWorks`（keyPath: `id`）：整理版の既存作品データ
  - `labShelves`（keyPath: `id`）：Lab内の棚情報
  - `apiRawResponses`（keyPath: `id`）：全年齢API・R18 APIから取得した生JSON、API種別、取得日時
  - `works`（keyPath: `id`）：Translator変換結果の保存先。version 7で追加。Atom由来の `newUrl` を含む有効な10作品だけを保存する
- 初期検証データ：なろう10作品（通常API 8件、R18 API 2件の生JSONを確認済み）
- 生APIデータは `apiRawResponses` に原形を保持する。Translatorプレビュー自体は読み取り専用。保存は独立した第9節の明示操作で `works` ストアに対してのみ行う

## Transfer／Translator／Registerの役割

- **Transfer**：各サイトの作品データを、ともたよむの共通形式へ受け渡す仕組み全体
- **Translator**：サイト固有のAPI・データ項目を読み取り、共通 `works` 形式へ変換・整理する処理
- **Register**：変換済みデータを本棚へ登録する最終処理

このLabで扱うのはTransfer全体のうち、取得データの調査とTranslatorの変換検証まで。**Registerは実験室に持ち込まない。** 本番登録・本番DBへの書き込みは行わない。

## Translator変換プレビュー

「8. Translator変換プレビュー（読み取り専用）」から、保存済みAPI生JSONを共通works形式へ変換して確認できる。

- `apiRawResponses` と `cleanWorks` をreadonlyトランザクションで読み込む
- Nコード（`workId`）で既存作品を照合する
- 変換結果は画面に作品ごとに表示し、全件JSONをコピーできる
- 変換処理はメモリ上のみ。TranslatorプレビューからLabDBへ書き込まない
- 既存作品がある場合は内部 `id`、元URL、棚、しおり、検索除外、既存作者ID、作者かな情報など、ともたよむ側の管理情報を保持する
- API項目が欠落・空文字・null・空白のみの場合は既存値を上書きしない
- なろうAPIから作品URLは取得できないため、Atomで補完する。Atom由来の正規URLは新設する `newUrl` に保存し、現在の `url` は移行中の旧URLとして保持する。NコードからURLを生成しない
- 新規作品の内部 `id` はこのプレビューでは採番しない

## 主な変換対応

| 共通works項目 | API項目 | 扱い |
|---|---|---|
| `workId` | `ncode` | 大文字に統一 |
| `title` | `title` | API値を反映 |
| `synopsis` | `story` | API値を反映 |
| `authorName` | `writer` | API値を反映 |
| `authorId` | 全年齢 `userid` | 既存値があれば保持。未設定時のみAPI値を採用。R18 APIに作者IDがなければ未設定 |
| `publishedAt` | `general_firstup` | 初期登録日。必須。欠落・空値・不正値は変換エラー |
| `lastPublishedAt` | `general_lastup` | 最新話登録日。必須。欠落・空値・不正値は変換エラー |

### 日付形式・タイムゾーン

- 共通worksの日付文字列は `YYYY/MM/DD HH:mm`（例：`2026/10/10 19:00`）に統一する。作品カードと同じく分まで保持・表示し、秒は含めない。ゼロ埋めを維持し、文字列ソートでも時系列順になる形式とする。
- なろうAPIの `general_firstup`・`general_lastup` のようにタイムゾーン表記がない日時は、日本時間（JST）の日時として解釈する。日付部分をJSTの暦日として採用し、UTC変換で日付をずらさない。
- ZまたはUTCオフセット付きの日時（Atom等）は、実際の時刻をJST（UTC+9）へ変換してから `YYYY/MM/DD HH:mm` にする。
- 必須日付が欠落・null・空文字・空白のみ・不正な形式／実在しない日付・時刻の場合は変換エラーとし、正常な変換として扱わない。空文字の項目枠を作ってエラーを隠さない。
- 既存作品に以前の日付がある場合は値を不用意に消さず保持するが、今回のAPI必須日付が欠落している事実はエラーとして残す。
| `episodeCount` | `general_all_no` | 全話数 |
| `status` | `novel_type`・`end` | 短編／完結／連載中へ変換 |
| `keywords` | `keyword` | 空白区切り文字列を配列化 |
| `genres` | `biggenre`・`genre`・`nocgenre`・属性フラグ | `source` と元の `value`・型を保持 |

### 属性フラグの対象範囲

現行プレビューの属性項目リストは、ユーザー提供の通常API8件・R18 API2件の標本で確認できた次の項目に限定している。

- `isr15`、`isbl`、`isgl`、`iszankoku`、`istensei`、`istenni`

これは標本10件で確認した範囲であり、API仕様上の全属性項目を網羅する保証ではない。未知の `is...` 項目は自動採用せず、診断として表示する。0/1等の元の値・型はBooleanへ変換しない。

## API項目の除外

- `length`、`time`、`novelupdated_at`、`updated_at`、`isstop`、`gensaku`、`kaiwaritu`、`sasie_cnt` は共通worksへ取り込まない
- ポイント・評価・ブックマーク数・感想数・レビュー数等も取り込まない
- APIの `updated_at` を取得日時として流用しない。取得日時は生データ側の `fetchedAt` で管理する

## 共通worksの日付項目

| 項目 | 意味 | 方針 |
|---|---|---|
| `publishedAt` | 初回掲載日 | `general_firstup` |
| `lastPublishedAt` | 最新話更新日 | `general_lastup` |

旧 `updatedAt` は `lastPublishedAt` へ移行し、旧項目名は残さない。APIの `novelupdated_at` と `updated_at` は取り込まない。

## 安全境界

- 本番DB `tomotaYomuWorksDB`、旧DB、その他の本番IndexedDBには接続しない
- 本番localStorage / sessionStorageを変更しない
- 本番 `register.html` とINDEXを変更しない
- Shortcut・GitHub Actionsと連携・変更しない
- 本番作品カード・本棚・本番データへ書き込まない
- TranslatorプレビューはLabDBをreadonlyで読み込むだけ
- API取得ボタンを押した場合に限り、なろう通常API・R18 APIへ読み取り通信を行い、取得した生JSONをLabDBの `apiRawResponses` に保存する
- Registerは実験対象外

## 現在の到達点（2026-11-19）

- LabDB version 7。既存4ストアを保持したまま、共通作品保存用 `works` ストアを追加
- 通常API8作品・R18 API2作品の生JSONを取得し、項目監査を実施
- 全10作品の生JSON一括コピー機能を実装
- 共通worksへの読み取り専用Translator変換プレビューを実装
- 変換結果の一括コピーを実装
- 変換関数の単体確認で、既存の内部ID・URL・棚・しおり・検索除外・作者ID・作者かな情報の保持、キーワード分割、status変換、genresの元型保持を確認
- GitHubコード・JavaScript構文確認済み。commit：`3660d4099311b178bab5894932abb2871c1e39cb`
- iPhone実機で10作品の日時表示を確認し、違和感なし。**Translator全項目の出力・Atom URL補完・LabDB保存・作品カード表示の総合確認は未完了。**
- LabDB version 7の `works` ストアと、第9節の保存・カード表示UIを追加。保存は10作品すべてに内部 `id`・有効な `newUrl` があり、変換エラーがなく、`works` が空の場合だけ `add` で実行。既存レコードは上書きしない。コードcommit：`1aed4d06f2c69c69a04d0aa23d241c06f4b74739`。iPhone実機でのversion 7移行確認は未実施。
- 2026-11-19、日付2項目を必須検証に変更。欠落・空値・不正値は変換エラーとして表示し、`YYYY/MM/DD HH:mm` に正規化。タイムゾーンなしはJST、明示オフセット付きはJSTへ変換。秒は含めない。短編判定は `novel_type === 2 && end === 0`。HTML commits：`611bc9f7b22750d3ae643f5a06bc8f381ffd0730`、`013628ce463e2951b7f76d530775e55d640c2e12`、正規表現修正：`24cd9b69ec0c7bd72bf741834884dec651d2c7f8`

## 実機確認手順

1. GitHub Pagesで実験ページを開く
2. 「保存内容を再読込」でLabDBの接続状態を確認する
3. 「保存済みAPIデータを調査」で通常API8件・R18 API2件が表示されることを確認する
4. 「全作品の生JSONをまとめてコピー」で必要なら生データを控える
5. 「保存済みAPIデータを共通worksへ変換してプレビュー」を押す
6. 変換件数・既存作品との照合件数・各作品JSON・確認事項を確認する
7. 「変換結果をまとめてコピー」で全件を控え、必要に応じて会話で検査する
8. LabDBの保存件数が変換操作によって増減・更新されていないことを確認する

特に、通常APIの既存作者IDが上書きされないこと、R18の手動作者IDが維持されること、API単独のプレビューでURLを生成・推測しないこと、API空値が既存値を消さないことを確認する。作品URLは次工程でAtomから取得する。

## 次の工程

1. iPhone実機でTranslator変換プレビューを実行し、10作品の出力を確認する
2. 出力と設計記録の対応表を照合し、誤変換・欠落・警告を修正する
3. APIで不足する作品URLをAtomから取得する。Atomは最大100件単位とし、100件を超える場合は複数回に分割する
4. 既存 `url` を旧URLとして保持し、Atomの返却URLを新設予定の `newUrl` に保存する。全件検証後、Lab作品カードの接続先を `newUrl` に切り替え、通常・R18をiPhoneで確認する
5. API＋Atomの統合結果をLabDBの独立した `works` ストアへ保存し、保存データからLab作品カードを表示する（本番DBには接続しない）
6. 必要に応じてAPI標本を増やし、属性フラグ等の網羅性を調べる。他サイトTranslator（カクヨム・note等）は別々に設計する
7. 正規URLへの移行確認後、旧 `url` のバックアップを確保してから旧項目を削除する。Register・本番接続・本番導入はLab検証とは別工程として判断する


## API＋Atom統合取得と正規URL移行（2026-11-19追記）

### 取得の役割分担

- なろうAPI：作品メタデータを取得する主経路。
- Atom：APIレスポンスに含まれない作品URLを補完する経路。
- Translator：APIとAtomの情報を作品単位で統合し、共通 `works` 形式へ変換する。
- Atomの取得単位は最大100件。100件を超える場合は複数回に分け、取得先への負荷に配慮する。
- URLはAtomの返却値そのものを採用し、Nコードから組み立てない。

### 旧URL・新URLの二段階移行

- 現在の `url` は移行中の旧URLとして保持する。
- 新たに `newUrl` を設け、Atomから取得した正規URLを保存する。
- 既存のR18作品URLの一部には、全年齢向けのURL組み立て方式で生成されたと見られる例がある。スムーズに接続できても正規URLとは限らないため、Atomの返却URLを正とする。
- 全作品のAtom取得・URL検査後、Lab作品カードの接続先を `newUrl` に切り替える。通常作品・R18作品をiPhoneで実際に開いて確認する。
- 問題がなければ、旧 `url` のバックアップを確保してから旧項目を削除する。検証前に旧URLを削除しない。
- Atomで取得できなかった作品は旧URLを保持し、未取得として明示する。未取得が残る場合のカード切替条件・再取得方法はLab実装時に確認する。

### 次のLab実験

API取得→Atom URL補完→Translator変換→Atomの返却URLを `newUrl` へ保存→LabDBの独立 `works` ストアへ保存→保存データを読み出してLab作品カードに表示、の順で10作品を使って検証する。変換エラー作品は保存せず、既存の内部ID・`bookmark`・`shelfId`・作者情報等を保持する。

version 7で `works` ストアと第9節の保存・カード表示UIを追加済み。保存条件は10作品すべての変換エラーなし・既存内部 `id` あり・有効な `newUrl` あり・保存先 `works` が空であること。保存には `add` を使い、既存レコードを上書きしない。Atom URL取得とiPhone実機でのDB version 7移行確認はこれから。

10作品の日付表示はiPhone実機で違和感なしを確認済み。ただし、Translator全項目・Atom URL・LabDB保存・カード表示の総合検証は未完了。

この工程はLab内だけで実施し、本番DB・本番本棚・Register・INDEX・Shortcut・GitHub Actionsには接続・変更しない。


### Atomスナップショットの制約

- リポジトリの `data/atom/author-feeds.json` は作者別Atomフィードの公開スナップショットだが、`scripts/atom/publish_author_atom_feeds.py` が直近7日分のエントリーに絞って保存する。
- 2026-11-19に今回の10作品を照合したところ、既存スナップショットでNコード一致を確認できたのは2作品。残り8作品はスナップショット内にエントリーがなかった。
- したがって、スナップショットで見つからないことをAtom上に作品がない証拠としない。対象作者のAtom取得方法・通常／R18のフィード選択・100件単位の扱いを別途確認する。
