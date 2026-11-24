# GitHub PAT設定記録：ともたよむ Atom更新Shortcut

最終確認日：2026-11-25  
対象リポジトリ：`tomotaday/tomotayomu`  
対象PAT名：`tomotayomu-actions-shortcut`  
用途：iPhoneショートカットからGitHub Actionsを起動し、Atom更新用の作者一覧ファイルを受け渡す。

## 1. PATの基本設定

| 項目 | 設定 |
|---|---|
| トークン種別 | Fine-grained personal access token |
| トークン名 | `tomotayomu-actions-shortcut` |
| Resource owner | `tomotaday` |
| Repository access | Only select repositories |
| 対象リポジトリ | `tomotaday/tomotayomu` |
| Expiration | 有効期限なし |
| User permissions | なし |

## 2. Repository permissions（2026-11-25更新後）

| 権限 | 設定 |
|---|---|
| Actions | Read and write |
| Contents | Read and write |
| Metadata | Read-only（必須） |

2026-11-25、既存PATの編集画面で `Contents` を追加し、`Read and write` に設定してUpdateを実行。更新後の詳細画面で、MetadataのReadと、Actions and codeのRead and Writeが表示されることを確認した。

**重要：** ActionsのRead and writeだけでは、ShortcutからContents APIでリポジトリ内ファイルを作成・更新できない。ファイル書き込みにはContentsのRead and writeが必要。GitHub Actionsワークフロー内の `permissions: contents: write` はActions実行時のGITHUB_TOKENに対する設定であり、Shortcutが使うこのPATの権限とは別。

## 3. 今回の障害調査との関係

### GitHub Actions dispatchのサイズ超過

2026-11-25のiPhone実機画面で、作者一覧JSONをActionsの `workflow_dispatch.inputs.author_list_json` に渡す従来方式について、次の表示を確認。

- 作者数：1,264人
- JSON本体：56,683文字／56,683バイト
- GitHub送信形式：66,856文字／66,856バイト
- 応答：HTTP 422、`inputs are too large.`

これはPATのContents権限とは別の問題。JSONをworkflow_dispatchの入力として直接渡す方式はサイズ超過で拒否されている。

### Contents APIへの診断用PUT

診断用ファイル `data/author-list-diagnostic.json` へのPUTを試した際、権限追加前は `Resource not accessible by personal access token` が返った。

その後、上記のとおりPATにContents: Read and writeを追加し、GitHub画面で設定反映を確認した。

**未確認：** Contents権限追加後の診断用PUT再実行結果。成功（通常はHTTP 201 Created）を確認するまでは、Shortcutからのファイル書き込み成功とは扱わない。

## 4. 次の確認

1. 実験用Shortcutでのみ、`data/author-list-diagnostic.json` へのPUTを再実行する。
2. 応答がHTTP 201 Createdとなり、GitHub上に診断用ファイルが作成されたことを確認する。
3. 成功確認後、診断用ファイルを削除する。
4. その後に、作者一覧JSONをファイルとして保存してから、入力なしで `publish-author-atom-feeds.yml` を起動する方式を設計する。本番ファイル `data/author-list.json` は、設計・検証・明示確認が済むまで更新しない。

## 5. 秘密情報の取り扱い

- PATの実際の値はこの資料室、GitHub Pagesで公開されるファイル、スクリーンショット、チャット本文へ記録しない。
- PATの実値はiPhoneショートカットのキーチェーンに保存する。ショートカット内の参照名は `GitHub_PAT`、実行時変数名は `token`。
- パスワード管理ツールにはPAT本体を安全な秘密情報として保管し、この資料には設定情報のみを記録する。
- このPATは `tomotaday/tomotayomu` のみを対象とする。不要なRepository permissionsやUser permissionsを追加しない。
