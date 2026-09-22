// Rectangular fabric with equal-sized checks; preserve the original Fluent pole.
function RacingFlagIcon() {
  return <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <g className="racing-flag-fabric">
      <rect x="5.5" y="3.5" width="10" height="6" rx=".15" fill="none" stroke="currentColor" />
      {Array.from({ length: 15 }, (_, index) => {
        const row = Math.floor(index / 5), column = index % 5;
        return (row + column) % 2 === 0
          ? <rect key={index} x={5.5 + column * 2} y={3.5 + row * 2} width="2" height="2" /> : null;
      })}
    </g>
    <path className="racing-flag-pole" d="M5 3.5a.5.5 0 0 1 1 0v14a.5.5 0 0 1-1 0v-14Z" />
  </svg>;
}

export type DesktopApp = "terminal" | "help" | "recycle" | "spotify" | "notes" | "f1";
export const DESKTOP_APP_ORDER: DesktopApp[] = ["terminal", "notes", "f1", "help", "spotify", "recycle"];
export const DESKTOP_APPS: { id: DesktopApp; name: string; description: string }[] = [
  { id: "recycle", name: "Trash", description: "Empty Trash" },
  { id: "help", name: "Help", description: "Terminal command reference" },
  { id: "terminal", name: "Terminal", description: "GitHub Pulse and portfolio commands" },
  { id: "notes", name: "Notes", description: "Brian's personal bulletin board" },
  { id: "f1", name: "F1 Forecast", description: "Formula 1 constructor standings and championship probabilities" },
  { id: "spotify", name: "Spotify", description: "Brian's Spotify profile" },
];
export const MAC_ICON_ASSETS = { terminal: "terminal.png", recycle: "trash.png", about: "contacts.png", contact: "mail.png", help: "help.png", notes: "notes.png" } as const;

export default function DesktopIcon({ name }: { name: DesktopApp }) {
  return <span className={`windows-app-icon windows-app-icon-${name}`} aria-hidden="true">
    {name === "f1" ? <RacingFlagIcon /> : <img src={name === "spotify" ? "/spotify/icon-primary.svg" : `/macos-icons/${MAC_ICON_ASSETS[name]}`} alt="" draggable={false} />}
  </span>;
}
