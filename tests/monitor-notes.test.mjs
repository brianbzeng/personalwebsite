import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { desktopWindowReducer as reduce, INITIAL_DESKTOP_SESSION } from "../app/components/desktopWindowManager.ts";

const source = (file) => readFileSync(new URL(`../app/components/${file}`, import.meta.url), "utf8");

test("every monitor visit greets with Notes popped over the terminal", () => {
  const desktop = source("MonitorDesktop.tsx");
  assert.match(desktop, /dispatch\(\{ type: "open-notes" \}\);\s*\}, \[\]\);/);
  const state = reduce(structuredClone(INITIAL_DESKTOP_SESSION), { type: "open-notes" });
  assert.equal(state.active, "notes");
  const notes = state.windows.find((item) => item.id === "notes");
  const terminal = state.windows.find((item) => item.id === "terminal-1");
  assert.ok(notes && terminal, "greeting keeps both windows open");
  assert.ok(notes.z > terminal.z, "Notes sits in front of the terminal");
  assert.equal(terminal.minimized, false, "the terminal stays visible behind Notes");
});

test("the room menu carries a handwritten New! shortcut into the monitor", () => {
  const room = source("CinematicRoom.tsx");
  const css = source("cinematicRoom.css");
  assert.match(room, /import \{ ManicLettering \} from ['"]\.\/HandwrittenCue['"]/);
  assert.match(room, /className="cinematic-new"/);
  assert.match(room, /<ManicLettering text="New!"/);
  assert.match(room, /aria-label="New! Open Notes on the monitor"/);
  assert.match(room, /onPointerDown=\{\(\) => arm\("approach"\)\} onFocus=\{\(\) => arm\("approach"\)\} onClick=\{enterMonitor\}/);
  assert.match(css, /\.cinematic-controls \.cinematic-new \{ position: absolute; top: 20px; left: 28px;/);
  assert.match(css, /@media \(max-width: 600px\) \{ \.cinematic-controls \.cinematic-new \{[^}]*bottom: 62px;/);
});
