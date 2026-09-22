export type SpotifySong = { id: string; name: string; artist: string; image: string | null; url: string };
export type SpotifyPlaylist = { id: string; name: string; image: string | null; url: string; playedAt: number };
export type SpotifyPlaylistCache = Record<string, { playlist: SpotifyPlaylist | null; expiresAt: number }>;
export type SpotifyFeed = {
  status: "ready" | "disconnected" | "unavailable";
  isPlaying: boolean;
  song: SpotifySong | null;
  playlists: SpotifyPlaylist[];
  updatedAt: number;
};
export const EMPTY_SPOTIFY_FEED: SpotifyFeed = { status: "disconnected", isPlaying: false, song: null, playlists: [], updatedAt: 0 };
export const SPOTIFY_PROFILE_URL = "https://open.spotify.com/user/12127274651";

export function inactiveSpotifyFeed(feed: SpotifyFeed | null): SpotifyFeed {
  // Retain the last-known cards through outages, but never imply live playback.
  // Empty feeds from a disconnect or Private Session stay empty.
  return { ...(feed ?? EMPTY_SPOTIFY_FEED), status: "unavailable", isPlaying: false };
}

export function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
export function spotifyId(value: unknown): string | null {
  return typeof value === "string" && /^[a-zA-Z0-9]{22}$/.test(value) ? value : null;
}
function artwork(images: unknown): string | null {
  if (!Array.isArray(images)) return null;
  for (const item of images) {
    const url = record(item).url;
    if (typeof url !== "string") continue;
    try {
      const parsed = new URL(url);
      // Spotify serves custom playlist covers from spotifycdn.com as well as
      // the scdn.co hosts used for album art and generated playlist mosaics.
      const spotifyCdn = parsed.hostname.endsWith(".scdn.co") || parsed.hostname.endsWith(".spotifycdn.com");
      if (parsed.protocol === "https:" && spotifyCdn) return url;
    } catch { /* An unavailable cover is preferable to an untrusted image URL. */ }
  }
  return null;
}
export function songFromSpotify(value: unknown): SpotifySong | null {
  const item = record(value), id = spotifyId(item.id);
  if (!id || item.type !== "track" || item.is_local === true || typeof item.name !== "string") return null;
  const artist = Array.isArray(item.artists) ? item.artists.map((entry) => record(entry).name).filter((name): name is string => typeof name === "string").join(", ") : "";
  return { id, name: item.name, artist, image: artwork(record(item.album).images), url: `https://open.spotify.com/track/${id}` };
}
export function playlistFromSpotify(value: unknown, playedAt: number): SpotifyPlaylist | null {
  const item = record(value), id = spotifyId(item.id);
  // Only profile-published playlists; private/unlisted/unknown visibility is excluded.
  if (!id || item.public !== true || typeof item.name !== "string") return null;
  return { id, name: item.name, image: artwork(item.images), url: `https://open.spotify.com/playlist/${id}`, playedAt };
}

export function playlistCacheFromStorage(value: unknown, now: number): SpotifyPlaylistCache {
  const cache: SpotifyPlaylistCache = {};
  for (const [id, raw] of Object.entries(record(value))) {
    const entry = record(raw), item = record(entry.playlist);
    if (!spotifyId(id) || typeof entry.expiresAt !== "number" || !Number.isFinite(entry.expiresAt) || entry.expiresAt <= now) continue;
    const playlist = entry.playlist === null ? null : playlistFromSpotify({
      id: item.id, name: item.name, public: true, images: [{ url: item.image }],
    }, 0);
    if (entry.playlist !== null && (!playlist || playlist.id !== id)) continue;
    cache[id] = { playlist, expiresAt: entry.expiresAt };
  }
  // Bound storage even when many different playlists are played in an hour.
  return Object.fromEntries(Object.entries(cache).sort((a, b) => b[1].expiresAt - a[1].expiresAt).slice(0, 64));
}

export async function cachedSpotifyPlaylist(
  id: string, playedAt: number, cache: SpotifyPlaylistCache, now: number, ttl: number,
  fetchPlaylist: (id: string) => Promise<unknown>,
): Promise<SpotifyPlaylist | null> {
  if (!spotifyId(id)) return null;
  let entry = cache[id];
  if (!entry || entry.expiresAt <= now) {
    const playlist = playlistFromSpotify(await fetchPlaylist(id), 0);
    // Negative results are cached too; don't repeatedly request private/missing playlists.
    entry = { playlist: playlist?.id === id ? playlist : null, expiresAt: now + ttl };
    cache[id] = entry;
  }
  // Listening again updates ordering without downloading the same artwork/details.
  return entry.playlist ? { ...entry.playlist, playedAt } : null;
}
export function playlistContext(value: unknown): string | null {
  const context = record(value);
  if (context.type !== "playlist" || typeof context.uri !== "string") return null;
  return spotifyId(context.uri.replace(/^spotify:playlist:/, ""));
}
export function recentPlaylistContexts(history: unknown, current: unknown, previous: SpotifyPlaylist[], now: number) {
  const found = new Map<string, number>();
  for (const item of previous) if (now - item.playedAt < 30 * 86400_000 && spotifyId(item.id)) found.set(item.id, item.playedAt);
  const items = record(history).items;
  if (Array.isArray(items)) for (const raw of items) {
    const item = record(raw), id = playlistContext(item.context);
    const at = typeof item.played_at === "string" ? Date.parse(item.played_at) : NaN;
    if (id && Number.isFinite(at) && at <= now && now - at < 30 * 86400_000) found.set(id, Math.max(found.get(id) ?? 0, at));
  }
  const playback = record(current), activeId = playlistContext(playback.context);
  if (playback.is_playing === true && activeId) found.set(activeId, now);
  return [...found].sort((a, b) => b[1] - a[1]).slice(0, 12);
}
