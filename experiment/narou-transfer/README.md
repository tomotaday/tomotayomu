# なろうトランスファー Lab

各サイトの作品データを、ともたよむの共通 `works` 形式へ受け渡すための独立実験環境。現在は、なろう全年齢API・R18 APIの取得データを調査し、共通形式へ変換するTranslatorの検証を行う。

## 現在の構成

- 実験ページ：`narou_transfer_lab.html`
- LabDB：`tomotaYomuNarouTranslatorLabDB` version 6
- Object Store：
  - `sourceWorks`（keyPath: `id`）：初期サンプル原本用ストア。現行画面のTranslatorプレビューでは参照・更新しない
  - `cleanWorks`（keyPath: `id`）：整理版の既存作品データ
  - `labShelves`（keyPath: `id`）：Lab内の棚情報
  - `apiRawResponses`（keyPath: `id`）：全年齢API・R18 APIから取得した生JSON、API種別、取得日時
- 初期検証データ：なろう10作品（通常API 8件、R18 API 2件の生JSONを確認済み）
- 生APIデータは `apiRawResponses` に原形を保持する。共通形式への変換結果は現在、プレビューとしてメモリ上に生成するだけで、DBへ保存しない

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
- APIから元URLは取得できない。Shortcut連携が未実装のため、既存URLがない場合はURLを作らず、未設定の警告を表示する
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

- LabDB version 6。生APIレスポンスを保存する `apiRawResponses` を使用
- 通常API8作品・R18 API2作品の生JSONを取得し、項目監査を実施
- 全10作品の生JSON一括コピー機能を実装
- 共通worksへの読み取り専用Translator変換プレビューを実装
- 変換結果の一括コピーを実装
- 変換関数の単体確認で、既存の内部ID・URL・棚・しおり・検索除外・作者ID・作者かな情報の保持、キーワード分割、status変換、genresの元型保持を確認
- GitHubコード・JavaScript構文確認済み。commit：`3660d4099311b178bab5894932abb2871c1e39cb`
- **iPhone実機でのTranslatorプレビュー実行・10作品の実出力確認は未確認。** 実機確認済みとは扱わない
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

特に、通常APIの既存作者IDが上書きされないこと、R18の手動作者IDが維持されること、URLが生成されないこと、API空値が既存値を消さないことを確認する。

## 次の工程

1. iPhone実機でTranslator変換プレビューを実行し、10作品の出力を確認する
2. 出力と設計記録の対応表を照合し、誤変換・欠落・警告を修正する
3. Shortcutから元URLをTranslatorへ渡す方法を別途設計する（URLを生成・推測しない）
4. 必要に応じてAPI標本を増やし、属性フラグ等の網羅性を調べる
5. 他サイトTranslator（カクヨム・note等）は、なろうの検証完了後に別々に設計する
6. Register・本番接続・本番導入は、Lab検証とは別工程として判断する
