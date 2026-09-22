import { env } from "cloudflare:workers";
import { EMPTY_SPOTIFY_FEED, cachedSpotifyPlaylist, inactiveSpotifyFeed, playlistCacheFromStorage, recentPlaylistContexts, record, songFromSpotify, type SpotifyFeed, type SpotifyPlaylistCache } from "../components/spotifyData";
import { SPOTIFY_HISTORY_TTL_MS, SPOTIFY_IDLE_REFRESH_MS, SPOTIFY_PLAYLIST_TTL_MS, spotifyRefreshInterval, spotifyRetryDelay } from "../components/spotifyRefresh";
import { SPOTIFY_OWNER, SPOTIFY_SCOPES, digest, localSpotifyRequest, ownerMatches, randomToken, seal, spotifyCallbackAllowed, spotifyOAuthRequest, spotifyStateCookie, unseal } from "./spotifySecurity";

const API = "https://api.spotify.com/v1";
const STATE_COOKIE = "spotify_connect_state";
const ATTEMPT_TTL = 600_000;
type Stored = { value: string; expires_at: number };
type Tokens = { access: string; refresh: string; expiresAt: number; generation: string; accountId?: string };
class SpotifyError extends Error {
  constructor(public code: "unavailable" | "reconnect" | "rate_limit" | "quota_limit", public retryAfter = SPOTIFY_IDLE_REFRESH_MS, public upstreamStatus = 0, public endpoint = "") { super(code); }
}
export function logSpotifyFailure(error: unknown) {
  // Deliberately omit upstream bodies, URLs, query strings, tokens and cookies.
  console.warn("[spotify]", error instanceof SpotifyError
    ? { code: error.code, status: error.upstreamStatus, endpoint: error.endpoint }
    : { code: "local_failure", kind: error instanceof Error ? error.name : "unknown" });
}
function config() {
  const { SPOTIFY_CLIENT_ID: clientId, SPOTIFY_CLIENT_SECRET: secret, SPOTIFY_REDIRECT_URI: redirect, SPOTIFY_USER_ID: owner } = env;
  if (!clientId || !secret || !spotifyCallbackAllowed(redirect, process.env.NODE_ENV === "development") || owner !== SPOTIFY_OWNER || !env.DB) throw new Error("Spotify configuration unavailable");
  return { clientId, secret, redirect, db: env.DB };
}
export function spotifyConfigured() { try { config(); return true; } catch { return false; } }
export function spotifyRequestAllowed(request: Request) {
  return spotifyOAuthRequest(request, env.SPOTIFY_REDIRECT_URI, process.env.NODE_ENV === "development");
}
async function get(key: string) { return config().db.prepare("SELECT value, expires_at FROM spotify_state WHERE key = ?").bind(key).first<Stored>(); }
async function put(key: string, value: string, expiresAt = 0) {
  await config().db.prepare("INSERT INTO spotify_state (key, value, expires_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at").bind(key, value, expiresAt).run();
}
function tokenData(value: unknown): Tokens {
  const data = record(value);
  if (typeof data.access !== "string" || typeof data.refresh !== "string" || typeof data.expiresAt !== "number" || typeof data.generation !== "string") throw new Error("Invalid stored connection");
  return { access: data.access, refresh: data.refresh, expiresAt: data.expiresAt, generation: data.generation, accountId: typeof data.accountId === "string" ? data.accountId : undefined };
}
async function connection() {
  const row = await get("tokens");
  if (!row) return null;
  return { ...tokenData(await unseal(row.value, config().secret)), sealed: row.value };
}

