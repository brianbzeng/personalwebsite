/**
 * Camera moves are prerendered at a fixed pace. A playback-rate curve gives them
 * acceleration without re-rendering: launch already moving, speed up through the
 * middle of the move, then ease off so the landing cut is not abrupt.
 */
export type MotionProfile = {
  /** Rate on the first frame. */
  start: number;
  /** Fastest rate, reached at `peakAt`. */
  peak: number;
  /** Rate on the final frame. */
  end: number;
  /** Clip progress (0..1) where the peak lands. */
  peakAt: number;
};

/** Room ↔ scene moves (3–5 s clips). */
export const SCENE_MOTION: MotionProfile = { start: 1.5, peak: 3.2, end: 1.6, peakAt: 0.5 };
/** Shelf cubby moves (1.5 s clips) are already brisk; push them less. */
export const SHELF_MOTION: MotionProfile = { start: 1.3, peak: 2.2, end: 1.4, peakAt: 0.5 };

/** Playback rate for a clip at `progress` (0..1). Accelerates into the peak, decelerates out of it. */
export function transitionRate(progress: number, profile: MotionProfile = SCENE_MOTION) {
  const p = Math.min(1, Math.max(0, progress));
  if (p < profile.peakAt) {
    const t = p / profile.peakAt;
    return profile.start + (profile.peak - profile.start) * t * t;
  }
  const t = (p - profile.peakAt) / (1 - profile.peakAt);
  return profile.peak + (profile.end - profile.peak) * (1 - (1 - t) * (1 - t));
}

/** Wall-clock seconds the curve takes to play a clip of `seconds`. */
export function acceleratedDuration(seconds: number, profile: MotionProfile = SCENE_MOTION, steps = 200) {
  let total = 0;
  for (let i = 0; i < steps; i++) total += 1 / transitionRate((i + 0.5) / steps, profile);
  return (seconds * total) / steps;
}

type RateVideo = Pick<HTMLVideoElement, 'playbackRate' | 'currentTime' | 'duration' | 'ended' | 'addEventListener' | 'removeEventListener'>;

/** Follow the curve while `video` plays. Returns a stop function. */
export function driveTransitionRate(video: RateVideo, profile: MotionProfile = SCENE_MOTION) {
  let frame = 0, active = true;
  video.playbackRate = transitionRate(0, profile);
  const tick = () => {
    if (!active) return;
    if (!video.ended && Number.isFinite(video.duration) && video.duration > 0) {
      const rate = transitionRate(video.currentTime / video.duration, profile);
      if (Math.abs(rate - video.playbackRate) > 0.01) video.playbackRate = rate;
    }
    frame = requestAnimationFrame(tick);
  };
  // Some browsers reset the rate when the source is first bound.
  const rebase = () => { if (active) video.playbackRate = transitionRate(video.currentTime / (video.duration || 1), profile); };
  video.addEventListener('loadedmetadata', rebase);
  video.addEventListener('play', rebase);
  frame = requestAnimationFrame(tick);
  return () => {
    active = false;
    cancelAnimationFrame(frame);
    video.removeEventListener('loadedmetadata', rebase);
    video.removeEventListener('play', rebase);
  };
}
