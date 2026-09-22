"use client";

import { useEffect, useRef, useState } from 'react';
import { ManicLettering } from './HandwrittenCue';
import './activityCues.css';

export type CueRect = { x: number; y: number; width: number; height: number };
export type CueSide = 'top' | 'bottom' | 'left' | 'right';
export type CueGesture = 'point' | 'drag' | 'swipe-x' | 'swipe-left' | 'swipe-y';
export type CueSpec = {
  id: string;
  label: string;
  touchLabel?: string;
  selector?: string;
  /** Bounds are viewport pixels, not percentages or 3D world coordinates. */
  rect?: CueRect;
  side?: CueSide;
  /** Optional vertical aim along a side, e.g. a page's lower turning corner. */
  pointBias?: number;
  gesture?: CueGesture;
  touchGesture?: CueGesture;
  appearance?: 'arrow-only' | 'text-only';
  /** Fractions of the target bounds; narrows generous hit areas to visible art. */
  targetInset?: Partial<Record<CueSide, number>>;
  /** Optional larger/smaller cue, without scaling its pointer's overlap. */
  scale?: number;
  /** Normalized viewport center, useful for page-centered scroll guidance. */
  viewportAnchor?: { x: number; y: number };
  /** Keep a settled cue in place when its object lifts or rocks on hover. */
  freezeTarget?: boolean;
};
type CuePlacement = CueRect & { side: CueSide };
type ResolvedCue = { spec: CueSpec; label: string; target: CueRect; box: CuePlacement; textWidth: number };
type Props = {
  cues: CueSpec[]; sceneKey: string; ready: boolean; replayKey?: number;
  visibleMs?: number; allowReplay?: boolean; onComplete?: () => void;
  inputMode?: 'auto' | 'mouse' | 'touch';
  refined?: boolean;
  /** Fade both ends inside visibleMs, rather than appending the outro. */
  fadeIn?: boolean;
};

export const ACTIVITY_CUE_SETTLE_MS = 600;
export const ACTIVITY_CUE_VISIBLE_MS = 4000;
export const ACTIVITY_CUE_FADE_MS = 450;

export function insetCueTarget(rect: CueRect, inset: CueSpec['targetInset']): CueRect {
  if (!inset) return rect;
  const fraction = (value = 0) => Math.max(0, Math.min(.95, value));
  const left = fraction(inset.left);
  const top = fraction(inset.top);
  const right = Math.min(fraction(inset.right), .95 - left);
  const bottom = Math.min(fraction(inset.bottom), .95 - top);
  return { x: rect.x + rect.width * left, y: rect.y + rect.height * top,
    width: rect.width * (1 - left - right), height: rect.height * (1 - top - bottom) };
}

// Pure placement helpers are shared by all staged activities. A failed fit
// omits a note instead of putting handwriting over its point of interest.
export function cueRectsOverlap(a: CueRect, b: CueRect, gap = 0) {
  return a.x < b.x + b.width + gap && a.x + a.width + gap > b.x
    && a.y < b.y + b.height + gap && a.y + a.height + gap > b.y;
}

export function placeActivityCue(
  target: CueRect,
  viewport: { width: number; height: number },
  size: { width: number; height: number },
  preferred: CueSide = 'top',
  avoid: CueRect[] = [],
  verticalBias = .5,
): CuePlacement | null {
  const edge = 12;
  const clearance = 10;
  if (size.width > viewport.width - edge * 2 || size.height > viewport.height - edge * 2) return null;
  const sides: CueSide[] = [preferred, ...(['top', 'right', 'bottom', 'left'] as CueSide[]).filter(side => side !== preferred)];
  const clamp = (n: number, max: number) => Math.max(edge, Math.min(n, max - edge));
  for (const side of sides) {
    let x = target.x + (target.width - size.width) / 2;
    let y = target.y + target.height * verticalBias - size.height / 2;
    if (side === 'top') y = target.y - size.height - clearance;
    if (side === 'bottom') y = target.y + target.height + clearance;
    if (side === 'left') x = target.x - size.width - clearance;
    if (side === 'right') x = target.x + target.width + clearance;
    // Clamp only the cross axis. Clamping the main axis would cover the POI.
    if (side === 'top' || side === 'bottom') x = clamp(x, viewport.width - size.width);
    else y = clamp(y, viewport.height - size.height);
    const box = { x, y, ...size, side };
    if (x < edge || y < edge || x + size.width > viewport.width - edge || y + size.height > viewport.height - edge) continue;
    if (cueRectsOverlap(box, target, 6) || avoid.some(rect => cueRectsOverlap(box, rect, 6))) continue;
    return box;
  }
  return null;
}

