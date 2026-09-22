import { spotifyFeed } from "../../server/spotify";
import { EMPTY_SPOTIFY_FEED } from "../../components/spotifyData";
export const dynamic = "force-dynamic";
export async function GET() {
  try { return Response.json(await spotifyFeed(), { headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } }); }
  catch { return Response.json({ ...EMPTY_SPOTIFY_FEED, status: "unavailable" }, { status: 503, headers: { "Cache-Control": "no-store" } }); }
}
