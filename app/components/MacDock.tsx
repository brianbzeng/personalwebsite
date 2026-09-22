"use client";

import { useEffect, useRef, useState, type CSSProperties, type MouseEvent as ReactMouseEvent } from "react";
import DesktopIcon, { DESKTOP_APPS, type DesktopApp } from "./DesktopIcon";
import { dockLayout } from "./macDesktopState";
import { SPOTIFY_PROFILE_URL } from "./spotifyData";

type DockApp = DesktopApp | "spotify";
const APPS: DockApp[] = ["terminal", "notes", "f1", "help", "spotify", "recycle"];
type Props = { onLaunch: (app: DesktopApp) => void; onExternalLaunch: () => void; onAppContextMenu: (event: ReactMouseEvent<HTMLElement>, app: DesktopApp) => void; running: DesktopApp[]; nearBottom: boolean };

export default function MacDock({ onLaunch, onExternalLaunch, onAppContextMenu, running, nearBottom }: Props) {
  const [shown, setShown] = useState(false);
  const [pointer, setPointer] = useState<number | null>(null);
  const [size, setSize] = useState(52);
  const [bouncing, setBouncing] = useState<DockApp | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const nearBottomRef = useRef(nearBottom);
  const wasNearBottom = useRef(false);
  nearBottomRef.current = nearBottom;
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const layout = dockLayout(pointer, APPS.length, size, 10);

  function reveal() {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    setShown(true);
  }
  function hideLater(delay = 250) {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    hideTimer.current = setTimeout(() => {
      if (!nearBottomRef.current && !listRef.current?.contains(document.activeElement) && !listRef.current?.matches(":hover")) { setShown(false); setPointer(null); }
    }, delay);
  }
  useEffect(() => {
    return () => { if (hideTimer.current) clearTimeout(hideTimer.current); if (bounceTimer.current) clearTimeout(bounceTimer.current); };
  }, []);

  useEffect(() => {
    if (nearBottom) reveal();
    else if (wasNearBottom.current) hideLater();
    wasNearBottom.current = nearBottom;
  }, [nearBottom]);

  return <div className="mac-dock-region" onPointerEnter={reveal} onPointerLeave={() => { setPointer(null); hideLater(); }}>
    <button type="button" className="mac-dock-trigger" aria-label="Show Dock" aria-expanded={shown} onPointerEnter={reveal} onFocus={reveal} onClick={reveal} />
    <nav className={"mac-dock " + (shown ? "is-visible" : "")} aria-label="Dock" onFocus={reveal}
      onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node)) hideLater(); }}
      style={{ "--dock-expansion": layout.expansion / 2 + "px" } as CSSProperties}>
      <div className="mac-dock-items" ref={listRef} onPointerMove={(event) => {
        if (event.pointerType === "touch") return;
        const rect = event.currentTarget.getBoundingClientRect();
        const button = event.currentTarget.querySelector<HTMLElement>(".mac-dock-app");
        if (button) setSize(button.offsetWidth);
        setPointer(event.clientX - rect.left);
      }} onPointerLeave={() => setPointer(null)} onKeyDown={(event) => {
        const buttons = Array.from(event.currentTarget.querySelectorAll<HTMLElement>("button, a[href]"));
        const index = buttons.indexOf(document.activeElement as HTMLElement);
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          event.preventDefault(); buttons[(index + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length]?.focus();
        }
        if (event.key === "Escape") { (document.activeElement as HTMLElement)?.blur(); setShown(false); setPointer(null); }
      }}>
        {APPS.map((id, index) => {
          const name = id === "spotify" ? "Spotify" : DESKTOP_APPS.find((app) => app.id === id)!.name;
          const props = {
            className: "mac-dock-app " + (id === "recycle" ? "mac-dock-trash " : "") + (id !== "spotify" && running.includes(id) ? "is-running " : "") + (bouncing === id ? "is-bouncing" : ""),
            "aria-label": name,
            onContextMenu: (event: ReactMouseEvent<HTMLElement>) => onAppContextMenu(event, id),
            style: { "--icon-scale": layout.scales[index], transform: "translateX(" + layout.offsets[index] + "px)" } as CSSProperties,
            onClick: () => {
              if (id !== "spotify") onLaunch(id);
              else onExternalLaunch();
              setBouncing(id);
              if (bounceTimer.current) clearTimeout(bounceTimer.current);
              bounceTimer.current = setTimeout(() => setBouncing(null), 650);
            },
          };
          const contents = <>
            <span className="mac-dock-tooltip">{name}</span>
            <span className="mac-dock-icon"><DesktopIcon name={id} /></span>
            <span className="mac-dock-indicator" aria-hidden="true" />
          </>;
          return id === "spotify"
            ? <a key={id} {...props} href={SPOTIFY_PROFILE_URL} target="_blank" rel="noopener noreferrer">{contents}</a>
            : <button key={id} {...props} type="button">{contents}</button>;
        })}
      </div>
    </nav>
  </div>;
}
