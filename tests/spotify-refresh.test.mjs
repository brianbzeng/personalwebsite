import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { DatabaseSync } from "node:sqlite";
import ts from "typescript";
import * as data from "../app/components/spotifyData.ts";
import * as refresh from "../app/components/spotifyRefresh.ts";
import * as security from "../app/server/spotifySecurity.ts";

const start = Date.parse("2026-09-07T12:00:00Z");
const ids = ["0123456789abcdefghijkl", "abcdefghijkl0123456789", "1111111111111111111111", "2222222222222222222222"];
const track = { id: ids[0], type: "track", name: "Test song", artists: [{ name: "Test artist" }], album: { images: [{ url: "https://i.scdn.co/image/test" }] } };
const playlist = (id) => ({ id, name: `Playlist ${id}`, public: true, images: [{ url: "https://image-cdn-fa.spotifycdn.com/image/test" }] });
const context = (id) => ({ type: "playlist", uri: `spotify:playlist:${id}` });
const source = await readFile(new URL("../app/server/spotify.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;

// Execute the real server logic and SQL against isolated in-memory SQLite.
// Only Workers bindings and outbound HTTP are substituted; no live tokens or Spotify calls.
async function serverHarness(t) {
  const sqlite = new DatabaseSync(":memory:");
  sqlite.exec("CREATE TABLE spotify_state (key TEXT PRIMARY KEY, value TEXT NOT NULL, expires_at INTEGER NOT NULL DEFAULT 0)");
  t.after(() => sqlite.close());
  const db = { prepare(sql) {
    const statement = sqlite.prepare(sql);
    let args = [];
    return {
      bind(...values) { args = values; return this; },
      async first() { return statement.get(...args) ?? null; },
      async run() { return { meta: { changes: Number(statement.run(...args).changes) } }; },
    };
  }, async batch(statements) { return Promise.all(statements.map((statement) => statement.run())); } };
  const env = { DB: db, SPOTIFY_CLIENT_ID: "test-client", SPOTIFY_CLIENT_SECRET: "test-secret", SPOTIFY_REDIRECT_URI: security.SPOTIFY_PRODUCTION_CALLBACK, SPOTIFY_USER_ID: security.SPOTIFY_OWNER };
  const harness = {
    now: start, playing: true, activeId: ids[0], privateSession: false, calls: [],
    override: async () => null,
    get(key) { const row = sqlite.prepare("SELECT * FROM spotify_state WHERE key = ?").get(key); return row ? { ...row, data: JSON.parse(row.value) } : null; },
    put(key, value, expiresAt = 0) { sqlite.prepare("INSERT OR REPLACE INTO spotify_state VALUES (?, ?, ?)").run(key, JSON.stringify(value), expiresAt); },
    clear() { sqlite.exec("DELETE FROM spotify_state"); },
    expireFeed() { const row = this.get("feed"); if (row) this.put("feed", { ...row.data, updatedAt: this.now - refresh.SPOTIFY_IDLE_REFRESH_MS }); },
  };
  t.mock.method(Date, "now", () => harness.now);
  t.mock.method(globalThis, "fetch", async (url) => {
    const path = new URL(url).pathname;
    harness.calls.push(path);
    const override = await harness.override(path);
    if (override) return override;
    if (path === "/v1/me/player") return Response.json({ is_playing: harness.playing, item: track, context: context(harness.activeId), device: { is_private_session: harness.privateSession } });
    if (path === "/v1/me/player/recently-played") return Response.json({ items: ids.map((id, index) => ({ track, context: context(id), played_at: new Date(harness.now - (index + 1) * 1000).toISOString() })) });
    if (path.startsWith("/v1/playlists/")) return Response.json(playlist(path.split("/").at(-1)));
    throw new Error(`Unexpected test request: ${path}`);
  });
  const sealed = await security.seal({ access: "test-access", refresh: "test-refresh", generation: "test-generation", expiresAt: start + 10 * 86400_000 }, env.SPOTIFY_CLIENT_SECRET);
  sqlite.prepare("INSERT INTO spotify_state VALUES ('tokens', ?, 0)").run(sealed);
  const exports = {};
  const modules = { "cloudflare:workers": { env }, "../components/spotifyData": data, "../components/spotifyRefresh": refresh, "./spotifySecurity": security };
  new Function("require", "exports", "process", compiled)((name) => {
    assert.ok(name in modules, `Unexpected test import ${name}`);
    return modules[name];
  }, exports, {env:{NODE_ENV:'production'}});
  return { ...exports, harness };
}

test("active/idle refreshes share one cache, without redownloading playlist artwork", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  const first = await spotifyFeed();
  assert.equal(first.playlists.length, 4);
  assert.equal(h.calls.length, 6); // playback + history + four playlists
  h.now += 30_000;
  await Promise.all(Array.from({ length: 10 }, () => spotifyFeed()));
  assert.equal(h.calls.length, 6);
  h.now += 30_000;
  await spotifyFeed();
  assert.equal(h.calls.length, 7); // playback only
  h.now += 60_000;
  h.playing = false;
  const idle = await spotifyFeed();
  assert.equal(idle.isPlaying, false);
  h.now += 299_999;
  await spotifyFeed();
  assert.equal(h.calls.length, 8);
  h.now += 1;
  await spotifyFeed();
  assert.equal(h.calls.length, 10); // playback + five-minute history refresh
  assert.equal(h.calls.filter((path) => path.startsWith("/v1/playlists/")).length, 4);
});

test("concurrent stale visitors share the refresh lease", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  await spotifyFeed();
  h.now += 60_000;
  const before = h.calls.length;
  await Promise.all(Array.from({ length: 20 }, () => spotifyFeed()));
  assert.equal(h.calls.length - before, 1);
  assert.equal(h.get("lease"), null);
});

