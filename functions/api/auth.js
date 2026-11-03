// Starts the GitHub sign-in for the staff website editor (/admin).
// Needs two Cloudflare environment variables: GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.
export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const state = crypto.randomUUID();
  const github = new URL("https://github.com/login/oauth/authorize");
  github.searchParams.set("client_id", env.GITHUB_CLIENT_ID);
  github.searchParams.set("redirect_uri", `${url.origin}/api/callback`);
  github.searchParams.set("scope", "public_repo");
  github.searchParams.set("state", state);
  return new Response(null, {
    status: 302,
    headers: {
      Location: github.toString(),
      "Set-Cookie": `cms_oauth_state=${state}; Path=/api; HttpOnly; Secure; SameSite=Lax; Max-Age=600`,
      "Cache-Control": "no-store",
    },
  });
}