/** Opacity is driven by visible elapsed time, so background tabs cannot eat it. */
export function activityCueEndMs(visibleMs: number, fadeIn = false) {
  return ACTIVITY_CUE_SETTLE_MS + visibleMs + (fadeIn ? 0 : ACTIVITY_CUE_FADE_MS);
}

export function activityCueOpacity(elapsed: number, visibleMs = ACTIVITY_CUE_VISIBLE_MS, fadeIn = false) {
  if (elapsed < ACTIVITY_CUE_SETTLE_MS) return 0;
  if (fadeIn) {
    const age = elapsed - ACTIVITY_CUE_SETTLE_MS;
    const ramp = Math.min(ACTIVITY_CUE_FADE_MS, visibleMs / 2);
    if (ramp <= 0) return 0;
    return Math.max(0, Math.min(1, age / ramp, (visibleMs - age) / ramp));
  }
  const fadeElapsed = elapsed - ACTIVITY_CUE_SETTLE_MS - visibleMs;
  return Math.max(0, Math.min(1, 1 - fadeElapsed / ACTIVITY_CUE_FADE_MS));
}

export function placeViewportCue(target: CueRect, viewport: { width: number; height: number },
  size: { width: number; height: number }, anchor: { x: number; y: number },
  side: CueSide = 'right', avoid: CueRect[] = []): CuePlacement | null {
  const edge = 12;
  if (size.width > viewport.width - edge * 2 || size.height > viewport.height - edge * 2) return null;
  const box = { x: Math.max(edge, Math.min(viewport.width * anchor.x - size.width / 2, viewport.width - size.width - edge)),
    y: Math.max(edge, Math.min(viewport.height * anchor.y - size.height / 2, viewport.height - size.height - edge)), ...size, side };
  return cueRectsOverlap(box, target, 6) || avoid.some(rect => cueRectsOverlap(box, rect, 6)) ? null : box;
}

/** Shorten only the shaft: preserve the arrowhead and exact target contact. */
export function shortenCueTail(start: { x: number; y: number }, tip: { x: number; y: number }, refined: boolean) {
  return refined ? { x: (start.x + tip.x) / 2, y: (start.y + tip.y) / 2 } : start;
}

export function stableCueTarget(spec: CueSpec, rect: CueRect, cache: Map<string, CueRect>, settled: boolean): CueRect {
  if (cache.has(spec.id)) return cache.get(spec.id)!;
  const target = insetCueTarget(rect, spec.targetInset);
  if (settled) cache.set(spec.id, { ...target });
  return target;
}

function pointArrow({ box, target, spec }: ResolvedCue, refined: boolean) {
  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;
  let start = { x: cx, y: cy };
  let tip = { x: target.x + target.width / 2, y: target.y + 1.5 };
  let direction = { x: 0, y: 1 };
  if (box.side === 'top') start = { x: cx, y: box.y + box.height - 6 };
  if (box.side === 'bottom') {
    start = { x: cx, y: box.y + 4 };
    tip = { x: target.x + target.width / 2, y: target.y + target.height - 1.5 };
    direction = { x: 0, y: -1 };
  }
  if (box.side === 'left') {
    start = { x: box.x + box.width - 4, y: cy };
    tip = { x: target.x + 1.5, y: target.y + target.height * (spec.pointBias ?? .5) };
    direction = { x: 1, y: 0 };
  }
  if (box.side === 'right') {
    start = { x: box.x + 4, y: cy };
    tip = { x: target.x + target.width - 1.5, y: target.y + target.height * (spec.pointBias ?? .5) };
    direction = { x: -1, y: 0 };
  }
  if (spec.appearance === 'arrow-only') {
    // Without a caption, use the whole compact slot for the arrow's shaft.
    if (box.side === 'top') start.y = box.y + 4;
    if (box.side === 'bottom') start.y = box.y + box.height - 4;
    if (box.side === 'left') start.x = box.x + 4;
    if (box.side === 'right') start.x = box.x + box.width - 4;
  }
  start = shortenCueTail(start, tip, refined);
  const bend = (box.side === 'top' || box.side === 'bottom' ? 4 : -4) * (refined ? .5 : 1);
  const control = { x: (start.x + tip.x) / 2 + direction.y * bend, y: (start.y + tip.y) / 2 + direction.x * bend };
  const back = { x: tip.x - direction.x * 6, y: tip.y - direction.y * 6 };
  return <path d={`M${start.x} ${start.y} Q${control.x} ${control.y} ${tip.x} ${tip.y} M${back.x - direction.y * 3.5} ${back.y + direction.x * 3.5} L${tip.x} ${tip.y} L${back.x + direction.y * 3.5} ${back.y - direction.x * 3.5}`} />;
}

