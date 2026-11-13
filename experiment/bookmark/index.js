const demoWorks = [
  { workKey: "narou:lab-short", site: "なろう短編", title: "短編テスト作品", kind: "short" },
  { workKey: "narou:lab-long", site: "なろう長編", title: "長編テスト作品", kind: "long" },
  { workKey: "kakuyomu:lab", site: "カクヨム", title: "カクヨムテスト作品", kind: "long" },
  { workKey: "note:lab", site: "note", title: "noteテストマガジン", kind: "long" }
];

const host = document.getElementById("works");
const status = document.getElementById("status");
document.getElementById("dbName").textContent = "使用DB: " + BookmarkLabDB.DB_NAME;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function validateBookmarkUrl(work, raw) {
  let parsed;
  try { parsed = new URL(raw); } catch { throw new Error("有効なURLを入力してください"); }
  if (parsed.protocol !== "https:") throw new Error("URLはhttpsで始まる必要があります");

  const hostname = parsed.hostname.toLowerCase();
  const parts = parsed.pathname.split("/").filter(Boolean);

  const narouHost = hostname === "syosetu.com" || hostname.endsWith(".syosetu.com");
  const narouPath = parts.length >= 1 && parts.length <= 2
    && /^[a-z0-9]+$/i.test(parts[0])
    && (parts.length === 1 || /^\d+$/.test(parts[1]));

  const kakuyomuPath = hostname === "kakuyomu.jp"
    && parts.length === 4
    && parts[0] === "works"
    && parts[2] === "episodes";

  const notePath = hostname === "note.com"
    && parts.length === 2
    && /^n[a-z0-9]+$/i.test(parts[1]);

  const valid = work.workKey.startsWith("narou:")
    ? narouHost && narouPath
    : work.workKey.startsWith("kakuyomu:")
      ? kakuyomuPath
      : notePath;

  if (!valid) throw new Error("サイトとURLの形式が一致しません");
  return parsed.href;
}

async function refreshRecords() {
  try {
    const records = await BookmarkLabDB.getAllBookmarks();
    document.getElementById("records").textContent = JSON.stringify(records, null, 2);
  } catch (error) {
    document.getElementById("records").textContent = "読込エラー：" + error.message;
  }
}

async function render() {
  host.replaceChildren();
  for (const work of demoWorks) {
    const card = el("article", "work");
    card.append(el("div", "site", work.site), el("h3", "", work.title));
    const fields = el("div", "field");
    let url = null;
    let position = null;
    let readToggle = null;

    if (work.kind === "short") {
      const label = el("label", "", "読了状態");
      readToggle = el("input");
      readToggle.type = "checkbox";
      readToggle.setAttribute("aria-label", work.title + " の既読状態");
      fields.append(label, readToggle);
    } else {
      const urlLabel = el("label", "", "しおりURL（テスト用URLを入力）");
      url = el("input");
      url.type = "url";
      url.placeholder = "https://...";
      url.setAttribute("aria-label", work.title + " のしおりURL");
      const posLabel = el("label", "", "読書位置");
      position = el("input");
      position.type = "number";
      position.min = "1";
      position.step = "1";
      position.placeholder = "話数・記事順（不明なら空欄）";
      position.setAttribute("aria-label", work.title + " の読書位置");
      fields.append(urlLabel, url, posLabel, position);
    }

    const actions = el("div", "actions");
    const save = el("button", "", work.kind === "short" ? "既読状態を保存" : "しおりを保存");
    const read = el("button", "secondary", "保存内容を確認");
    const remove = el("button", "danger", "実験データを削除");
    actions.append(save, read, remove);
    const output = el("div", "muted", "未確認");

    save.addEventListener("click", async () => {
      try {
        let record;
        if (work.kind === "short") {
          record = {
            workKey: work.workKey,
            site: "narou",
            bookmark: null,
            isRead: readToggle.checked,
            updatedAt: new Date().toISOString()
          };
        } else {
          const savedUrl = validateBookmarkUrl(work, url.value.trim());
          const raw = position.value.trim();
          const value = raw === "" ? null : Number(raw);
          if (value !== null && (!Number.isSafeInteger(value) || value < 1)) {
            throw new Error("位置は1以上の整数、または空欄にしてください");
          }
          record = {
            workKey: work.workKey,
            site: work.workKey.split(":")[0],
            bookmark: { url: savedUrl, position: value },
            isRead: null,
            updatedAt: new Date().toISOString()
          };
        }
        await BookmarkLabDB.saveBookmark(record);
        output.textContent = work.kind === "short"
          ? (record.isRead ? "既読として保存済み" : "未読として保存済み")
          : "しおり保存済み：" + (record.bookmark.position ?? "位置不明");
        status.textContent = work.title + " の実験データを保存しました。";
        await refreshRecords();
      } catch (error) {
        status.textContent = "保存エラー：" + error.message;
      }
    });

    read.addEventListener("click", async () => {
      try {
        const record = await BookmarkLabDB.getBookmark(work.workKey);
        if (!record) {
          output.textContent = "未登録";
        } else if (work.kind === "short") {
          readToggle.checked = record.isRead === true;
          output.textContent = record.isRead ? "既読" : "未読";
        } else {
          if (record.bookmark?.url) url.value = record.bookmark.url;
          if (record.bookmark?.position != null) position.value = String(record.bookmark.position);
          output.textContent = record.bookmark ? JSON.stringify(record.bookmark) : "しおり未登録";
        }
        status.textContent = work.title + " の保存内容を読み込みました。";
      } catch (error) {
        status.textContent = "読込エラー：" + error.message;
      }
    });

    remove.addEventListener("click", async () => {
      try {
        await BookmarkLabDB.deleteBookmark(work.workKey);
        output.textContent = "実験データを削除しました";
        status.textContent = work.title + " の実験データを削除しました。";
        await refreshRecords();
      } catch (error) {
        status.textContent = "削除エラー：" + error.message;
      }
    });

    card.append(fields, actions, output);
    if (work.kind !== "short") {
      const resume = el("button", "secondary", "保存URLを直接開く");
      resume.type = "button";
      resume.addEventListener("click", async () => {
        const popup = window.open("about:blank", "_blank");
        if (!popup) {
          status.textContent = "新しいタブが開けませんでした。ブラウザのポップアップ設定を確認してください。";
          return;
        }
        try {
          const record = await BookmarkLabDB.getBookmark(work.workKey);
          if (!record?.bookmark?.url) {
            popup.close();
            status.textContent = "保存済みURLがありません。";
            return;
          }
          popup.location.replace(record.bookmark.url);
        } catch (error) {
          popup.close();
          status.textContent = "URL読込エラー：" + error.message;
        }
      });
      card.append(resume);
    }
    host.append(card);
  }
  await refreshRecords();
}

document.getElementById("refresh").addEventListener("click", refreshRecords);
render().catch(error => { status.textContent = "初期化エラー：" + error.message; });
