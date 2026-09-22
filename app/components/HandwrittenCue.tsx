"use client";

import { useId, type CSSProperties } from "react";
import { manicGlyphs } from "./manicVariants";
import "./handwrittenCue.css";

export type HandwrittenCueKind = "swipe-right" | "drag";
type Props = { kind: HandwrittenCueKind; className?: string; style?: CSSProperties; paused?: boolean };

/** Use real alternate glyphs, not distorted copies or random per-frame changes. */
export function ManicLettering({ text, x = 124, y = 48, seed }: { text: string; x?: number; y?: number; seed?: string | number }) {
  // React's stable instance ID gives identical labels different handwriting,
  // while preserving the exact glyph choices through hydration and animation.
  const instanceId = useId();
  return <text className="handwritten-cue__letters" x={x} y={y} textAnchor="middle" xmlSpace="preserve">
    {manicGlyphs(text, seed ?? `${instanceId}:${text}`).map(({ letter, variant }, index) =>
      <tspan key={index} data-manic-variant={variant}>{letter}</tspan>)}
  </text>;
}

/** Decorative guidance only; the real gesture/action must remain accessible. */
export default function HandwrittenCue({ kind, className = "", style, paused = false }: Props) {
  return <span className={`handwritten-cue handwritten-cue--${kind} ${className}`}
    style={style} data-paused={paused || undefined} aria-hidden="true">
    <svg viewBox={kind === "drag" ? "0 0 248 150" : "0 0 248 128"} fill="none" focusable="false">
      <g className="handwritten-cue__float">
        {kind === "swipe-right" ? <>
          <g transform="rotate(-3 124 30)"><ManicLettering text="Swipe Right" /></g>
          <g className="handwritten-cue__arrow">
            <path d="M26 80C45 89 62 96 82 94S108 98 130 93S159 88 181 87Q202 88 218 82" />
            <path d="M203 71L221 82Q211 90 205 98" />
          </g>
        </> : <>
          <g transform="rotate(-3 124 30)"><ManicLettering text="Drag" y={42} /></g>
          <g className="handwritten-cue__arrow">
            <path d="M180 119C202 115 220 106 224 96C231 81 209 73 191 70S160 62 135 64S104 62 83 66C54 70 23 76 20 89S40 111 60 116Q80 121 101 119" />
            <path d="M85 108Q96 116 106 120L88 131" />
          </g>
        </>}
      </g>
    </svg>
  </span>;
}
