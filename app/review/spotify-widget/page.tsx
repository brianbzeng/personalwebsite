"use client";

import { useState } from "react";
import SpotifyWidget from "../../components/SpotifyWidget";
import type { SpotifyFeed } from "../../components/spotifyData";

// This sample is deliberately not Brian's live listening history.
const sampleFeed: SpotifyFeed = {
  status: "ready",
  isPlaying: true,
  song: {
    id: "review-sample",
    name: "Sample song",
    artist: "Preview artist",
    image: null,
    url: "https://open.spotify.com/search/Sample%20song",
  },
  playlists: [],
  updatedAt: 0,
};
const pausedFeed: SpotifyFeed = { ...sampleFeed, isPlaying: false };

export default function SpotifyWidgetReview() {
  const [playing, setPlaying] = useState(true);
  return <main className="spotify-widget-review">
    <h1>Spotify widget · review</h1>
    <p>Sample data, not live listening. The bars are decorative; hovering over them no longer reveals a listen-along option. The song itself remains a link.</p>
    <div className="spotify-widget-review-actions">
      <button type="button" aria-pressed={playing} onClick={() => setPlaying(true)}>Playing</button>
      <button type="button" aria-pressed={!playing} onClick={() => setPlaying(false)}>Paused</button>
    </div>
    <section className="spotify-widget-review-desktop" aria-label="Desktop widget preview">
      <SpotifyWidget previewFeed={playing ? sampleFeed : pausedFeed} />
    </section>
  </main>;
}
