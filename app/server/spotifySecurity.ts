const encoder = new TextEncoder();
export const SPOTIFY_CALLBACK = "http://127.0.0.1:3000/api/spotify/callback";
export const SPOTIFY_PRODUCTION_CALLBACK = "https://brianbzeng.com/api/spotify/callback";
export const SPOTIFY_OWNER = "12127274651";
// Playback-state is read-only and lets us honor Spotify's Private Session flag.
export const SPOTIFY_SCOPES = "user-read-playback-state user-read-recently-played";
export function localSpotifyRequest(request: Request, development: boolean) {
  return development && new URL(request.url).origin === new URL(SPOTIFY_CALLBACK).origin;
}
export function spotifyCallbackAllowed(callback: unknown, development: boolean) {
  return callback === (development ? SPOTIFY_CALLBACK : SPOTIFY_PRODUCTION_CALLBACK);
}
export function spotifyOAuthRequest(request: Request, callback: unknown, development: boolean) {
  return spotifyCallbackAllowed(callback, development)
    && new URL(request.url).origin === new URL(callback as string).origin;
}
export function spotifyStateCookie(value: string, maxAge: number, development: boolean) {
  return `spotify_connect_state=${value}; Path=/api/spotify; HttpOnly; SameSite=Lax; Max-Age=${maxAge}${development ? "" : "; Secure"}`;
}
export function sameOriginPost(request: Request) {
  return request.method === "POST" && request.headers.get("origin") === new URL(SPOTIFY_CALLBACK).origin
    && [null, "same-origin", "none"].includes(request.headers.get("sec-fetch-site"));
}
export function base64url(bytes: Uint8Array) {
  return btoa(String.fromCharCode(...bytes)).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}
export function randomToken() { return base64url(crypto.getRandomValues(new Uint8Array(32))); }
export async function digest(value: string) { return base64url(new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value)))); }
async function encryptionKey(secret: string) {
  const material = await crypto.subtle.importKey("raw", encoder.encode(secret), "HKDF", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "HKDF", hash: "SHA-256", salt: encoder.encode("brian-spotify-v1"), info: encoder.encode("owner-credentials") }, material, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}
export async function seal(value: unknown, secret: string) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await encryptionKey(secret), encoder.encode(JSON.stringify(value)));
  return JSON.stringify({ iv: Array.from(iv), data: Array.from(new Uint8Array(encrypted)) });
}
export async function unseal(value: string, secret: string): Promise<unknown> {
  const { iv, data } = JSON.parse(value);
  const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(iv) }, await encryptionKey(secret), new Uint8Array(data));
  return JSON.parse(new TextDecoder().decode(plain));
}
export function ownerMatches(profile: Record<string, unknown>, accountId?: string) {
  return accountId ? profile.account_id === accountId : profile.id === SPOTIFY_OWNER;
}
