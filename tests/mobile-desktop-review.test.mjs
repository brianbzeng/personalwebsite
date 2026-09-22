import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const css = read("app/components/mobileDesktop.css");

test("approved phone desktop layout is enabled and confined to short landscape screens", () => {
  assert.match(read("app/components/MonitorDesktop.tsx"), /mobileLayout = false/);
  assert.match(read("app/desktop/page.tsx"), /<MonitorDesktop mobileLayout \/>/);
  assert.match(read("app/review/mobile-desktop/page.tsx"), /<MonitorDesktop mobileLayout \/>/);
  assert.match(css, /max-width: 1024px.*max-height: 600px.*orientation: landscape/);
  assert.match(css, /data-mobile-layout="review"/);
});

test("phone terminal and widgets have separate bounded lanes", () => {
  for (const [width, height] of [[926, 322], [844, 390], [667, 300]]) {
    const widgetWidth = Math.max(194, Math.min(274, width * .27));
    const terminalWidth = width - widgetWidth - 96;
    const terminalBodyHeight = height - 32 - 38 - 12 - 34 - 20;
    assert.ok(terminalWidth >= 330, `${width}: terminal width`);
    assert.ok(Math.floor(terminalBodyHeight / (13 * 1.45)) >= 8, `${height}: terminal rows`);
    assert.ok(76 + terminalWidth + 12 <= width - widgetWidth - 8, "no widget overlap");
  }
  assert.match(css, /--mobile-widget-width: clamp\(194px, 27vw, 274px\)/);
  assert.match(css, /height: 100dvh/);
  assert.match(css, /overflow-y: auto; scrollbar-width: thin; overscroll-behavior: contain/);
});

test("touch entry does not summon the keyboard automatically", () => {
  const terminal = read("app/components/DesktopTerminal.tsx");
  assert.match(terminal, /mobileLayout && window\.matchMedia\("\(pointer: coarse\)"\)\.matches\) return/);
  assert.match(css, /windows-terminal-prompt input \{ font-size: 16px; \}/);
});
