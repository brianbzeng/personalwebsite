import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync, statSync } from "node:fs";
import { MAC_TERMINAL_PROMPT, DOCK_REVEAL_FRACTION, isInDockRevealRegion, dockLayout, terminalGridSize } from "../app/components/macDesktopState.ts";
import { modeFrame } from "../app/components/desktopState.ts";
import { APP_COMMANDS, resolveTerminalCommand } from "../app/components/terminalContent.ts";
import { SPOTIFY_PROFILE_URL } from "../app/components/spotifyData.ts";

test("Mac prompt preserves the existing inline portfolio command workflow", () => {
  assert.equal(MAC_TERMINAL_PROMPT, "brian@Mac ~ % ");
  assert.deepEqual(Object.values(APP_COMMANDS), ["help", "python pulse.py", "python about.txt", "python contact.txt", "python agents.txt"]);
  for (const command of [...Object.values(APP_COMMANDS), "clear"]) assert.ok(resolveTerminalCommand(command));
  assert.equal(resolveTerminalCommand("python pulse.py").pulse, true);
});

test("Dock rests at native sizes and magnification is bounded and symmetric", () => {
  assert.deepEqual(dockLayout(null, 5), { scales: [1, 1, 1, 1, 1], offsets: [0, 0, 0, 0, 0], expansion: 0 });
  const middle = 2 * 62 + 26;
  const layout = dockLayout(middle, 5);
  assert.equal(layout.scales[2], 1.55);
  assert.equal(layout.scales[0], layout.scales[4]);
  assert.equal(layout.scales[1], layout.scales[3]);
  assert.ok(Math.abs(layout.offsets[0] + layout.offsets[4]) < 1e-9);
  assert.ok(Math.abs(layout.offsets[2]) < 1e-9);
  for (const x of [-500, 0, middle, 310, 1000, NaN, Infinity]) {
    const { scales, offsets, expansion } = dockLayout(x, 5);
    assert.ok(scales.every((scale) => scale >= 1 && scale <= 1.55));
    assert.ok(offsets.every(Number.isFinite));
    assert.ok(Number.isFinite(expansion));
  }
});

test("Dock reveals throughout precisely the bottom eight percent of the desktop", () => {
  assert.equal(DOCK_REVEAL_FRACTION, .08);
  for (const [top, height] of [[0, 1080], [64, 720], [120, 450]]) {
    const threshold = top + height * .92;
    assert.equal(isInDockRevealRegion(threshold - .01, top, height), false);
    assert.equal(isInDockRevealRegion(threshold, top, height), true);
    assert.equal(isInDockRevealRegion(top + height, top, height), true);
    assert.equal(isInDockRevealRegion(top + height + 1, top, height), false);
  }
  for (const height of [0, -1, NaN, Infinity]) assert.equal(isInDockRevealRegion(100, 0, height), false);
});

