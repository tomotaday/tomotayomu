const DB_NAME = "tomotaYomuBookmarkLabDB";
const DB_VERSION = 1;
const STORE_NAME = "bookmarks";

function openBookmarkLabDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "workKey" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("実験用DBを開けません"));
    request.onblocked = () => reject(new Error("実験用DBが別画面で使用中です"));
  });
}

async function saveBookmark(record) {
  const db = await openBookmarkLabDB();
  try {
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).put(record);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error || new Error("保存に失敗しました"));
      tx.onabort = () => reject(tx.error || new Error("保存が中断されました"));
    });
  } finally {
    db.close();
  }
}

async function getBookmark(workKey) {
  const db = await openBookmarkLabDB();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const request = tx.objectStore(STORE_NAME).get(workKey);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error("読込に失敗しました"));
    });
  } finally {
    db.close();
  }
}

async function getAllBookmarks() {
  const db = await openBookmarkLabDB();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const request = tx.objectStore(STORE_NAME).getAll();
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error || new Error("一覧取得に失敗しました"));
    });
  } finally {
    db.close();
  }
}

async function deleteBookmark(workKey) {
  const db = await openBookmarkLabDB();
  try {
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).delete(workKey);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error || new Error("削除に失敗しました"));
      tx.onabort = () => reject(tx.error || new Error("削除が中断されました"));
    });
  } finally {
    db.close();
  }
}

window.BookmarkLabDB = { DB_NAME, saveBookmark, getBookmark, getAllBookmarks, deleteBookmark };
