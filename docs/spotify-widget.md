# Spotify desktop widget

Read-only, single-owner integration for Spotify profile `12127274651`. No terminal command, playback controls, autoplay, or synchronized playback.

## Local setup

- Store `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`, and `SPOTIFY_USER_ID` in ignored `.env.local`.
- Callback is exactly `http://127.0.0.1:3000/api/spotify/callback`.
- Run `pnpm exec wrangler d1 migrations apply site-creator-d1 --local --config wrangler.local.jsonc` after initial setup.
- `pnpm dev` binds to IPv4 loopback. Open `http://127.0.0.1:3000/api/spotify/connect`, then Continue to Spotify.
- Scopes: `user-read-playback-state` (includes Private Session status) and `user-read-recently-played`. No write/control scopes.
- Credentials are AES-GCM encrypted in local D1 under `.wrangler/state`; `.env*` and `.wrangler/` are ignored by Git. Keep the client secret stable; changing it requires reconnecting.
- Tokens/codes/cookies must never be copied into chat, screenshots, public build output, or logs.

## Behavior

The public endpoint `/api/spotify` returns only selected song/playlist fields. Private Sessions suppress the widget's listening data. Published public playlist contexts are deduplicated by most recent play time; missing contexts are not invented. Up to four qualifying playlists display, with a bounded 30-day recent-card window. Album/direct track plays cannot always identify a playlist.

The widget checks once a minute during active listening and every five minutes when idle, disconnected, or unavailable, only while the page is visible. The server enforces the same intervals with a shared D1 feed cache and refresh lease, so additional tabs/visitors and page reloads do not multiply Spotify requests. It rechecks the cache after acquiring the lease to avoid overlapping-refresh races. Starting playback from idle can take up to five minutes to appear; active track/stop changes can take up to a minute.

Recent history is cached for five minutes. Playlist names, artwork URLs, and public visibility are cached for one hour in D1, independently of playback. A newly encountered playlist is fetched on the next eligible playback/history check; listening again updates its position without refetching metadata. Private/missing results are negatively cached too. Visibility and artwork edits to known playlists can take an hour to be noticed; a playlist found private/deleted is removed even if another playlist request fails. Cache size is bounded to 64 metadata entries. No scheduled/background polling is configured. Long offline gaps can leave fewer than four recent playlists; Spotify does not guarantee complete history.

All Spotify 429 responses pause upstream requests for the full `Retry-After`, without truncating long cooldowns to 24 hours. A missing/invalid cooldown uses a five-minute fallback, or a conservative 24-hour fallback for `QUOTA_EXCEEDED`; the latter is our retry policy, not a claim about Spotify's reset schedule. Parallel playlist requests are all settled before saving the longest cooldown. Backoff and metadata persist across server restarts; reconnect/disconnect clears connection-scoped caches. Error bodies and credentials are never logged or exposed to visitors.

For continuous active viewing with the same four public playlists, the approximate daily data-request budget drops from 23,040 to 1,824 (1,440 playback + 288 history + 96 playlist requests), about 92% fewer. This estimate excludes token refreshes, newly encountered/private playlist candidates, and retries; it is not a guaranteed quota allowance. Idle periods and no visitors reduce it further.

During an upstream outage or cooldown, the last successful song and playlist cards remain available from the existing D1 feed across page reloads and server restarts. The original update time is preserved; live playback and listen-along animation are disabled. The visible inactive status is simply “A little quiet for now,” with no cache/offline notice. A successful fresh response replaces these cards; disconnect/reconnect clears them, and a detected Private Session replaces the feed with empty data. Cached playlist visibility cannot be rechecked until Spotify permits requests again.

Album covers remain unaltered and uncropped. Native desktop icons and wallpaper remain grayscale. The official full Spotify logo stays visible in the footer beside “My Current Rotation.” The upper-right slot is empty while idle; decorative bars fade in during playback. Initial loading shows muted skeleton artwork/text placeholders, without replacing populated content during background updates. Empty playlist rows have no placeholder message. Song/playlist links open their exact Spotify destination; Listen along opens the current track, not a Jam session.

## Disconnect and hosting

The local connection page has a disconnect action that clears the token and widget cache. Use a normal browser if the embedded browser sends an opaque Origin for this POST. You can also revoke access in Spotify account settings.

## Production setup (2026-09-11)

Brian requested live Spotify support on production. Cloudflare Worker `brian-zeng-portfolio` uses a dedicated `brian-portfolio-spotify` D1 database through `DB`, with the existing `spotify_state` migration. Local credentials and database contents are never uploaded.

- Spotify Developer Dashboard → existing app → Settings contains the Client ID and Client Secret.
- In Cloudflare Worker Settings → Variables and Secrets, store `SPOTIFY_CLIENT_SECRET` as **Secret** and `SPOTIFY_CLIENT_ID` as text or secret. The production config supplies `SPOTIFY_USER_ID=12127274651` and `SPOTIFY_REDIRECT_URI=https://brianbzeng.com/api/spotify/callback`.
- Register that exact HTTPS callback in the same Spotify app, keeping the existing loopback callback for local development.
- Visit https://brianbzeng.com/api/spotify/connect and authorize Brian's account. Only the verified owner can replace the encrypted production connection. Failed/non-owner authorization leaves the existing tokens and feed untouched.
- Production cookies are Secure, HttpOnly and SameSite=Lax. OAuth accepts only the configured exact canonical origin; worker preview URLs are not connection hosts. State is single-use, PKCE-bound, expires in ten minutes, and pending attempts are capped at 64.
- The destructive local disconnect POST and form remain unavailable in production. To revoke production access, use Spotify account app permissions; no anonymous visitor can clear the connection.
- Worker invocation logs are disabled so OAuth query parameters are not automatically recorded. Application errors still use fixed, redacted diagnostics.
- The production room now uses the live feed for the previously approved speaker loop; simulated playback remains confined to the speaker review route. Existing cache intervals and Private Session suppression are unchanged.

References: https://developer.spotify.com/documentation/web-api/tutorials/code-flow · https://developer.spotify.com/documentation/web-api/reference/get-recently-played · https://developer.spotify.com/documentation/design · https://developer.spotify.com/documentation/web-api/concepts/rate-limits · https://developer.spotify.com/documentation/web-api/concepts/quota-modes
