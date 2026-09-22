import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { EMPTY_SPOTIFY_FEED, inactiveSpotifyFeed, playlistContext, playlistFromSpotify, recentPlaylistContexts, songFromSpotify } from "../app/components/spotifyData.ts";
import { SPOTIFY_SCOPES, digest, localSpotifyRequest, ownerMatches, randomToken, sameOriginPost, seal, unseal } from "../app/server/spotifySecurity.ts";

const id = "0123456789abcdefghijkl";
const otherId = "abcdefghijkl0123456789";
const image = "https://i.scdn.co/image/example";
const track = { id, type: "track", name: "Track", artists: [{ name: "Artist" }], album: { images: [{ url: image }] } };
test("only trusted Spotify track fields and links reach the widget", () => {
  const result = songFromSpotify({ ...track, external_urls: { spotify: "https://evil.example" }, secret: "not public" });
  assert.deepEqual(result, { id, name: "Track", artist: "Artist", image, url: `https://open.spotify.com/track/${id}` });
  assert.equal(songFromSpotify({ ...track, is_local: true }), null);
  assert.equal(songFromSpotify({ ...track, type: "episode" }), null);
  assert.equal(songFromSpotify(null), null);
});
test("untrusted artwork URLs and playlist IDs are rejected", () => {
  assert.equal(songFromSpotify({ ...track, album: { images: [{ url: "https://evil.example/image" }] } }).image, null);
  assert.equal(playlistContext({ type: "playlist", uri: "spotify:playlist:../../secrets" }), null);
  assert.equal(playlistContext({ type: "album", uri: `spotify:album:${id}` }), null);
});
test("custom playlist covers load from Spotify's image CDNs without allowing lookalike hosts", () => {
  const cover = (url) => playlistFromSpotify({ id, name: "Custom cover", public: true, images: [{ url }] }, 1).image;
  for (const url of [
    "https://image-cdn-fa.spotifycdn.com/image/ab67706c0000da84f5af81872ff1839cbf01e787",
    "https://image-cdn-ak.spotifycdn.com/image/custom-cover",
    "https://mosaic.scdn.co/640/playlist-mosaic",
    image,
  ]) assert.equal(cover(url), url);
  for (const url of [
    "http://image-cdn-fa.spotifycdn.com/image/custom-cover",
    "https://image-cdn-fa.spotifycdn.com.evil.example/image/custom-cover",
    "https://evilspotifycdn.com/image/custom-cover",
    "https://evilscdn.co/image/custom-cover",
    "https://image-cdn-fa.spotifycdn.com@evil.example/image/custom-cover",
    "data:image/svg+xml,<svg/>",
    "not-a-url",
  ]) assert.equal(cover(url), null);
});
test("private, unlisted and unknown-publication playlists cannot become cards", () => {
  for (const published of [false, null, undefined]) assert.equal(playlistFromSpotify({ id, name: "Hidden", public: published }, 1), null);
  assert.equal(playlistFromSpotify({ id, name: "Public", public: true }, 1).url, `https://open.spotify.com/playlist/${id}`);
});
test("playlist recency uses actual play times, deduplicates and merges active playback", () => {
  const now = Date.now(), context = (id) => ({ type: "playlist", uri: `spotify:playlist:${id}` });
  const history = { items: [
    { context: context(id), played_at: new Date(now - 5000).toISOString() },
    { context: context(otherId), played_at: new Date(now - 2000).toISOString() },
    { context: context(id), played_at: new Date(now - 9000).toISOString() },
  ] };
  assert.deepEqual(recentPlaylistContexts(history, {}, [], now), [[otherId, now - 2000], [id, now - 5000]]);
  assert.deepEqual(recentPlaylistContexts(history, { is_playing: true, context: context(id) }, [], now), [[id, now], [otherId, now - 2000]]);
});
test("no fabricated playlists when history is missing, stale or invalid", () => {
  const now = Date.now();
  assert.deepEqual(recentPlaylistContexts(null, null, [], now), []);
  assert.deepEqual(recentPlaylistContexts({}, {}, [{ id, playedAt: now - 31 * 86400_000 }], now), []);
});
test("inactive fallback retains older music, artwork and links without claiming live playback", () => {
  const updatedAt = Date.now() - 2 * 86400_000;
  const cache = Object.freeze({ status: "ready", isPlaying: true, song: songFromSpotify(track), playlists: [playlistFromSpotify({ id: otherId, name: "Rotation", public: true, images: [{ url: image }] }, updatedAt)], updatedAt });
  const result = inactiveSpotifyFeed(cache);
  assert.deepEqual(result, { ...cache, status: "unavailable", isPlaying: false });
  assert.equal(result.song.image, image);
  assert.equal(result.playlists[0].url, `https://open.spotify.com/playlist/${otherId}`);
  assert.equal(cache.isPlaying, true);
  assert.equal(cache.status, "ready");
});
test("inactive fallback never resurrects cleared or private-session cards", () => {
  for (const cache of [null, EMPTY_SPOTIFY_FEED, { ...EMPTY_SPOTIFY_FEED, status: "ready", updatedAt: Date.now() }]) {
    const result = inactiveSpotifyFeed(cache);
    assert.equal(result.song, null);
    assert.deepEqual(result.playlists, []);
    assert.equal(result.isPlaying, false);
  }
});
test("server respects cooldown, clears on disconnect, and gates error fallback on connection generation", async () => {
  const server = await readFile(new URL("../app/server/spotify.ts", import.meta.url), "utf8");
  assert.match(server, /if \(backoff && backoff.expires_at > now\) return inactiveSpotifyFeed\(cache\)/);
  assert.ok(server.indexOf('backoff.expires_at > now') < server.indexOf('const access = await accessToken(stored)'));
  assert.match(server, /DELETE FROM spotify_state WHERE key IN \('tokens','feed','history','playlists','lease','backoff'\)/);
  assert.match(server, /return stillConnected \? inactiveSpotifyFeed\(fallback\) : EMPTY_SPOTIFY_FEED/);
  assert.match(server, /is_private_session === true[\s\S]*?\.\.\.EMPTY_SPOTIFY_FEED/);
});
test("OAuth setup rejects production and any non-literal loopback origin", () => {
  assert.equal(localSpotifyRequest(new Request("http://127.0.0.1:3000/api/spotify/connect"), true), true);
  for (const url of ["http://localhost:3000", "http://127.0.0.1:3001", "https://evil.example", "http://127.0.0.1.evil.example:3000"]) assert.equal(localSpotifyRequest(new Request(url), true), false);
  assert.equal(localSpotifyRequest(new Request("http://127.0.0.1:3000"), false), false);
});
test("disconnect POST requires exact origin, never accepts null or cross-site", () => {
  const request = (origin, site) => new Request("http://127.0.0.1:3000/api/spotify/connect", { method: "POST", headers: { origin, "sec-fetch-site": site } });
  assert.equal(sameOriginPost(request("http://127.0.0.1:3000", "same-origin")), true);
  assert.equal(sameOriginPost(request("null", "same-origin")), false);
  assert.equal(sameOriginPost(request("https://evil.example", "cross-site")), false);
});
test("OAuth binds only Brian's account, then uses immutable account_id", () => {
  assert.equal(ownerMatches({ id: "12127274651" }), true);
  assert.equal(ownerMatches({ id: "attacker" }), false);
  assert.equal(ownerMatches({ id: "changed", account_id: "stable" }, "stable"), true);
  assert.equal(ownerMatches({ id: "12127274651", account_id: "attacker" }, "stable"), false);
});
test("random state and PKCE are cryptographic; tokens are authenticated ciphertext", async () => {
  const nonce = randomToken(); assert.equal(nonce.length, 43); assert.notEqual(nonce, randomToken());
  assert.equal((await digest(nonce)).length, 43);
  const payload = { access: "access-test-secret", refresh: "refresh-test-secret" };
  const encrypted = await seal(payload, "fake-local-secret");
  assert.ok(!encrypted.includes(payload.refresh));
  assert.deepEqual(await unseal(encrypted, "fake-local-secret"), payload);
  await assert.rejects(unseal(encrypted, "different-secret"));
});
test("no playback modifications or terminal command; persistent attribution and reduced motion", async () => {
  assert.equal(SPOTIFY_SCOPES, "user-read-playback-state user-read-recently-played");
  assert.ok(!SPOTIFY_SCOPES.includes("modify"));
  const widget = await readFile(new URL("../app/components/SpotifyWidget.tsx", import.meta.url), "utf8");
  const css = await readFile(new URL("../app/components/spotifyWidget.css", import.meta.url), "utf8");
  assert.match(widget, /spotify-widget-footer/);
  assert.match(widget, /wordmark-white\.svg/);
  assert.doesNotMatch(widget, /onClick=|onPointerDown=/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /object-fit: contain/);
  assert.match(css, /\.spotify-widget a:focus-visible/);
  assert.doesNotMatch(widget, /spotify-listen-along|spotify-listen-label|Listen along/);
  assert.doesNotMatch(css, /spotify-listen-along|spotify-listen-label/);
});
test("widget uses one footer logo, no empty-playlist copy, and initial-only skeletons", async () => {
  const widget = await readFile(new URL("../app/components/SpotifyWidget.tsx", import.meta.url), "utf8");
  const css = await readFile(new URL("../app/components/spotifyWidget.css", import.meta.url), "utf8");
  assert.match(widget, /My Current Rotation/);
  assert.doesNotMatch(widget, /Your recent playlists will appear here|Recently in rotation|spotify-status-logo|icon-white\.svg/);
  assert.match(widget, /loading \? <SongSkeleton/);
  assert.match(widget, /loading \? <PlaylistSkeletons/);
  assert.match(widget, /aria-busy=\{loading\}/);
  assert.match(widget, /const playing = !loading/);
  assert.match(widget, /const status = playing \? "Listening now" : "A little quiet for now"/);
  assert.doesNotMatch(widget, /Temporarily offline|Temporarily unavailable|Cached music|Recently played/);
  assert.match(widget, /<span className="spotify-passive-levels" aria-hidden="true">/);
  assert.match(css, /\.spotify-passive-levels \{[^}]*opacity: 0;[^}]*pointer-events: none;[^}]*transition: opacity/);
  assert.match(css, /\.spotify-widget\.is-playing \.spotify-passive-levels \{ opacity: 1;/);
  assert.match(css, /@keyframes spotify-skeleton-pulse/);
});