test("Terminal uses a single session with a folder title and no tab creation controls", () => {
  const terminal = readFileSync(new URL("../app/components/DesktopTerminal.tsx", import.meta.url), "utf8");
  const desktop = readFileSync(new URL("../app/components/MonitorDesktop.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(terminal, /newTab|closeTab|role="tablist"|role="tabpanel"|New tab|setTabs/);
  assert.doesNotMatch(desktop, /newTab|New Tab/);
  assert.equal((terminal.match(/<TerminalSession\b/g) ?? []).length, 1);
  assert.match(terminal, /src="\/macos-icons\/folder\.png"/);
  assert.match(terminal, /PORTFOLIO_GREETING_ART/);
});

test("Terminal title shows a live character grid and aligns after the left window controls", () => {
  assert.deepEqual(terminalGridSize(960, 540, 8, 18), { columns: 120, rows: 30 });
  assert.deepEqual(terminalGridSize(719, 399, 8, 18), { columns: 89, rows: 22 });
  assert.deepEqual(terminalGridSize(960, 540, 10, 22.5), { columns: 96, rows: 24 });
  assert.deepEqual(terminalGridSize(1, 1, 8, 18), { columns: 1, rows: 1 });
  for (const invalid of [0, -1, NaN, Infinity]) {
    assert.equal(terminalGridSize(invalid, 540, 8, 18), null);
    assert.equal(terminalGridSize(960, invalid, 8, 18), null);
    assert.equal(terminalGridSize(960, 540, invalid, 18), null);
    assert.equal(terminalGridSize(960, 540, 8, invalid), null);
  }
  const terminal = readFileSync(new URL("../app/components/DesktopTerminal.tsx", import.meta.url), "utf8");
  const css = readFileSync(new URL("../app/components/macosDesktop.css", import.meta.url), "utf8");
  assert.match(terminal, /observer.observe\(probe\)/);
  assert.match(terminal, /body.clientHeight - pixels\(styles.paddingTop\)/);
  assert.match(terminal, /\{grid.columns\}×\{grid.rows\}/);
  assert.match(terminal, /onGridChange=\{updateGrid\}/);
  assert.match(css, /\.mac-terminal-window \.mac-window-heading \{[^}]*justify-content: flex-start/);
  assert.match(css, /\.terminal-cell-probe \{[^}]*visibility: hidden/);
});

test("Dock neighbors retain a gap at every pointer position without accumulating drift", () => {
  for (const count of [5, 6, 7]) for (const size of [36, 44, 52]) {
    for (let x = -100; x <= 500; x += 2) {
      const first = dockLayout(x, count, size);
      for (let i = 0; i < count - 1; i++) {
        const right = i * (size + 10) + size / 2 + first.offsets[i] + size * first.scales[i] / 2;
        const left = (i + 1) * (size + 10) + size / 2 + first.offsets[i + 1] - size * first.scales[i + 1] / 2;
        assert.ok(Math.abs(left - right - 10) < 1e-8);
      }
      assert.deepEqual(dockLayout(x, count, size), first);
    }
  }
});

test("Dock starts hidden with no introductory reveal, including touch devices", () => {
  const dock = readFileSync(new URL("../app/components/MacDock.tsx", import.meta.url), "utf8");
  const css = readFileSync(new URL("../app/components/macosDesktop.css", import.meta.url), "utf8");
  assert.match(dock, /\[shown, setShown\] = useState\(false\)/);
  assert.doesNotMatch(dock, /1800/);
  assert.match(dock, /if \(nearBottom\) reveal\(\)/);
  assert.match(dock, /onFocus=\{reveal\}/);
  assert.match(css, /\.mac-dock \{[^}]*opacity: 0; pointer-events: none;/);
  const touchRules = css.slice(css.indexOf("@media (hover: none)"), css.indexOf("@media (prefers-reduced-motion"));
  assert.doesNotMatch(touchRules, /opacity: 1/);
  assert.match(touchRules, /\.mac-dock-trigger \{ height: 100%; \}/);
});

test("Spotify is a grayscale Dock shortcut to Brian's profile, not a terminal app", () => {
  const dock = readFileSync(new URL("../app/components/MacDock.tsx", import.meta.url), "utf8");
  const css = readFileSync(new URL("../app/components/macosDesktop.css", import.meta.url), "utf8");
  assert.equal(SPOTIFY_PROFILE_URL, "https://open.spotify.com/user/12127274651");
  assert.match(dock, /"help", "spotify", "recycle"/);
  assert.match(dock, /href=\{SPOTIFY_PROFILE_URL\} target="_blank" rel="noopener noreferrer"/);
  assert.match(dock, /if \(id !== "spotify"\) onLaunch\(id\)/);
  assert.match(dock, /"button, a\[href\]"/);
  assert.match(css, /\.mac-dock-icon \.windows-app-icon \{[^}]*filter: grayscale\(1\)/);
  const icons = readFileSync(new URL("../app/components/DesktopIcon.tsx", import.meta.url), "utf8");
  assert.match(icons, /"\/spotify\/icon-primary\.svg"/);
  const icon = readFileSync(new URL("../public/spotify/icon-primary.svg", import.meta.url), "utf8");
  assert.match(icon, /<svg/);
  assert.match(icon, /viewBox="0 0 236\.05 225\.25"/);
});

test("Full-screen presentation preserves the normal restore frame", () => {
  const normal = { x: .15, y: .2, width: .7, height: .6 };
  assert.deepEqual(modeFrame("fullscreen", normal), { x: 0, y: 0, width: 1, height: 1 });
  assert.deepEqual(modeFrame("normal", normal), normal);
});

test("native icon files are valid local PNGs, with a web-sized Tahoe wallpaper", () => {
  for (const name of ["terminal", "contacts", "mail", "trash", "help", "apple", "folder", "notes"]) {
    const png = readFileSync(new URL("../public/macos-icons/" + name + ".png", import.meta.url));
    assert.equal(png.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
    assert.ok(png.readUInt32BE(16) >= 48 && png.readUInt32BE(20) >= 48);
  }
  const path = new URL("../public/macos-tahoe-dark.jpg", import.meta.url);
  assert.equal(readFileSync(path).subarray(0, 2).toString("hex"), "ffd8");
  assert.ok(statSync(path).size < 500000);
});