// Fixed Spotify endpoints only; bounded bodies, timeouts and no upstream error-body logging.
async function spotifyFetch(url: string, init: RequestInit = {}): Promise<unknown> {
  // workerd supports manual, not redirect:error. Reject 3xx below; never forward credentials.
  const response = await fetch(url, { ...init, cache: "no-store", redirect: "manual", signal: AbortSignal.timeout(10_000) });
  if (response.status === 204 || response.status === 404) return null;
  if (!response.ok) {
    if (response.status === 429) {
      const body = await boundedSpotifyJson(response, 16_384).catch(() => null);
      const reason = record(record(body).error).reason;
      throw new SpotifyError(reason === "QUOTA_EXCEEDED" ? "quota_limit" : "rate_limit",
        spotifyRetryDelay(response.headers.get("retry-after"), reason), 429, new URL(url).pathname);
    }
    throw new SpotifyError(response.status === 401 || response.status === 400 ? "reconnect" : "unavailable", SPOTIFY_IDLE_REFRESH_MS, response.status, new URL(url).pathname);
  }
  return boundedSpotifyJson(response);
}
async function boundedSpotifyJson(response: Response, limit = 1_000_000): Promise<unknown> {
  if (!response.body) return null;
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = []; let length = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read(); if (done) break;
      length += value.byteLength;
      if (length > limit) { await reader.cancel(); throw new SpotifyError("unavailable"); }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(length); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder().decode(bytes));
}
function api(path: string, access: string) { return spotifyFetch(`${API}${path}`, { headers: { Authorization: `Bearer ${access}` } }); }
async function tokenRequest(body: URLSearchParams) {
  const { clientId, secret } = config();
  return record(await spotifyFetch("https://accounts.spotify.com/api/token", {
    method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded", Authorization: `Basic ${btoa(`${clientId}:${secret}`)}` }, body,
  }));
}
function tokensFromResponse(data: Record<string, unknown>, previous?: Tokens): Tokens {
  if (typeof data.access_token !== "string" || typeof data.expires_in !== "number") throw new SpotifyError("unavailable");
  const refresh = typeof data.refresh_token === "string" ? data.refresh_token : previous?.refresh;
  if (!refresh) throw new SpotifyError("reconnect");
  return { access: data.access_token, refresh, expiresAt: Date.now() + data.expires_in * 1000, generation: previous?.generation ?? randomToken(), accountId: previous?.accountId };
}
async function accessToken(stored: NonNullable<Awaited<ReturnType<typeof connection>>>) {
  if (stored.expiresAt > Date.now() + 60_000) return stored.access;
  const refreshed = tokensFromResponse(await tokenRequest(new URLSearchParams({ grant_type: "refresh_token", refresh_token: stored.refresh })), stored);
  // The feed lease serializes refreshes; this compare-and-swap also protects a new connection.
  const result = await config().db.prepare("UPDATE spotify_state SET value = ? WHERE key = 'tokens' AND value = ?")
    .bind(await seal(refreshed, config().secret), stored.sealed).run();
  if (!result.meta.changes) throw new SpotifyError("unavailable");
  return refreshed.access;
}

