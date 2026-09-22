import test from "node:test";
import assert from "node:assert/strict";
import { INITIAL_DESKTOP_SESSION, desktopWindowReducer as reduce, managedWindowTitle } from "../app/components/desktopWindowManager.ts";
import { resolveTerminalCommand } from "../app/components/terminalContent.ts";

test("Help opens independently, restores once, and leaves terminal history alone", () => {
  const initial = structuredClone(INITIAL_DESKTOP_SESSION);
  let state = reduce(initial, { type: "open-help" });
  assert.equal(state.active, "help");
  assert.deepEqual(state.windows[0], initial.windows[0]);
  assert.equal(managedWindowTitle(state.windows.at(-1)), "Help");
  state = reduce(state, { type: "minimize", id: "help" });
  state = reduce(state, { type: "open-help" });
  assert.equal(state.windows.filter((item) => item.app === "help").length, 1);
  assert.equal(state.windows.at(-1).minimized, false);
  state = reduce(state, { type: "close", id: "help" });
  assert.equal(state.active, "terminal-1");
  assert.ok(resolveTerminalCommand("help").lines.some((line) => line.includes("python about.txt")));
});
