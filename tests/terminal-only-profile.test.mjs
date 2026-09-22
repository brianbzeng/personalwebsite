import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { APP_COMMANDS, resolveTerminalCommand } from "../app/components/terminalContent.ts";

test("About and Contact remain terminal commands but are not desktop apps", () => {
  const read = (name) => readFileSync(new URL(`../app/components/${name}`, import.meta.url), "utf8");
  const registry = read("DesktopIcon.tsx");
  assert.doesNotMatch(registry, /id: "(?:about|contact)"/);
  assert.doesNotMatch(registry.match(/DESKTOP_APP_ORDER[^;]+/)[0], /"(?:about|contact)"/);
  assert.doesNotMatch(read("MacDock.tsx").match(/const APPS[^;]+/)[0], /"(?:about|contact)"/);
  assert.doesNotMatch(read("MonitorDesktop.tsx"), /launch\("(?:about|contact)"\)/);
  for (const feature of ["about", "contact"]) {
    const result = resolveTerminalCommand(APP_COMMANDS[feature]);
    assert.ok(result.lines.length > 0);
    assert.ok(!result.lines.some((line) => line.includes("not recognized")));
    assert.ok(resolveTerminalCommand("help").lines.some((line) => line.includes(APP_COMMANDS[feature])));
  }
});
