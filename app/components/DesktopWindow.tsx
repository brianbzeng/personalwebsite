"use client";

import { useEffect, useLayoutEffect, useRef, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import { Dismiss16Regular } from "@fluentui/react-icons/svg/dismiss";
import { Square16Regular } from "@fluentui/react-icons/svg/square";
import { Subtract16Regular } from "@fluentui/react-icons/svg/subtract";
import { WindowMultiple24Regular } from "@fluentui/react-icons/svg/window-multiple";
import { clamp, fitFrame, fitFrameToArea, INITIAL_FRAME, modeFrame, type WindowFrame, type WindowMode } from "./desktopState";

type Props = {
  className?: string;
  initialFrame?: WindowFrame;
  minimumSize?: { width: number; height: number };
  title: string; children: ReactNode; titlebar: ReactNode; active: boolean; foreground: boolean; minimized: boolean; zIndex: number;
  onActivate: () => void; onMinimize: () => void; onClose: () => void;
};

export default function DesktopWindow({ className = "", initialFrame = INITIAL_FRAME, minimumSize, title, children, titlebar, active, foreground, minimized, zIndex, onActivate, onMinimize, onClose }: Props) {
  const windowRef = useRef<HTMLElement>(null);
  const cleanupRef = useRef<() => void>(() => {});
  const [normal, setNormal] = useState<WindowFrame>(() => fitFrame(initialFrame));
  const [mode, setMode] = useState<WindowMode>("normal");
  const [snapPreview, setSnapPreview] = useState<WindowMode | null>(null);
  const [snapMenu, setSnapMenu] = useState(false);
  const frame = modeFrame(mode, normal);

  useEffect(() => () => cleanupRef.current(), []);
  const minimumWidth = minimumSize?.width;
  const minimumHeight = minimumSize?.height;
  useLayoutEffect(() => {
    const area = windowRef.current?.parentElement;
    if (!area || minimumWidth === undefined || minimumHeight === undefined) return;
    const fit = () => {
      setNormal((current) => {
        const next = fitFrameToArea(current, { width: area.clientWidth, height: area.clientHeight }, { width: minimumWidth, height: minimumHeight });
        return next.x === current.x && next.y === current.y && next.width === current.width && next.height === current.height ? current : next;
      });
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(area);
    return () => observer.disconnect();
  }, [minimumWidth, minimumHeight]);

  function maximize() { setMode((current) => current === "maximized" ? "normal" : "maximized"); setSnapMenu(false); }

  function beginAction(event: ReactPointerEvent<HTMLElement>, edge?: string) {
    if (event.button !== 0 || (!edge && (event.target as HTMLElement).closest("button, [role=tablist], input, textarea, select, a, [data-window-no-drag]"))) return;
    const area = windowRef.current?.parentElement?.getBoundingClientRect();
    if (!area) return;
    event.preventDefault();
    onActivate();
    setSnapMenu(false);
    cleanupRef.current();
    const startX = event.clientX;
    const startY = event.clientY;
    let start = frame;
    let moved = false;
    let pendingSnap: WindowMode | null = null;
    const minWidth = Math.min((minimumWidth ?? 440) / area.width, 1);
    const minHeight = Math.min((minimumHeight ?? 260) / area.height, 1);
    function move(e: PointerEvent) {
      if (!moved && Math.hypot(e.clientX - startX, e.clientY - startY) < 4) return;
      if (!moved && !edge && mode !== "normal") {
        const ratio = clamp((startX - area!.left) / area!.width, 0, 1);
        start = fitFrame({ ...normal, x: ratio - normal.width * ratio, y: (startY - area!.top - 20) / area!.height }, minWidth, minHeight);
        setMode("normal");
      }
      moved = true;
      const dx = (e.clientX - startX) / area!.width;
      const dy = (e.clientY - startY) / area!.height;
      if (!edge) {
        setNormal(fitFrame({ ...start, x: start.x + dx, y: start.y + dy }, minWidth, minHeight));
        pendingSnap = e.clientY <= area!.top + 8 ? "maximized" : e.clientX <= area!.left + 10 ? "left" : e.clientX >= area!.right - 10 ? "right" : null;
        setSnapPreview(pendingSnap);
      } else {
        const next = { ...start };
        if (edge.includes("e")) next.width = clamp(start.width + dx, minWidth, 1 - start.x);
        if (edge.includes("s")) next.height = clamp(start.height + dy, minHeight, 1 - start.y);
        if (edge.includes("w")) { next.x = clamp(start.x + dx, 0, start.x + start.width - minWidth); next.width = start.width + start.x - next.x; }
        if (edge.includes("n")) { next.y = clamp(start.y + dy, 0, start.y + start.height - minHeight); next.height = start.height + start.y - next.y; }
        setNormal(fitFrame(next, minWidth, minHeight));
      }
    }
    function stop() { if (moved && pendingSnap) setMode(pendingSnap); setSnapPreview(null); cleanupRef.current(); }
    function cancel() { setSnapPreview(null); cleanupRef.current(); }
    cleanupRef.current = () => {
      window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", stop);
      window.removeEventListener("pointercancel", cancel); window.removeEventListener("blur", cancel);
    };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", stop);
    window.addEventListener("pointercancel", cancel); window.addEventListener("blur", cancel);
  }

  return <>
    {snapPreview && <div className={`win-snap-preview win-snap-${snapPreview}`} aria-hidden="true" />}
    <section
      ref={windowRef}
      className={`win-window ${className} ${active ? "is-focused" : ""} ${foreground ? "is-foreground" : ""} ${mode === "maximized" ? "is-maximized" : ""} ${mode === "fullscreen" ? "is-fullscreen" : ""} ${minimized ? "is-minimized" : ""}`}
      aria-label={title}
      aria-hidden={minimized}
      inert={minimized}
      tabIndex={-1}
      style={{ left: `${frame.x * 100}%`, top: `${frame.y * 100}%`, width: `${frame.width * 100}%`, height: `${frame.height * 100}%`, zIndex }}
      onPointerDown={onActivate}
      onFocusCapture={onActivate}
      onKeyDown={(event) => {
        if (event.key === "Escape") { setSnapMenu(false); if (mode === "fullscreen") setMode("normal"); }
        if (event.altKey && event.key === "F4") { event.preventDefault(); onClose(); }
      }}
    >
      <header className="win-titlebar" onPointerDown={(event) => beginAction(event)} onDoubleClick={(event) => { if (!(event.target as HTMLElement).closest("button, [role=tablist], input, textarea, select, a, [data-window-no-drag]")) maximize(); }}>
        <div className="win-caption-controls mac-traffic-lights">
          <button type="button" className="win-close" title="Close" aria-label={`Close ${title}`} onClick={onClose}><Dismiss16Regular /></button>
          <button type="button" title="Minimize" aria-label={`Minimize ${title}`} onClick={onMinimize}><Subtract16Regular /></button>
          <div className="win-maximize-group" onMouseEnter={() => setSnapMenu(true)} onMouseLeave={() => setSnapMenu(false)}>
            <button type="button" title={mode === "fullscreen" ? "Exit Full Screen" : "Enter Full Screen"} aria-label={`${mode === "fullscreen" ? "Exit full screen for" : "Enter full screen for"} ${title}`} onClick={() => { setMode((current) => current === "fullscreen" ? "normal" : "fullscreen"); setSnapMenu(false); }}>
              {mode === "fullscreen" ? <WindowMultiple24Regular /> : <Square16Regular />}
            </button>
            {snapMenu && <div className="win-snap-menu" aria-label="Move and resize">
              <button type="button" aria-label={`Snap ${title} left`} title="Left half" onClick={() => { setMode("left"); setSnapMenu(false); }}><span /></button>
              <button type="button" aria-label={`Snap ${title} right`} title="Right half" onClick={() => { setMode("right"); setSnapMenu(false); }}><span /></button>
              <button type="button" aria-label={`Fill desktop with ${title}`} title="Fill" onClick={() => { setMode("maximized"); setSnapMenu(false); }}><span /></button>
            </div>}
          </div>
        </div>
        {titlebar}
      </header>
      {children}
      {mode === "normal" && ["n", "s", "e", "w", "ne", "nw", "se", "sw"].map((edge) => <div key={edge} className={`win-resize win-resize-${edge}`} onPointerDown={(event) => beginAction(event, edge)} aria-hidden="true" />)}
    </section>
  </>;
}
