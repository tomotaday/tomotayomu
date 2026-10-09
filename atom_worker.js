/**
 * ともたよむ Atom取得 Worker（本番用・配置準備版）
 *
 * Worker の編集画面へこのファイル全体を一度だけ貼り付けて保存する。
 * 呼び出し例:
 *   /feed?type=novel&id=1826746
 *   /feed?type=novel&id=x8754cq
 *   /feed?type=activity&id=x8754cq
 *
 * 任意URL取得は許可せず、なろう公式Atomエンドポイントだけを取得する。
 * 多数作者を一気に処理せず、呼び出し側で順番に実行すること。
 */
const ALLOWED_ORIGINS = [
  "https://tomotaday.github.io",
  "http://localhost:8787",
  "http://localhost:5173"
];

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGINS.includes(origin)
      ? origin
      : ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin"
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...corsHeaders(origin)
    }
  });
}

function validAuthorId(value) {
  return /^[0-9]{1,10}$/.test(value) || /^x[0-9a-z]{1,12}$/i.test(value);
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (request.method !== "GET") {
      return json({ ok: false, error: "GET only" }, 405, origin);
    }
    if (url.pathname === "/health") {
      return json({ ok: true, service: "tomotayomu-atom", feedPath: "/feed" }, 200, origin);
    }
    if (url.pathname !== "/feed") {
      return json({ ok: false, error: "Use /feed?type=novel|activity&id=AUTHOR_ID" }, 404, origin);
    }

    const type = url.searchParams.get("type") || "";
    const id = (url.searchParams.get("id") || "").trim();
    if (!["novel", "activity"].includes(type)) {
      return json({ ok: false, error: "type must be novel or activity" }, 400, origin);
    }
    if (!validAuthorId(id)) {
      return json({ ok: false, error: "Invalid author ID" }, 400, origin);
    }

    // XIDはR18作者用。数字IDは通常作者用。
    const isXid = /^x/i.test(id);
    if (type === "activity" && !isXid && !/^[0-9]+$/.test(id)) {
      return json({ ok: false, error: "Invalid activity author ID" }, 400, origin);
    }

    const endpoint = type === "novel" ? "writernovel" : "writerblog";
    const target = `https://api.syosetu.com/${endpoint}/${encodeURIComponent(id)}.Atom`;

    try {
      const upstream = await fetch(target, {
        headers: {
          "Accept": "application/atom+xml, application/xml, text/xml;q=0.9",
          "User-Agent": "tomotayomu-atom/1.0"
        },
        cf: { cacheTtl: 0, cacheEverything: false }
      });
      const body = await upstream.text();
      return new Response(body, {
        status: upstream.status,
        headers: {
          "Content-Type": upstream.headers.get("Content-Type") || "application/atom+xml; charset=UTF-8",
          "Cache-Control": "no-store",
          "X-Upstream-Status": String(upstream.status),
          ...corsHeaders(origin)
        }
      });
    } catch (error) {
      return json({ ok: false, error: String(error?.message || error) }, 502, origin);
    }
  }
};
