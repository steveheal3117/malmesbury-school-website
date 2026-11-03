// Finishes the GitHub sign-in and hands the token to the editor window.
function page(origin, status, payload) {
  const message = `authorization:github:${status}:${JSON.stringify(payload)}`;
  return new Response(
    `<!doctype html><html><body><p>Signing you in…</p><script>
(function () {
  var origin = ${JSON.stringify(origin)};
  var message = ${JSON.stringify(message)};
  function receive(e) {
    if (e.origin !== origin) return;
    window.opener.postMessage(message, origin);
    window.removeEventListener("message", receive, false);
    setTimeout(function () { window.close(); }, 500);
  }
  window.addEventListener("message", receive, false);
  window.opener.postMessage("authorizing:github", origin);
})();
</script></body></html>`,
    { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store",
                 "Set-Cookie": "cms_oauth_state=; Path=/api; Max-Age=0; HttpOnly; Secure; SameSite=Lax" } }
  );
}

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const origin = url.origin;
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const cookie = request.headers.get("Cookie") || "";
  const saved = (cookie.match(/(?:^|;\s*)cms_oauth_state=([^;]+)/) || [])[1];
  if (!code || !state || !saved || state !== saved) {
    return page(origin, "error", { message: "Sign-in could not be verified. Please close this window and try again." });
  }
  const res = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json", "User-Agent": "malmesbury-website-editor" },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
      redirect_uri: `${origin}/api/callback`,
    }),
  });
  const data = await res.json();
  if (!data.access_token) {
    return page(origin, "error", { message: data.error_description || "GitHub did not return a sign-in token." });
  }
  return page(origin, "success", { token: data.access_token, provider: "github" });
}
