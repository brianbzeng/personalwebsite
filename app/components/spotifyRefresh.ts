import type { SpotifyFeed } from "./spotifyData";

// Shared by the browser and server: opening more tabs cannot bypass these limits.
export const SPOTIFY_ACTIVE_REFRESH_MS = 60_000;
export const SPOTIFY_IDLE_REFRESH_MS = 5 * 60_000;
export const SPOTIFY_HISTORY_TTL_MS = 5 * 60_000;
export const SPOTIFY_PLAYLIST_TTL_MS = 60 * 60_000;

export function spotifyRefreshInterval(feed: SpotifyFeed): number {
  return feed.status === "ready" && feed.isPlaying
    ? SPOTIFY_ACTIVE_REFRESH_MS : SPOTIFY_IDLE_REFRESH_MS;
}

export function spotifyRetryDelay(retryAfter: string | null, reason: unknown, now = Date.now()): number {
  const value = retryAfter?.trim() ?? "";
  const seconds = /^\d+(?:\.\d+)?$/.test(value) ? Number(value) : NaN;
  const milliseconds = Number.isFinite(seconds) ? seconds * 1000
    : /^[A-Za-z]{3},/.test(value) ? Date.parse(value) - now : NaN;
  // Never shorten an upstream cooldown, including one longer than a day.
  if (Number.isFinite(milliseconds) && milliseconds > 0) return Math.max(SPOTIFY_IDLE_REFRESH_MS, milliseconds);
  // A conservative local fallback, NOT an assumption about Spotify's quota reset window.
  return reason === "QUOTA_EXCEEDED" ? 24 * 60 * 60_000 : SPOTIFY_IDLE_REFRESH_MS;
}