export const PRIVATE_HEADERS = { "Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY" };
function cookie(value: string, maxAge: number) { return spotifyStateCookie(value, maxAge, process.env.NODE_ENV === "development"); }
function readCookie(request: Request) {
  const value = request.headers.get("cookie")?.split(";").map((part) => part.trim()).find((part) => part.startsWith(`${STATE_COOKIE}=`))?.slice(STATE_COOKIE.length + 1);
  return value && /^[A-Za-z0-9_-]{43}$/.test(value) ? value : null;
}
function html(body: string, status = 200, setCookie?: string) {
  return new Response(`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Connect Spotify · Brian Zeng</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#171717;color:#eee;font:16px/1.65 system-ui}main{max-width:440px;margin:24px;padding:32px;border:1px solid #ffffff30;border-radius:24px;background:#ffffff09}h1{font-size:25px;line-height:1.2}p{color:#c8c8c8}a{color:#eee}button{font:inherit;border:1px solid #ffffff50;border-radius:10px;padding:10px 18px;background:#eee;color:#171717;cursor:pointer}button.secondary{background:transparent;color:#ccc;margin-top:14px;font-size:14px}.mark{width:100px;margin-bottom:14px}.note{font-size:13px}</style><main>${body}</main></html>`, {
    status, headers: { ...PRIVATE_HEADERS, "Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'", ...(setCookie ? { "Set-Cookie": setCookie } : {}) },
  });
}
export function connectionError(message = "The connection could not be completed. Please try again.", status = 400) {
  // Callers pass fixed messages, never Spotify response bodies or query parameters.
  return html(`<h1>Spotify connection</h1><p>${message}</p><a href="/api/spotify/connect">Back to connection setup</a>`, status, cookie("", 0));
}
export async function connectPage() {
  if (!spotifyConfigured()) return connectionError("Spotify settings are not ready. Add the Spotify app credentials to this environment before connecting.", 503);
  const nonce = randomToken(), verifier = randomToken(), now = Date.now();
  await config().db.prepare("DELETE FROM spotify_state WHERE key LIKE 'oauth:%' AND expires_at < ?").bind(now).run();
  // A public setup page must not grow the attempts table without a bound.
  const issued = await config().db.prepare("INSERT INTO spotify_state (key, value, expires_at) SELECT ?, ?, ? WHERE (SELECT COUNT(*) FROM spotify_state WHERE key LIKE 'oauth:%') < 64")
    .bind(`oauth:${await digest(nonce)}`, await seal({ verifier }, config().secret), now + ATTEMPT_TTL).run();
  if (!issued.meta.changes) return connectionError("Too many connection attempts. Please try again in a few minutes.", 429);
  const connected = Boolean(await get("tokens"));
  return html(`<img class="mark" src="/spotify/wordmark-white.svg" alt="Spotify"><h1>${connected ? "Spotify is connected" : "Connect your listening"}</h1><p>This connects Brian’s account to the desktop widget. Your current or latest song and recently played public playlists will be visible to visitors.</p><p>Read-only access. No playback controls. Private Sessions are not shown.</p><p><a href="/api/spotify/authorize?state=${nonce}" style="display:inline-block;background:#eee;color:#171717;padding:10px 18px;border-radius:10px;text-decoration:none">${connected ? "Reconnect Spotify" : "Continue to Spotify"}</a></p>${connected && process.env.NODE_ENV === "development" ? `<form method="post"><input type="hidden" name="state" value="${nonce}"><button class="secondary" name="action" value="disconnect">Disconnect and clear widget data</button></form>` : ""}<p class="note">Only account 12127274651 can connect. Credentials stay on the server.</p><a href="/desktop">Back to desktop</a>`, 200, cookie(nonce, ATTEMPT_TTL / 1000));
}
export async function authorizeGet(request: Request) {
  const nonce = readCookie(request);
  if (!nonce || new URL(request.url).searchParams.get("state") !== nonce) return connectionError("Please start from the connection page in this browser.", 403);
  const attempt = await get(`oauth:${await digest(nonce)}`);
  if (!attempt || attempt.expires_at < Date.now()) return connectionError("The connection request expired. Please start again.");
  return authorizationRedirect(nonce, attempt);
}
async function authorizationRedirect(nonce: string, attempt: Stored) {
  const transaction = record(await unseal(attempt.value, config().secret));
  if (typeof transaction.verifier !== "string") return connectionError();
  const params = new URLSearchParams({ client_id: config().clientId, response_type: "code", redirect_uri: config().redirect, scope: SPOTIFY_SCOPES, state: nonce, code_challenge_method: "S256", code_challenge: await digest(transaction.verifier) });
  return new Response(null, { status: 303, headers: { ...PRIVATE_HEADERS, Location: `https://accounts.spotify.com/authorize?${params}` } });
}
export async function connectPost(request: Request) {
  // An OAuth nonce proves browser continuity, not ownership. Never expose the
  // local disconnect action publicly, even if a caller bypasses the route guard.
  if (!localSpotifyRequest(request, process.env.NODE_ENV === "development")) return new Response("Not found", { status: 404, headers: PRIVATE_HEADERS });
  if (Number(request.headers.get("content-length") ?? 0) > 2048) return connectionError();
  const form = await request.formData(), nonce = readCookie(request);
  if (!nonce || form.get("state") !== nonce) return connectionError("The connection request expired. Please start again.");
  const key = `oauth:${await digest(nonce)}`, attempt = await get(key);
  if (!attempt || attempt.expires_at < Date.now()) return connectionError();
  if (form.get("action") === "disconnect") {
    await config().db.batch([
      config().db.prepare("DELETE FROM spotify_state WHERE key IN ('tokens','feed','history','playlists','lease','backoff')"),
      config().db.prepare("DELETE FROM spotify_state WHERE key = ?").bind(key),
    ]);
    return html('<h1>Spotify disconnected</h1><p>Your connection and cached widget data have been cleared.</p><a href="/desktop">Back to desktop</a>', 200, cookie("", 0));
  }
  if (form.get("action") !== "connect") return connectionError();
  return authorizationRedirect(nonce, attempt);
}
export async function connectCallback(request: Request) {
  const url = new URL(request.url), nonce = readCookie(request);
  if (!nonce || url.searchParams.get("state") !== nonce) return connectionError("The connection request expired or did not match this browser. Please start again.");
  // Consume before exchanging: callback replay and parallel requests fail closed.
  const attempt = await config().db.prepare("DELETE FROM spotify_state WHERE key = ? AND expires_at > ? RETURNING value, expires_at")
    .bind(`oauth:${await digest(nonce)}`, Date.now()).first<Stored>();
  if (!attempt || url.searchParams.has("error")) return connectionError("Spotify was not connected. You can try again when ready.");
  const transaction = record(await unseal(attempt.value, config().secret));
  const code = url.searchParams.get("code");
  if (!code || code.length > 4096 || typeof transaction.verifier !== "string") return connectionError();
  const response = await tokenRequest(new URLSearchParams({ grant_type: "authorization_code", code, redirect_uri: config().redirect, code_verifier: transaction.verifier }));
  const granted = typeof response.scope === "string" ? response.scope.split(" ") : [];
  if (!SPOTIFY_SCOPES.split(" ").every((scope) => granted.includes(scope))) return connectionError("Spotify did not grant the read-only access needed for the widget.");
  const tokens = tokensFromResponse(response);
  const profile = record(await api("/me", tokens.access));
  const previous = await connection();
  if (!ownerMatches(profile, previous?.accountId)) return connectionError("Please sign in to Brian’s Spotify account. The existing connection has not been changed.", 403);
  tokens.accountId = typeof profile.account_id === "string" ? profile.account_id : undefined;
  await config().db.batch([
    config().db.prepare("INSERT INTO spotify_state (key, value, expires_at) VALUES ('tokens', ?, 0) ON CONFLICT(key) DO UPDATE SET value = excluded.value").bind(await seal(tokens, config().secret)),
    config().db.prepare("DELETE FROM spotify_state WHERE key IN ('feed','history','playlists','backoff')"),
  ]);
  // Redirect immediately so the authorization code is removed from the visible URL.
  return new Response(null, { status: 303, headers: { ...PRIVATE_HEADERS, "Set-Cookie": cookie("", 0), Location: "/api/spotify/connect?connected=1" } });
}

