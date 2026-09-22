import { SPOTIFY_ACTIVE_REFRESH_MS } from "./spotifyRefresh";

/** Never treat cached last-played cards, errors, or malformed feeds as live audio. */
export function speakerIsPlaying(value: unknown, now = Date.now()): boolean {
  if (!value || typeof value !== "object") return false;
  const feed = value as Record<string, unknown>;
  return feed.status === "ready" && feed.isPlaying === true && !!feed.song && typeof feed.song === "object"
    && typeof feed.updatedAt === "number" && Number.isFinite(feed.updatedAt)
    && feed.updatedAt <= now && now - feed.updatedAt < SPOTIFY_ACTIVE_REFRESH_MS;
}
