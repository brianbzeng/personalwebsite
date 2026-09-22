"use client";

import { useEffect, useState } from "react";
import { EMPTY_SPOTIFY_FEED, inactiveSpotifyFeed, SPOTIFY_PROFILE_URL, type SpotifyFeed } from "./spotifyData";
import { SPOTIFY_IDLE_REFRESH_MS, spotifyRefreshInterval } from "./spotifyRefresh";
import "./spotifyWidget.css";

function Cover({ image, name }: { image: string | null; name: string }) {
  const [failedImage, setFailedImage] = useState<string | null>(null);
  return image && image !== failedImage ? <img className="spotify-cover" src={image} alt={name} draggable={false} onError={() => setFailedImage(image)} />
    : <span className="spotify-cover spotify-cover-empty" aria-label={`${name} — artwork unavailable`}>♪</span>;
}

function SongSkeleton() {
  return <div className="spotify-song spotify-song-skeleton" aria-hidden="true">
    <span className="spotify-cover spotify-skeleton" />
    <span className="spotify-song-copy">
      <span className="spotify-skeleton spotify-skeleton-status" />
      <span className="spotify-skeleton spotify-skeleton-title" />
      <span className="spotify-skeleton spotify-skeleton-artist" />
    </span>
  </div>;
}

function PlaylistSkeletons() {
  return <>{[0, 1, 2, 3].map((index) => <div className="spotify-playlist" key={index} aria-hidden="true">
    <span className="spotify-cover spotify-skeleton" />
    <span className="spotify-skeleton spotify-skeleton-caption" />
  </div>)}</>;
}

type SpotifyWidgetProps = {
  /** Explicit review fixture; never polls or substitutes production listening data. */
  previewFeed?: SpotifyFeed;
};

export default function SpotifyWidget({ previewFeed }: SpotifyWidgetProps = {}) {
  const [liveFeed, setFeed] = useState<SpotifyFeed>(EMPTY_SPOTIFY_FEED);
  const [liveLoading, setLoading] = useState(true);
  useEffect(() => {
    if (previewFeed) return;
    // The Blender idle capture must not bake personal listening data into its loop.
    if (new URLSearchParams(window.location.search).get("capture") === "idle") return;
    let stopped = false, timer: ReturnType<typeof setTimeout> | undefined;
    let controller: AbortController | undefined;
    const refresh = async () => {
      clearTimeout(timer);
      if (stopped || document.hidden) return;
      controller?.abort(); controller = new AbortController();
      const current = controller;
      const deadline = setTimeout(() => current.abort(), 45_000);
      let delay = SPOTIFY_IDLE_REFRESH_MS;
      try {
        const response = await fetch("/api/spotify", { cache: "no-store", signal: current.signal });
        if (!response.ok) throw new Error("Spotify unavailable");
        const data: SpotifyFeed = await response.json();
        if (!stopped && !current.signal.aborted) setFeed(data);
        delay = spotifyRefreshInterval(data);
      } catch {
        if (!stopped && controller === current) setFeed(inactiveSpotifyFeed);
        delay = SPOTIFY_IDLE_REFRESH_MS;
      } finally {
        clearTimeout(deadline);
        if (!stopped && controller === current) { setLoading(false); timer = setTimeout(refresh, delay); }
      }
    };
    const visibility = () => {
      if (document.hidden) {
        clearTimeout(timer);
        const active = controller;
        controller = undefined;
        active?.abort();
      }
      else void refresh();
    };
    void refresh();
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("online", refresh);
    return () => { stopped = true; clearTimeout(timer); controller?.abort(); document.removeEventListener("visibilitychange", visibility); window.removeEventListener("online", refresh); };
  }, [previewFeed]);

  const feed = previewFeed ?? liveFeed;
  const loading = previewFeed ? false : liveLoading;
  const playing = !loading && feed.status === "ready" && feed.isPlaying && Boolean(feed.song);
  const status = playing ? "Listening now" : "A little quiet for now";
  return <aside className={`spotify-widget${playing ? " is-playing" : ""}`} aria-label="Brian’s Spotify listening" aria-busy={loading}>
    <div className="spotify-widget-top">
      {loading ? <SongSkeleton /> : feed.song ? <a className="spotify-song" href={feed.song.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${feed.song.name} by ${feed.song.artist} in Spotify`}>
        <Cover image={feed.song.image} name={`${feed.song.name} cover`} />
        <span className="spotify-song-copy"><span className="spotify-status" aria-live="polite">{status}</span><strong title={feed.song.name}>{feed.song.name}</strong><span className="spotify-artist" title={feed.song.artist}>{feed.song.artist}</span></span>
      </a> : <div className="spotify-song spotify-song-idle">
        <span className="spotify-cover spotify-cover-empty" aria-hidden="true">♪</span>
        <span className="spotify-song-copy"><span className="spotify-status" aria-live="polite">{status}</span><strong>Brian’s listening</strong>{feed.status === "disconnected" && <span className="spotify-artist">Spotify isn’t connected yet</span>}</span>
      </div>}
      <div className="spotify-live-slot">
        <span className="spotify-passive-levels" aria-hidden="true">
          <span className="spotify-equalizer">{[0, 1, 2, 3, 4].map((index) => <i key={index} />)}</span>
        </span>
      </div>
    </div>
    <div className="spotify-playlist-strip" aria-label="Recently listened-to public playlists">
      {loading ? <PlaylistSkeletons /> : feed.playlists.map((playlist) => <a className="spotify-playlist" key={playlist.id} href={playlist.url} target="_blank" rel="noopener noreferrer" aria-label={`Open playlist ${playlist.name} in Spotify`} title={playlist.name}>
        <Cover image={playlist.image} name={`${playlist.name} playlist cover`} /><span>{playlist.name}</span>
      </a>)}
    </div>
    <footer className="spotify-widget-footer"><span>My Current Rotation</span><a href={SPOTIFY_PROFILE_URL} target="_blank" rel="noopener noreferrer" aria-label="Brian’s Spotify profile"><img src="/spotify/wordmark-white.svg" alt="Spotify" draggable={false} /></a></footer>
  </aside>;
}
