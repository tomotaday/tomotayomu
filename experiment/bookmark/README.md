# しおりシステム実験室

本番アプリ・本番DBから独立した試験環境。

## 安全境界
- 使用DB: `tomotaYomuBookmarkLabDB`（本番DBとは別名）
- 使用ストア: `bookmarks`
- 本番 `tomotaYomuWorksDB` / 旧DB / localStorage / Shortcut は読み書きしない
- 外部サイトの目次取得や本番データ移行は、別途設計・承認するまで行わない
- テスト作品は画面内の仮データのみ。実作品を自動取込しない

## 現在の段階
1. 独立DBへの保存・読込・削除の基本動作
2. 保存URLをそのまま開く動作
3. サイト別の位置表現の確認
4. INDEXカード表示との接続
5. 目次更新時の位置再評価
6. 本番移行設計（最後に判断）

## 保存モデル案
```js
{
  workKey: "site:work-id",
  site: "narou | kakuyomu | note",
  bookmark: {
    url: "",
    position: null
  },
  updatedAt: ""
}
```

位置の意味はサイト別に解釈する。noteは読書順（古い記事から新しい記事）で扱う。短編なろうの既読状態は別機能として保持し、長編のしおりと混同しない。
