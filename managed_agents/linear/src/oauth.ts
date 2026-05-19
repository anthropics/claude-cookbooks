import { chmodSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

const LINEAR_CLIENT_ID = process.env.LINEAR_CLIENT_ID!;
const LINEAR_CLIENT_SECRET = process.env.LINEAR_CLIENT_SECRET!;
const BASE_URL = process.env.BASE_URL || `http://localhost:${process.env.PORT || 3000}`;
const REDIRECT_URI = `${BASE_URL}/oauth/callback`;

type TokenEntry = { accessToken: string; refreshToken: string; expiresAt: number };
const TOKEN_FILE = join(import.meta.dir, "..", ".linear-tokens.json");

function load(): Map<string, TokenEntry> {
  try {
    return new Map(Object.entries(JSON.parse(readFileSync(TOKEN_FILE, "utf-8"))));
  } catch {
    return new Map();
  }
}
function save(m: Map<string, TokenEntry>) {
  // Token file holds Linear OAuth access + refresh tokens per workspace.
  // Restrict to owner-only on POSIX so a co-tenant on the same host can't
  // recover them. The `mode` option applies on initial create; chmod after
  // handles the pre-existing-file (overwrite) case. Try/catch wraps chmod
  // because Windows does not support POSIX modes.
  writeFileSync(TOKEN_FILE, JSON.stringify(Object.fromEntries(m), null, 2), { mode: 0o600 });
  try {
    chmodSync(TOKEN_FILE, 0o600);
  } catch {
    // Windows fallback.
  }
}
const tokens = load();

export function handleOAuthAuthorize(): Response {
  const params = new URLSearchParams({
    client_id: LINEAR_CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: "code",
    scope: "read,write,app:assignable,app:mentionable",
    actor: "app",
  });
  return Response.redirect(`https://linear.app/oauth/authorize?${params}`);
}

export async function handleOAuthCallback(url: URL): Promise<Response> {
  const code = url.searchParams.get("code");
  if (!code) return new Response("Missing code", { status: 400 });

  const tok = await exchange({ grant_type: "authorization_code", code, redirect_uri: REDIRECT_URI });

  const orgRes = await fetch("https://api.linear.app/graphql", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${tok.access_token}` },
    body: JSON.stringify({ query: "{ organization { id name } }" }),
  });
  const org = ((await orgRes.json()) as any).data.organization;

  tokens.set(org.id, {
    accessToken: tok.access_token,
    refreshToken: tok.refresh_token,
    expiresAt: Date.now() + tok.expires_in * 1000,
  });
  save(tokens);

  console.log(`[oauth] installed in "${org.name}" (${org.id})`);
  return new Response(
    `<h1>Agent installed in ${org.name}</h1><p>You can now @mention it in Linear.</p>`,
    { headers: { "Content-Type": "text/html" } },
  );
}

export async function getAccessToken(orgId: string): Promise<string> {
  const entry = tokens.get(orgId);
  if (!entry) throw new Error(`No Linear token for org ${orgId}`);

  if (entry.expiresAt - Date.now() < 5 * 60 * 1000) {
    const tok = await exchange({ grant_type: "refresh_token", refresh_token: entry.refreshToken });
    entry.accessToken = tok.access_token;
    entry.refreshToken = tok.refresh_token;
    entry.expiresAt = Date.now() + tok.expires_in * 1000;
    save(tokens);
  }
  return entry.accessToken;
}

async function exchange(params: Record<string, string>) {
  const res = await fetch("https://api.linear.app/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: LINEAR_CLIENT_ID,
      client_secret: LINEAR_CLIENT_SECRET,
      ...params,
    }),
  });
  if (!res.ok) throw new Error(`Linear OAuth: ${await res.text()}`);
  return (await res.json()) as { access_token: string; refresh_token: string; expires_in: number };
}