function Gesture({ kind }: { kind: CueSpec['gesture'] }) {
  if (kind === 'drag') return <g>
    <path d="M150 96C178 90 191 80 179 70S132 60 101 62S34 66 25 79S47 98 76 99" />
    <path d="M65 88L80 99L66 107" />
  </g>;
  if (kind === 'swipe-y') return <g>
    <path d="M103 57Q95 70 100 80T98 106M89 65L103 55L111 68M88 96L98 108L110 96" />
  </g>;
  return <g transform={kind === 'swipe-left' ? 'translate(200 0) scale(-1 1)' : undefined}>
    <path d="M23 79Q48 86 70 82T114 82Q145 77 174 80M162 69L178 80L165 90" />
  </g>;
}

export default function ActivityCues({ cues, sceneKey, ready, replayKey = 0,
  visibleMs = ACTIVITY_CUE_VISIBLE_MS, allowReplay = true, onComplete, inputMode = 'auto', refined = false, fadeIn = false }: Props) {
  const [fontReady, setFontReady] = useState(false);
  const [deviceTouch, setTouch] = useState(false);
  const touch = inputMode === 'auto' ? deviceTouch : inputMode === 'touch';
  const [manualReplay, setManualReplay] = useState(0);
  const [visual, setVisual] = useState({ key: '', opacity: 0, done: false });
  const [resolved, setResolved] = useState<ResolvedCue[]>([]);
  const rootRef = useRef<HTMLDivElement>(null);
  const cuesRef = useRef(cues);
  const readyRef = useRef(ready);
  const resolvedRef = useRef<ResolvedCue[]>([]);
  const clock = useRef({ key: '', elapsed: 0 });
  const completedKey = useRef('');
  const dismissedKey = useRef('');
  const layoutKey = useRef('');
  const completionRef = useRef(onComplete);
  const key = JSON.stringify([sceneKey, allowReplay ? replayKey : 0, allowReplay ? manualReplay : 0, fadeIn]);

  useEffect(() => { cuesRef.current = cues; }, [cues]);
  useEffect(() => { readyRef.current = ready; }, [ready]);
  useEffect(() => { completionRef.current = onComplete; }, [onComplete]);

  useEffect(() => {
    // Capture the start of input, before the object begins moving. Never
    // prevent the gesture or wait for a drag threshold / pointer release.
    const dismiss = (event: Event) => {
      if (!readyRef.current || completedKey.current === key) return;
      if (event instanceof KeyboardEvent && !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Enter', ' ', 'Escape', 'PageUp', 'PageDown', 'Home', 'End'].includes(event.key)) return;
      dismissedKey.current = key;
      if (rootRef.current) {
        rootRef.current.style.opacity = '0';
        rootRef.current.dataset.state = 'done';
      }
      clock.current = { key, elapsed: activityCueEndMs(visibleMs, fadeIn) };
      setVisual({ key, opacity: 0, done: true });
      completedKey.current = key;
      completionRef.current?.();
    };
    const events = ['pointerdown', 'touchstart', 'wheel', 'keydown', 'resize'] as const;
    for (const event of events) window.addEventListener(event, dismiss, { capture: true, passive: true });
    return () => {
      for (const event of events) window.removeEventListener(event, dismiss, true);
    };
  }, [key, visibleMs, fadeIn]);

  useEffect(() => {
    if (!allowReplay) return;
    const replay = () => setManualReplay(value => value + 1);
    window.addEventListener('bz-replay-cues', replay);
    return () => window.removeEventListener('bz-replay-cues', replay);
  }, [allowReplay]);

  useEffect(() => {
    let cancelled = false;
    const media = window.matchMedia('(pointer: coarse)');
    const updateTouch = () => setTouch(media.matches);
    updateTouch();
    media.addEventListener('change', updateTouch);
    // Explicit requests are necessary: fonts.ready alone can resolve before
    // these SVG glyphs have mounted and requested their alternate faces.
    const families = ['Manic Regular', 'Manic Alternate One', 'Manic Alternate Two', 'Manic Alternate Three'];
    Promise.all(families.map(family => document.fonts.load(`24px "${family}"`, 'Click Tap Hover Drag Swipe Scroll Type')))
      .then(() => document.fonts.ready)
      .then(() => { if (!cancelled) setFontReady(true); })
      .catch(() => { /* A missing handwriting font must not become a fallback-font cue. */ });
    return () => {
      cancelled = true;
      media.removeEventListener('change', updateTouch);
    };
  }, []);

  useEffect(() => {
    let frame = 0;
    let lastMeasure = -Infinity;
    let previous = '';
    const frozenTargets = new Map<string, CueRect>();
    let frozenViewport = '';
    const textMeasure = document.createElement('canvas').getContext('2d');
    const families = ['Manic Regular', 'Manic Alternate One', 'Manic Alternate Two', 'Manic Alternate Three'];
    const labelWidth = (label: string) => Math.max(200, Array.from(label).reduce((sum, letter) => {
      // Reserve the widest authentic variant so random lettering cannot spill
      // beyond the placement box or drift onto the object.
      const widths = families.map(family => {
        if (!textMeasure) return 30;
        textMeasure.font = `43px "${family}"`;
        return textMeasure.measureText(letter).width;
      });
      return sum + Math.max(...widths);
    }, 28));
    const measure = (now: number) => {
      if (dismissedKey.current === key || layoutKey.current === key) return;
      if (!readyRef.current || !fontReady) {
        frame = requestAnimationFrame(measure);
        return;
      }
      if (now - lastMeasure >= 80) {
        lastMeasure = now;
        const viewport = { width: window.innerWidth, height: window.innerHeight };
        const viewportKey = `${viewport.width}:${viewport.height}`;
        if (viewportKey !== frozenViewport) { frozenTargets.clear(); frozenViewport = viewportKey; }
        const targets = cuesRef.current.flatMap(spec => {
          let rect = frozenTargets.get(spec.id) ?? spec.rect;
          if (!rect && spec.selector) {
            const element = document.querySelector(spec.selector);
            if (element) {
              const bounds = element.getBoundingClientRect();
              rect = { x: bounds.x, y: bounds.y, width: bounds.width, height: bounds.height };
            }
          }
          // A standalone scroll gesture needs no artificial POI or DOM selector.
          if (!rect && spec.viewportAnchor) rect = { x: 0, y: 0, width: 1, height: 1 };
          if (!rect || rect.width <= 0 || rect.height <= 0 || rect.x >= viewport.width || rect.y >= viewport.height || rect.x + rect.width <= 0 || rect.y + rect.height <= 0) return [];
          rect = stableCueTarget(spec, rect, frozenTargets, readyRef.current && fontReady);
          return [{ spec, rect }];
        });
        const next: ResolvedCue[] = [];
        for (const { spec: sourceSpec, rect } of targets) {
          const spec = touch && sourceSpec.touchGesture ? { ...sourceSpec, gesture: sourceSpec.touchGesture } : sourceSpec;
          const label = touch && spec.touchLabel ? spec.touchLabel : spec.label;
          const compact = viewport.height < 600;
          const arrowOnly = spec.appearance === 'arrow-only';
          const hasGesture = spec.appearance !== 'text-only' && spec.gesture && spec.gesture !== 'point';
          const textWidth = hasGesture ? 200 : labelWidth(label);
          const width = arrowOnly ? 28 : hasGesture
            ? Math.min(compact ? 125 : 145, Math.max(compact ? 72 : 84, label.length * (compact ? 7 : 8.5) + 30))
            : textWidth * (compact ? .46 : .52);
          const height = arrowOnly ? 28 : hasGesture ? width * .57 : 34;
          const scale = Math.max(.5, Math.min(2, spec.scale ?? 1));
          const size = { width: width * scale, height: height * scale };
          const avoid = [...targets.filter(other => other.spec.id !== spec.id).map(other => other.rect), ...next.map(cue => cue.box)];
          const box = spec.viewportAnchor
            ? placeViewportCue(rect, viewport, size, spec.viewportAnchor, spec.side, avoid)
            : placeActivityCue(rect, viewport, size, spec.side, avoid, hasGesture ? .5 : spec.pointBias ?? .5);
          if (box) next.push({ spec, label, target: rect, box, textWidth });
        }
        // Geometry updates never restart the lifetime clock.
        const signature = JSON.stringify(next);
        resolvedRef.current = next;
        if (signature !== previous) { previous = signature; setResolved(next); }
        // Freeze the complete layout, not just target bounds. Hover, dragging,
        // and moving neighboring objects cannot move text or arrow tips.
        if (next.length > 0) { layoutKey.current = key; return; }
      }
      const done = clock.current.key === key
        && clock.current.elapsed >= activityCueEndMs(visibleMs, fadeIn);
      if (!done) frame = requestAnimationFrame(measure);
    };
    frame = requestAnimationFrame(measure);
    return () => cancelAnimationFrame(frame);
  }, [key, touch, fontReady, visibleMs, fadeIn]);

  useEffect(() => {
    if (clock.current.key !== key) clock.current = { key, elapsed: 0 };
    if (!ready || !fontReady) return;
    let frame = 0;
    let last = performance.now();
    const resetTick = () => { last = performance.now(); };
    document.addEventListener('visibilitychange', resetTick);
    const tick = (now: number) => {
      if (dismissedKey.current === key) return;
      const delta = now - last;
      last = now;
      const blocked = document.hidden || !!document.querySelector('dialog[open]') || resolvedRef.current.length === 0;
      if (!blocked) clock.current.elapsed += delta;
      const opacity = blocked ? 0 : activityCueOpacity(clock.current.elapsed, visibleMs, fadeIn);
      const done = clock.current.elapsed >= activityCueEndMs(visibleMs, fadeIn);
      setVisual(previous => previous.key === key && previous.opacity === opacity && previous.done === done
        ? previous : { key, opacity, done });
      if (done && completedKey.current !== key) {
        completedKey.current = key;
        completionRef.current?.();
      }
      if (!done) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener('visibilitychange', resetTick);
    };
    // Deliberately exclude cues/rects: updated bounds do not replay notes.
  }, [key, ready, fontReady, visibleMs, fadeIn]);

  const opacity = ready && fontReady && visual.key === key && dismissedKey.current !== key ? visual.opacity : 0;
  const state = !ready || !fontReady || visual.key !== key ? 'waiting'
    : opacity >= 1 ? 'visible' : opacity > 0 ? 'fading' : visual.done ? 'done' : 'waiting';
  return <div ref={rootRef} className="activity-cues" aria-hidden="true" style={{ opacity }} data-scene={sceneKey} data-state={state} data-refined={refined}>
    <svg className="activity-cues__canvas" width="100%" height="100%" focusable="false">
      {resolved.filter(cue => cues.some(spec => spec.id === cue.spec.id)).map(cue => {
        const arrowOnly = cue.spec.appearance === 'arrow-only';
        const textOnly = cue.spec.appearance === 'text-only';
        const hasGesture = !textOnly && cue.spec.gesture && cue.spec.gesture !== 'point';
        return <g key={cue.spec.id} data-cue={cue.spec.id} data-appearance={cue.spec.appearance ?? 'normal'} className="activity-cues__note">
        {!textOnly && (arrowOnly || !hasGesture) && <g className="activity-cues__point">{pointArrow(cue, refined)}</g>}
        {!arrowOnly &&
        <svg x={cue.box.x} y={cue.box.y} width={cue.box.width} height={cue.box.height}
          viewBox={`0 0 ${cue.textWidth} ${hasGesture ? 114 : 65}`} overflow="visible">
          <g className="activity-cues__float">
            <g transform={`rotate(-3 ${cue.textWidth / 2} 28)`}><ManicLettering text={cue.label} x={cue.textWidth / 2} y={hasGesture ? 41 : 46} /></g>
            {hasGesture && <g className="activity-cues__gesture"><Gesture kind={cue.spec.gesture} /></g>}
          </g>
        </svg>}
      </g>; })}
    </svg>
  </div>;
}