test("new playlist artwork loads on the next playback check while known details remain cached", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  await spotifyFeed();
  h.activeId = "3333333333333333333333";
  h.now += 60_000;
  const feed = await spotifyFeed();
  assert.equal(feed.playlists[0].id, h.activeId);
  assert.ok(feed.playlists[0].image.includes("spotifycdn.com"));
  assert.equal(h.calls.length, 8); // one playback + one new playlist
  h.now += 60_000;
  await spotifyFeed();
  assert.equal(h.calls.length, 9);
});

test("hourly refresh removes private playlists and updates changed artwork", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  await spotifyFeed();
  h.now += refresh.SPOTIFY_PLAYLIST_TTL_MS;
  h.override = async (path) => path === `/v1/playlists/${ids[0]}`
    ? Response.json({ ...playlist(ids[0]), public: false })
    : path === `/v1/playlists/${ids[1]}` ? Response.json({ ...playlist(ids[1]), images: [{ url: "https://i.scdn.co/image/updated" }] }) : null;
  const feed = await spotifyFeed();
  assert.equal(feed.playlists.length, 3);
  assert.ok(!feed.playlists.some((item) => item.id === ids[0]));
  assert.equal(feed.playlists[0].image, "https://i.scdn.co/image/updated");
  const before = h.calls.length;
  h.now += 60_000;
  await spotifyFeed();
  assert.equal(h.calls.length - before, 1); // private candidate is negatively cached
});

test("long Retry-After persists across visitors and never retries early", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  await spotifyFeed();
  h.now += 60_000;
  const limitedAt = h.now;
  h.override = async () => Response.json({ error: { reason: "QUOTA_EXCEEDED" } }, { status: 429, headers: { "Retry-After": "172800" } });
  const feed = await spotifyFeed();
  assert.equal(feed.status, "unavailable");
  assert.equal(feed.isPlaying, false);
  assert.equal(feed.playlists.length, 4);
  assert.equal(h.get("backoff").expires_at, limitedAt + 172800_000);
  assert.equal(h.get("backoff").data.code, "quota_limit");
  const count = h.calls.length;
  h.now += 172800_000 - 1;
  await Promise.all(Array.from({ length: 8 }, () => spotifyFeed()));
  assert.equal(h.calls.length, count);
  h.now += 1;
  h.override = async () => null;
  assert.equal((await spotifyFeed()).status, "ready");
  assert.ok(h.calls.length > count);
});

test("playlist batches honor the longest failure and don't restore a newly private card", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  await spotifyFeed();
  h.now += refresh.SPOTIFY_PLAYLIST_TTL_MS;
  h.override = async (path) => {
    if (path === `/v1/playlists/${ids[0]}`) return Response.json({ ...playlist(ids[0]), public: false });
    if (path === `/v1/playlists/${ids[1]}`) return new Response("", { status: 429, headers: { "Retry-After": "600" } });
    if (path === `/v1/playlists/${ids[2]}`) return Response.json({ error: { reason: "QUOTA_EXCEEDED" } }, { status: 429, headers: { "Retry-After": "259200" } });
    return null;
  };
  const feed = await spotifyFeed();
  assert.equal(h.get("backoff").expires_at, h.now + 259200_000);
  assert.equal(feed.playlists.length, 3);
  assert.ok(!feed.playlists.some((item) => item.id === ids[0]));
  assert.equal((await spotifyFeed()).playlists.length, 3);
  assert.equal(h.get("playlists").data[ids[0]].playlist, null);
  assert.equal(h.get("lease"), null);
});

test("Private Session suppresses history/cards and disconnect during refresh cannot repopulate cache", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  await spotifyFeed();
  h.now += 60_000;
  h.privateSession = true;
  const before = h.calls.length;
  const feed = await spotifyFeed();
  assert.equal(feed.song, null);
  assert.deepEqual(feed.playlists, []);
  assert.equal(h.calls.length - before, 1);
  h.now += refresh.SPOTIFY_IDLE_REFRESH_MS;
  h.privateSession = false;
  h.override = async (path) => { if (path === "/v1/me/player") h.clear(); return null; };
  assert.deepEqual(await spotifyFeed(), data.EMPTY_SPOTIFY_FEED);
  for (const key of ["tokens", "feed", "history", "playlists", "backoff", "lease"]) assert.equal(h.get(key), null);
});

test("cooldown parsing handles missing, malformed, date and quota-specific responses conservatively", () => {
  assert.equal(refresh.spotifyRetryDelay("172800", undefined, start), 172800_000);
  assert.equal(refresh.spotifyRetryDelay(new Date(start + 3600_000).toUTCString(), undefined, start), 3600_000);
  for (const header of [null, "", "nonsense", "-1", "Infinity", "0"]) {
    assert.equal(refresh.spotifyRetryDelay(header, undefined, start), 300_000);
    assert.equal(refresh.spotifyRetryDelay(header, "QUOTA_EXCEEDED", start), 86400_000);
  }
});

test("stable four-playlist daily traffic is reduced by more than 90 percent", async (t) => {
  const { spotifyFeed, harness: h } = await serverHarness(t);
  for (let minute = 0; minute < 24 * 60; minute++) {
    h.now = start + minute * 60_000;
    await spotifyFeed();
  }
  assert.equal(h.calls.filter((path) => path === "/v1/me/player").length, 1440);
  assert.equal(h.calls.filter((path) => path === "/v1/me/player/recently-played").length, 288);
  assert.equal(h.calls.filter((path) => path.startsWith("/v1/playlists/")).length, 96);
  assert.equal(h.calls.length, 1824);
  assert.ok(h.calls.length < 23040 * 0.1);
});
