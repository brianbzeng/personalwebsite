import { authorizeGet, connectionError, spotifyRequestAllowed } from "../../../server/spotify";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  if (!spotifyRequestAllowed(request)) return new Response("Not found", { status: 404 });
  try { return await authorizeGet(request); } catch { return connectionError(); }
}
