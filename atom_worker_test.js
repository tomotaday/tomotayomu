/**
 * ともたよむ Atom取得実験用 Cloudflare Worker
 * 
 * 本番 index.html からは参照しません。
 * まずは Narou Atom を取得し、
 * HTTP status / headers / raw Atom body をブラウザへ返すだけの実験です。
 *
 * 対象:
 *   通常作者・作品更新:
 *   https://api.syosetu.com/writernovel/{authorId}.Atom
 *
 * 今回の試験対象:
 *   三香 / authorId 1826746
 *
 * Worker URL:
 *   https://api.syosetu.com/ を直接ブラウザから叩くのではなく、
 *   この Worker が取得してブラウザへ返します。
 */

const ALLOWED_ORIGINS = [
  "https://tomotaday.github.io",
  "http://localhost:8787",
  "http://localhost:5173",
];

function corsHeaders(origin) {
  const allowOrigin = ALLOWED_ORIGINS.includes(origin)
    ? origin
    : ALLOWED_ORIGINS[0];

  return {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function jsonResponse(data, status, origin) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(origin),
    },
  });
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(origin),
      });
    }

    if (request.method !== "GET") {
      return jsonResponse({ ok: false, error: "GET only" }, 405, origin);
    }

    /*
     * 今回は安全確認のため、取得先を固定。
     * 任意URLを受け取る汎用CORS Proxyにはしない。
     */
    const target =
      "https://api.syosetu.com/writernovel/1826746.Atom";

    try {
      const upstream = await fetch(target, {
        headers: {
          "User-Agent": "tomotayomu-atom-test/1.0",
          "Accept": "application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
      });

      const body = await upstream.text();

      return new Response(body, {
        status: upstream.status,
        headers: {
          "Content-Type":
            upstream.headers.get("Content-Type") ||
            "application/atom+xml; charset=UTF-8",
          "X-Upstream-Status": String(upstream.status),
          "X-Upstream-ETag": upstream.headers.get("ETag") || "",
          "X-Upstream-Last-Modified":
            upstream.headers.get("Last-Modified") || "",
          "X-Upstream-Cache-Control":
            upstream.headers.get("Cache-Control") || "",
          ...corsHeaders(origin),
        },
      });
    } catch (error) {
      return jsonResponse(
        {
          ok: false,
          error: String(error?.message || error),
        },
        502,
        origin,
      );
    }
  },
};
