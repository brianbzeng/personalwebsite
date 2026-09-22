"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { MusicNote124Regular, MusicNote224Regular } from "@fluentui/react-icons/svg/music-note";
import { SPOTIFY_IDLE_REFRESH_MS, spotifyRefreshInterval } from "./spotifyRefresh";
import { speakerIsPlaying } from "./speakerPlayback";
import type { SpotifyFeed } from "./spotifyData";
import { createRingPicker, SPEAKER_RING_PATHS } from "./speakerRings";
import "./roomSpeakerActivity.css";

export type SpeakerPreviewMode = "playing" | "paused" | "live";
export function useSpeakerPlayback(enabled: boolean) {
  const [playing, setPlaying] = useState(false);
  const [status, setStatus] = useState("Not checked");
  useEffect(() => {
    setPlaying(false);
    if (!enabled || new URLSearchParams(location.search).get("capture") === "idle") return;
    let stopped = false, timer: ReturnType<typeof setTimeout> | undefined, expiry: ReturnType<typeof setTimeout> | undefined;
    let controller: AbortController | undefined;
    async function refresh() {
      clearTimeout(timer); clearTimeout(expiry);
      if (stopped || document.hidden) return;
      controller?.abort(); const request = new AbortController(); controller = request;
      const deadline = setTimeout(() => request.abort(), 12_000);
      let delay = SPOTIFY_IDLE_REFRESH_MS;
      try {
        const response = await fetch("/api/spotify", { cache: "no-store", signal: request.signal });
        if (!response.ok) throw new Error("Unavailable");
        const feed: SpotifyFeed = await response.json();
        if (stopped || controller !== request || request.signal.aborted) return;
        const active = speakerIsPlaying(feed);
        setPlaying(active);
        setStatus(active ? "Spotify · listening now" : feed.status === "disconnected" ? "Spotify · not connected" : feed.status !== "ready" ? "Spotify · unavailable" : "Spotify · paused or idle");
        delay = spotifyRefreshInterval(feed);
        if (active) {
          delay = Math.max(1000, feed.updatedAt + delay - Date.now());
          expiry = setTimeout(() => { setPlaying(false); setStatus("Spotify · refreshing"); }, delay);
        }
      } catch {
        if (!stopped && controller === request) { setPlaying(false); setStatus("Spotify · unavailable"); }
      } finally {
        clearTimeout(deadline);
        if (!stopped && controller === request) timer = setTimeout(refresh, delay);
      }
    }
    function visibility() {
      if (document.hidden) { clearTimeout(timer); clearTimeout(expiry); const pending = controller; controller = undefined; pending?.abort(); setPlaying(false); }
      else void refresh();
    }
    void refresh(); document.addEventListener("visibilitychange", visibility); window.addEventListener("online", refresh);
    return () => { stopped = true; clearTimeout(timer); clearTimeout(expiry); controller?.abort(); document.removeEventListener("visibilitychange", visibility); window.removeEventListener("online", refresh); };
  }, [enabled]);
  return { playing, status };
}

// Visible large-woofer front-cap centers, projected from the 1920×1080 camera.
const SPEAKERS = [[672.83, 483.60], [833.11, 428.19]];
export default function RoomSpeakerActivity({ playing, motion, visible }: { playing: boolean; motion: boolean; visible: boolean }) {
  const active = playing && motion && visible;
  const [running, setRunning] = useState(false);
  const [rings, setRings] = useState([0, 1, 2, 3, 4, 5]);
  const pickers = useRef<ReturnType<typeof createRingPicker>[]>([]);
  useEffect(() => {
    pickers.current = [createRingPicker(), createRingPicker()];
    setRings(Array.from({ length: 6 }, (_, i) => pickers.current[Math.floor(i / 3)]()));
  }, []);
  useEffect(() => {
    if (active) { setRunning(true); return; }
    // Let existing particles finish fading before freezing the loop.
    const timer = setTimeout(() => setRunning(false), 650); return () => clearTimeout(timer);
  }, [active]);
  return <svg className={`room-speaker-activity${active ? " is-active" : ""}${running ? " is-running" : ""}`} viewBox="0 0 1920 1080" aria-hidden="true" data-playing={active}>
    {/* Scale locally after translating: the cone centers never move. */}
    {SPEAKERS.map(([x, y], speaker) => <g key={speaker} transform={`translate(${x} ${y}) scale(.7)`}>
      {[0, 1, 2].map(i => <g key={`wave-${i}`} className="speaker-wave" data-ring-shape={rings[speaker * 3 + i]}
        style={{ "--delay": `${-i * 1.2 - speaker * .6}s` } as CSSProperties}
        onAnimationIteration={() => {
          // Change silhouette only at the invisible boundary between emissions.
          const shape = pickers.current[speaker]?.();
          if (shape !== undefined) setRings(current => current.map((value, index) => index === speaker * 3 + i ? shape : value));
        }}><path d={SPEAKER_RING_PATHS[rings[speaker * 3 + i]]} /></g>)}
      {[0, 1, 2].map(i => <g key={`note-${i}`} className="speaker-note" style={{ "--delay": `${-i * 1.6 - speaker * .8}s`, "--drift": `${-18 + i * 15}px`, "--tilt": `${-10 + i * 10}deg` } as CSSProperties}>
        {i === 1 ? <MusicNote224Regular x={-9} y={-18} width={22} height={22} /> : <MusicNote124Regular x={-9} y={-18} width={20} height={20} />}
      </g>)}
    </g>)}
  </svg>;
}
