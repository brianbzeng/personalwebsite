import { connectPage, connectPost, connectionError, spotifyRequestAllowed } from "../../../server/spotify";
import { localSpotifyRequest, sameOriginPost } from "../../../server/spotifySecurity";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  if (!spotifyRequestAllowed(request)) return new Response("Not found", { status: 404 });
  try { return await connectPage(); } catch { return connectionError("The connection setup is unavailable. Check the database and Spotify settings for this environment.", 503); }
}
export async function POST(request: Request) {
  if (!localSpotifyRequest(request, process.env.NODE_ENV === "development")) return new Response("Not found", { status: 404 });
  if (!sameOriginPost(request)) return connectionError("Please start from the local connection page.", 403);
  try { return await connectPost(request); } catch { return connectionError(); }
}
