const demoWorks = [
  { workKey: "narou:lab-short", site: "なろう短編（既読テスト）", title: "短編テスト作品", sampleUrl: "https://ncode.syosetu.com/n0000zz/" , kind: "short" },
  { workKey: "narou:lab-long", site: "なろう長編", title: "長編テスト作品", sampleUrl: "https://ncode.syosetu.com/n0000zy/" , kind: "long" },
  { workKey: "kakuyomu:lab", site: "カクヨム", title: "カクヨムテスト作品", sampleUrl: "https://kakuyomu.jp/works/00000000000000000000/episodes/00000000000000000000", kind: "long" },
  { workKey: "note:lab", site: "note", title: "noteテストマガジン", sampleUrl: "https://note.com/example/n000000000000", kind: "long" }
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

async function render() {
  host.replaceChildren();
  for (const work of demoWorks) {
    const card = el("article", "work");
    card.append(el("div", "site", work.site), el("h3", "", work.title));
    const url = el("input");
    url.type = "url";
    url.placeholder = "しおりURL（実験用）";
    url.value = work.sampleUrl;
    url.setAttribute("aria-label", work.title + " のしおりURL");
    const position = el("input");
    position.type = "number";
    position.min = "1";
    position.step = "1";
    position.placeholder = work.kind === "short" ? "短編は位置を使わない" : "読書位置（話数・記事順）";
    position.disabled = work.kind === "short";
    position.setAttribute("aria-label", work.title + " の読書位置");
    const fields = el("div", "field");
    fields.append(el("label", "", "保存URL"), url, el("label", "", "位置"), position);
    const actions = el("div", "actions");
    const save = el("button", "", "しおりを保存");
    const read = el("button", "secondary", "保存内容を確認");
    const remove = el("button", "danger", "実験データを削除");
    actions.append(save, read, remove);
    const output = el("div", "muted", "しおり未確認");
    save.addEventListener("click", async () => {
      try {
        const parsed = new URL(url.value);
        const allowed = work.workKey.startsWith("narou:") ? parsed.hostname.endsWith("syosetu.com") :
          work.workKey.startsWith("kakuyomu:") ? parsed.hostname === "kakuyomu.jp" :
          parsed.hostname === "note.com";
        if (!allowed) throw new Error("作品サイトとURLのドメインが一致しません");
        const raw = position.value.trim();
        const value = raw === "" ? null : Number(raw);
        if (value !== null && (!Number.isInteger(value) || value < 1)) throw new Error("位置は1以上の整数、または空欄にしてください");
        const record = { workKey: work.workKey, site: work.workKey.split(":")[0], bookmark: { url: parsed.href, position: work.kind === "short" ? null : value }, isRead: work.kind === "short" ? true : null, updatedAt: new Date().toISOString() };
        await BookmarkLabDB.saveBookmark(record);
        output.textContent = "保存済み：" + (record.bookmark.position ?? "位置不明");
        status.textContent = work.title + " の実験用しおりを保存しました。";
        await refreshRecords();
      } catch (error) { status.textContent = "保存エラー：" + error.message; }
    });
    read.addEventListener("click", async () => {
      try {
        const record = await BookmarkLabDB.getBookmark(work.workKey);
        output.textContent = record ? JSON.stringify(record.bookmark) : "しおり未登録";
        status.textContent = work.title + " の保存内容を読み込みました。";
      } catch (error) { status.textContent = "読込エラー：" + error.message; }
    });
    remove.addEventListener("click", async () => {
      try {
        await BookmarkLabDB.deleteBookmark(work.workKey);
        output.textContent = "実験データを削除しました";
        status.textContent = work.title + " の実験用データを削除しました。";
        await refreshRecords();
      } catch (error) { status.textContent = "削除エラー：" + error.message; }
    });
    const resume = el("a", "resume", "保存URLを直接開く（保存後）");
    resume.href = "#";
    resume.addEventListener("click", async event => {
      event.preventDefault();
      const record = await BookmarkLabDB.getBookmark(work.workKey);
      if (!record?.bookmark?.url) { status.textContent = "保存済みURLがありません。"; return; }
      window.open(record.bookmark.url, "_blank", "noopener");
    });
    card.append(fields, actions, output, resume);
    host.append(card);
  }
  await refreshRecords();
}

async function refreshRecords() {
  try {
    const records = await BookmarkLabDB.getAllBookmarks();
    document.getElementById("records").textContent = JSON.stringify(records, null, 2);
  } catch (error) { document.getElementById("records").textContent = "読込エラー：" + error.message; }
}
document.getElementById("refresh").addEventListener("click", refreshRecords);
render().catch(error => { status.textContent = "初期化エラー：" + error.message; });
