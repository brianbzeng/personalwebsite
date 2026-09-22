import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { INITIAL_DESKTOP_SESSION, desktopWindowReducer as reduce, preferredTerminal, managedWindowTitle } from "../app/components/desktopWindowManager.ts";
import { terminalInitialFrame, INITIAL_FRAME } from "../app/components/desktopState.ts";

const fresh = () => structuredClone(INITIAL_DESKTOP_SESSION);
const threeTerminals = () => reduce(reduce(fresh(), { type: "new-terminal", command: "python about.txt" }), { type: "new-terminal", command: "python contact.txt" });

test("new terminals have independent stable IDs and initial commands", () => {
  const initial = fresh(), state = threeTerminals();
  assert.deepEqual(state.windows.map((item) => item.id), ["terminal-1", "terminal-2", "terminal-3"]);
  assert.deepEqual(state.windows.map((item) => item.initialCommand), [undefined, "python about.txt", "python contact.txt"]);
  assert.equal(state.active, "terminal-3");
  assert.equal(state.nextTerminal, 4);
  assert.deepEqual(initial, INITIAL_DESKTOP_SESSION);
  assert.deepEqual(state.windows.map(managedWindowTitle), ["Terminal 1", "Terminal 2", "Terminal 3"]);
});

test("closing or minimizing a background terminal preserves active window and other sessions", () => {
  const state = threeTerminals();
  const closed = reduce(state, { type: "close", id: "terminal-1" });
  assert.equal(closed.active, "terminal-3");
  assert.equal(closed.windows[0], state.windows[1]);
  const minimized = reduce(closed, { type: "minimize", id: "terminal-2" });
  assert.equal(minimized.active, "terminal-3");
  assert.equal(minimized.windows.length, 2);
  assert.equal(minimized.windows[0].initialCommand, "python about.txt");
  assert.equal(reduce(minimized, { type: "close", id: "terminal-99" }), minimized);
});

test("closing the active window selects the highest visible window, never a minimized one", () => {
  let state = reduce(threeTerminals(), { type: "minimize", id: "terminal-2" });
  state = reduce(state, { type: "close", id: "terminal-3" });
  assert.equal(state.active, "terminal-1");
  state = reduce(state, { type: "close", id: "terminal-1" });
  assert.equal(state.active, null);
  assert.equal(state.windows[0].id, "terminal-2");
  state = reduce(state, { type: "focus", id: "terminal-2" });
  assert.equal(state.active, "terminal-2");
  assert.equal(state.windows[0].minimized, false);
});

test("Select Command targets the active terminal or most recently used surviving terminal", () => {
  let state = reduce(threeTerminals(), { type: "focus", id: "terminal-1" });
  assert.equal(preferredTerminal(state).id, "terminal-1");
  state = reduce(state, { type: "open-trash" });
  assert.equal(state.active, "recycle");
  assert.equal(preferredTerminal(state).id, "terminal-1");
  state = reduce(state, { type: "close", id: "terminal-1" });
  assert.equal(preferredTerminal(state).id, "terminal-3");
  state = reduce(state, { type: "close-terminals" });
  assert.equal(preferredTerminal(state), undefined);
});

test("Show Desktop restores the prior window group and active terminal", () => {
  let state = reduce(threeTerminals(), { type: "minimize", id: "terminal-2" });
  state = reduce(state, { type: "focus", id: "terminal-1" });
  const hidden = reduce(state, { type: "show-desktop" });
  assert.equal(hidden.active, null);
  assert.ok(hidden.windows.every((item) => item.minimized));
  assert.deepEqual(hidden.restoreIds, ["terminal-1", "terminal-3"]);
  const restored = reduce(hidden, { type: "show-desktop" });
  assert.equal(restored.active, "terminal-1");
  assert.deepEqual(restored.windows.map((item) => item.minimized), [false, true, false]);
  const closedWhileHidden = reduce(hidden, { type: "close", id: "terminal-1" });
  assert.equal(reduce(closedWhileHidden, { type: "show-desktop" }).active, "terminal-3");
});

test("app-wide Terminal actions leave Trash intact and never reuse session IDs", () => {
  let state = reduce(threeTerminals(), { type: "open-trash" });
  state = reduce(state, { type: "hide-terminals" });
  assert.equal(state.active, "recycle");
  assert.ok(state.windows.filter((item) => item.app === "terminal").every((item) => item.minimized));
  state = reduce(state, { type: "close-terminals" });
  assert.deepEqual(state.windows.map((item) => item.id), ["recycle"]);
  state = reduce(state, { type: "new-terminal" });
  assert.equal(state.active, "terminal-4");
  const repeatTrash = reduce(state, { type: "open-trash" });
  assert.equal(repeatTrash.windows.filter((item) => item.app === "recycle").length, 1);
});

test("terminal cascade wraps within bounds without moving the first window", () => {
  assert.deepEqual(terminalInitialFrame(1), INITIAL_FRAME);
  assert.deepEqual(terminalInitialFrame(7), INITIAL_FRAME);
  assert.notDeepEqual(terminalInitialFrame(1), terminalInitialFrame(2));
  for (let instance = 1; instance <= 250; instance++) {
    const frame = terminalInitialFrame(instance);
    assert.ok(frame.x >= 0 && frame.y >= 0);
    assert.ok(frame.x + frame.width <= 1 && frame.y + frame.height <= 1);
  }
});

test("menus and desktop icons share app actions, context handling and stable Terminal instances", () => {
  const source = (file) => readFileSync(new URL(`../app/components/${file}`, import.meta.url), "utf8");
  const desktop = source("MonitorDesktop.tsx"), terminal = source("DesktopTerminal.tsx"), dock = source("MacDock.tsx");
  assert.doesNotMatch(desktop, /Finder|WINDOW_IDS|windows\.terminal|terminal\.current/);
  assert.match(desktop, /key=\{item\.id\} instance=\{item\.number\}/);
  assert.match(desktop, /terminalRefs\.current\.get\(target\.id\)\?\.run\(command\)/);
  assert.match(terminal, /id=\{props\.instance\}/);
  assert.match(source("DesktopWindow.tsx"), /onFocusCapture=\{onActivate\}/);
  assert.match(desktop, /aria-controls="terminal-command-menu"/);
  assert.match(desktop, /COMMANDS\.map\(\(command\)/);
  assert.match(desktop, /item\.closest\('\[role="menu"\]'\) === focusedMenu/);
  assert.match(desktop, /event\.preventDefault\(\); event\.stopPropagation\(\)/);
  assert.match(desktop, /onContextMenu=\{\(event\) => openContext\(event, id\)\}/);
  assert.match(dock, /onAppContextMenu\(event, id\)/);
  assert.match(desktop, /DESKTOP_APP_ORDER\.map/);
  assert.match(source("spotifyWidget.css"), /position: absolute; right: 22px; top: 20px/);
  assert.match(desktop, /focusSession=\{active === item\.id && !flyout && !restoringMenuFocus\}/);
  assert.match(desktop, /\[role="menuitem"\]:not\(:disabled\)/);
  const css = source("macosDesktop.css");
  assert.match(css, /\.mac-desktop \.win-workarea \{[^}]*isolation: isolate/);
  assert.match(css, /\.mac-desktop \.win-task-view > div \{ display: grid/);
  assert.match(css, /\.mac-menu-edit \{ left: clamp/);
});
