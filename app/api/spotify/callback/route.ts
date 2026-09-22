import { connectCallback, connectionError, logSpotifyFailure, spotifyRequestAllowed } from "../../../server/spotify";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  if (!spotifyRequestAllowed(request)) return new Response("Not found", { status: 404 });
  try { return await connectCallback(request); } catch (error) { logSpotifyFailure(error); return connectionError(); }
}