async function readFeed(): Promise<SpotifyFeed | null> {
  const cache = await get("feed");
  return cache ? JSON.parse(cache.value) : null;
}
async function putForConnection(key: string, value: string, generation: string, expiresAt = 0) {
  const latest = await connection();
  if (!latest || latest.generation !== generation) return false;
  const result = await config().db.prepare("INSERT INTO spotify_state (key, value, expires_at) SELECT ?, ?, ? WHERE EXISTS (SELECT 1 FROM spotify_state WHERE key = 'tokens' AND value = ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at")
    .bind(key, value, expiresAt, latest.sealed).run();
  return Boolean(result.meta.changes);
}
export async function spotifyFeed(): Promise<SpotifyFeed> {
  if (!spotifyConfigured()) return EMPTY_SPOTIFY_FEED;
  let cache = await readFeed();
  const now = Date.now();
  const backoff = await get("backoff");
  if (backoff && backoff.expires_at > now) return inactiveSpotifyFeed(cache);
  if (cache && now - cache.updatedAt < spotifyRefreshInterval(cache)) return cache;
  const stored = await connection();
  if (!stored) return EMPTY_SPOTIFY_FEED;
  const leaseId = randomToken();
  const lease = await config().db.prepare("INSERT INTO spotify_state (key, value, expires_at) VALUES ('lease', ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at WHERE spotify_state.expires_at < ? RETURNING value")
    .bind(leaseId, now + 60_000, now).first<{ value: string }>();
  if (!lease) return cache && now - cache.updatedAt < 60_000 ? cache : inactiveSpotifyFeed(cache);
  let playlistCache: SpotifyPlaylistCache | undefined;
  try {
    // Another visitor may have finished a refresh between our first read and lease acquisition.
    cache = await readFeed();
    const latestBackoff = await get("backoff"), checkedAt = Date.now();
    if (latestBackoff && latestBackoff.expires_at > checkedAt) return inactiveSpotifyFeed(cache);
    if (cache && checkedAt - cache.updatedAt < spotifyRefreshInterval(cache)) return cache;
    const access = await accessToken(stored);
    const current = record(await api("/me/player", access));
    // Private Session suppresses all live data; do not query history during it.
    if (record(current.device).is_private_session === true) {
      const feed = { ...EMPTY_SPOTIFY_FEED, status: "ready" as const, updatedAt: now };
      await putForConnection("feed", JSON.stringify(feed), stored.generation); return feed;
    }
    const historyCache = await get("history");
    const history = historyCache && historyCache.expires_at > now ? JSON.parse(historyCache.value) : await api("/me/player/recently-played?limit=50", access);
    if (!historyCache || historyCache.expires_at <= now) {
      // Retain only one track's display fields and recent playlist contexts, for five minutes.
      const items = Array.isArray(record(history).items) ? record(history).items as unknown[] : [];
      await putForConnection("history", JSON.stringify({ items: items.map((raw, index) => {
        const item = record(raw), track = record(item.track), album = record(track.album), context = record(item.context);
        return { played_at: item.played_at, context: { type: context.type, uri: context.uri }, ...(index === 0 ? { track: { id: track.id, type: track.type, name: track.name, is_local: track.is_local, artists: track.artists, album: { images: album.images } } } : {}) };
      }) }), stored.generation, now + SPOTIFY_HISTORY_TTL_MS);
    }
    const historyItems = record(history).items;
    const first = Array.isArray(historyItems) ? record(historyItems[0]) : {};
    const song = songFromSpotify(current.item) ?? songFromSpotify(first.track);
    const candidates = recentPlaylistContexts(history, current, cache?.playlists ?? [], now);
    const playlists: SpotifyFeed["playlists"] = [];
    const metadata = await get("playlists");
    playlistCache = playlistCacheFromStorage(metadata ? JSON.parse(metadata.value) : null, now);
    const sharedPlaylists = playlistCache;
    // Revalidate publication/artwork hourly; fetch newly encountered playlists immediately.
    for (let index = 0; index < candidates.length && playlists.length < 4; index += 4) {
      const group = await Promise.allSettled(candidates.slice(index, index + 4).map(([id, at]) =>
        cachedSpotifyPlaylist(id, at, sharedPlaylists, now, SPOTIFY_PLAYLIST_TTL_MS,
          (playlistId) => api(`/playlists/${playlistId}?fields=id,name,public,images,external_urls`, access))));
      // Wait for every in-flight request and honor the longest cooldown in the batch.
      const failures = group.filter((item) => item.status === "rejected").map((item) => item.reason as unknown);
      if (failures.length) throw failures.sort((a, b) =>
        (b instanceof SpotifyError ? b.retryAfter : SPOTIFY_IDLE_REFRESH_MS) - (a instanceof SpotifyError ? a.retryAfter : SPOTIFY_IDLE_REFRESH_MS))[0];
      for (const item of group) if (item.status === "fulfilled" && item.value && playlists.length < 4) playlists.push(item.value);
    }
    const feed: SpotifyFeed = { status: "ready", isPlaying: current.is_playing === true && Boolean(songFromSpotify(current.item)), song, playlists, updatedAt: Date.now() };
    // Disconnect/reconnect during a network request must not repopulate cleared data.
    return await putForConnection("feed", JSON.stringify(feed), stored.generation) ? feed : EMPTY_SPOTIFY_FEED;
  } catch (error) {
    const retry = error instanceof SpotifyError ? error.retryAfter : SPOTIFY_IDLE_REFRESH_MS;
    const stillConnected = await putForConnection("backoff", JSON.stringify({ code: error instanceof SpotifyError ? error.code : "unavailable" }), stored.generation, Date.now() + retry);
    // A private/deleted playlist discovered before another request failed stays removed.
    const fallback = cache && playlistCache ? { ...cache, playlists: cache.playlists.filter((item) => playlistCache?.[item.id]?.playlist !== null) } : cache;
    if (stillConnected && fallback !== cache) await putForConnection("feed", JSON.stringify(fallback), stored.generation);
    return stillConnected ? inactiveSpotifyFeed(fallback) : EMPTY_SPOTIFY_FEED;
  } finally {
    try {
      // Persist partial successes too, without allowing a disconnected request to restore data.
      if (playlistCache) await putForConnection("playlists", JSON.stringify(playlistCacheFromStorage(playlistCache, Date.now())), stored.generation);
    } finally {
      await config().db.prepare("DELETE FROM spotify_state WHERE key = 'lease' AND value = ?").bind(leaseId).run();
    }
  }
}
