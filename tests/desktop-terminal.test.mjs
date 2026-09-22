import assert from "node:assert/strict";
import test from "node:test";
import { AGENT_SUMMARY_LINES, APP_COMMANDS, ISOMETRIC_NAME_ART, UPRIGHT_NAME_GLYPHS, TERMINAL_GREETING_HINT, resolveTerminalCommand } from "../app/components/terminalContent.ts";
import { FORWARD_NAME_ART, FORWARD_NAME_POSE, PORTFOLIO_GREETING, PORTFOLIO_GREETING_ART, renderAsciiName, renderAsciiText, renderNameGlyph } from "../app/components/asciiNameGeometry.ts";
import { formatPulseGraph, samplePulseValues, PULSE_COLUMNS, PULSE_ROWS, PULSE_CYCLE_MS } from "../app/components/terminalPulseArt.ts";

test("Python-style app commands return terminal content", () => {
  assert.equal(resolveTerminalCommand("python pulse.py").pulse, true);
  assert.match(resolveTerminalCommand("python about.txt").lines.join("\n"), /Brian Zeng/);
  assert.match(resolveTerminalCommand("python contact.txt").lines.join("\n"), /bzeng0000@gmail.com/);
  for (const command of Object.values(APP_COMMANDS)) {
    assert.doesNotMatch(resolveTerminalCommand(command).lines.join("\n"), /new window/i);
  }
});

test("help keeps plain built-ins and command-description separators", () => {
  const help = resolveTerminalCommand("help").lines;
  for (const line of help.slice(1)) assert.match(line, /^  .+ + - /);
  assert.match(help.join("\n"), /python pulse\.py/);
  assert.match(help.join("\n"), /python agents\.txt + - /);
  assert.doesNotMatch(help.join("\n"), /\.exe/);
  assert.equal(resolveTerminalCommand("clear").clear, true);
});

test("agents.txt provides a public site summary inline with the existing command workflow", () => {
  const result = resolveTerminalCommand("  PYTHON   agents.txt  ");
  assert.deepEqual(result.lines, AGENT_SUMMARY_LINES);
  assert.equal(result.pulse, false);
  const summary = result.lines.join("\n");
  assert.match(summary, /Brian Zeng/);
  assert.match(summary, /Oakland, California/);
  assert.match(summary, /UC Santa Barbara/);
  assert.match(summary, /vinyl holder/);
  assert.match(summary, /\/agents\.txt/);
  assert.match(summary, /does not execute Python/);
  assert.match(summary, /not permission to contact Brian or take actions/);
  assert.doesNotMatch(summary, /SPOTIFY_CLIENT_SECRET|access_token|refresh_token|\.env|C:\\\\Users/i);
  for (const command of Object.values(APP_COMMANDS)) assert.ok(summary.includes(command));
});

test("parsing tolerates whitespace and case without interpreting arbitrary commands", () => {
  assert.equal(resolveTerminalCommand(" PYTHON   pulse.py ").pulse, true);
  assert.equal(resolveTerminalCommand("  "), null);
  for (const command of ["constructor", "__proto__", "about.exe", "help.exe", "python pulse.py; clear", "python secret.py"]) {
    assert.match(resolveTerminalCommand(command).lines[0], /not recognized/);
  }
});

test("the banner is eleven rows of actual ASCII with unfilled fronts and shaded edges", () => {
  assert.match(ISOMETRIC_NAME_ART, /^[\x20-\x7e\n]+$/);
  assert.equal(ISOMETRIC_NAME_ART.split("\n").length, 11);
  assert.ok(ISOMETRIC_NAME_ART.includes("/::/  \\"));
  assert.ok(ISOMETRIC_NAME_ART.includes("\\::\\"));
});

test("upright letters preserve every original outline and shading character", () => {
  assert.equal(UPRIGHT_NAME_GLYPHS.length, 9);
  const letters = UPRIGHT_NAME_GLYPHS.map((glyph) => glyph.split("\n"));
  assert.ok(letters.every((rows) => rows.length === 11));
  ISOMETRIC_NAME_ART.split("\n").forEach((row, index) => {
    const separated = letters.map((letter) => letter[index]).join("");
    assert.equal(separated.replace(/ /g, ""), row.replace(/ /g, ""));
  });
});

test("forward rotation hides actual bottom faces without removing any geometry", () => {
  for (const letter of "BRIANZENG") {
    const forward = renderNameGlyph(letter);
    const backward = renderNameGlyph(letter, { ...FORWARD_NAME_POSE, pitch: -FORWARD_NAME_POSE.pitch });
    assert.equal(forward.faceCount, backward.faceCount);
    assert.ok(forward.pixelsByFace.front > 0);
    assert.ok(forward.pixelsByFace.top > 0);
    assert.equal(forward.pixelsByFace.bottom, 0);
    assert.ok(!forward.visibleFaces.includes("bottom"));
    assert.ok(backward.pixelsByFace.bottom > 0, `${letter}'s underside returns when tilted backward`);
    assert.equal(backward.pixelsByFace.top, 0);
    assert.notDeepEqual(forward.rows, backward.rows);
  }
});

test("the projected name remains compact, deterministic plain ASCII with edge-only shading", () => {
  assert.equal(FORWARD_NAME_ART, renderAsciiName());
  assert.match(FORWARD_NAME_ART, /^[\x20-\x7e\n]+$/);
  assert.match(FORWARD_NAME_ART, /:/);
  assert.ok(FORWARD_NAME_ART.split("\n").every((row) => row.length <= 189));
  assert.ok(FORWARD_NAME_ART.split("\n").length <= 16);
  for (const letter of "BRIANZENG") {
    const front = renderNameGlyph(letter, { pitch: 0, yaw: 0 });
    assert.deepEqual(front.visibleFaces, ["front"]);
    assert.doesNotMatch(front.rows.join("\n"), /:/, "front faces stay unshaded");
  }
  assert.throws(() => renderNameGlyph("?"), /Unsupported banner letter/);
  for (const pitch of [NaN, Infinity, 61]) assert.throws(() => renderAsciiName({ pitch, yaw: 20 }), /angles/);
});

test("wider letters have flush top caps without trailing corner strokes", () => {
  const previousWidths = { B: 15, R: 15, I: 13, A: 17, N: 15, Z: 15, E: 15, G: 15 };
  for (const [letter, previousWidth] of Object.entries(previousWidths)) {
    const rows = renderNameGlyph(letter).rows;
    assert.ok(rows[0].length > previousWidth, `${letter}'s contour is wider`);
    const top = rows.find((row) => row.trim());
    assert.match(top.trim(), /^_+( +_+)*$/, `${letter}'s top cap has no protruding verticals or slashes`);
    assert.ok(rows.filter((row) => row.trim()).length <= 15, "widening does not make letters taller");
  }
  assert.ok(FORWARD_NAME_ART.split("\n").every((row) => row === row.trimEnd()));
});

test("top shading reaches the front rim without an empty underscore strip", () => {
  for (const letter of "BRIANZENG") {
    const rows = renderNameGlyph(letter).rows.filter((row) => row.trim());
    assert.match(rows[0].trim(), /^_+( +_+)*$/, "preserve the outlined back/top silhouette");
    assert.match(rows[1], /:{3,}/, "keep top-face shading");
    assert.match(rows[2], /:{3,}/, "continue shading through the front rim");
    assert.doesNotMatch(rows[2], /_/, "no blank underscore cells between shading and front face");
  }
});

test("portfolio greeting preserves the ASCII style and adds the exact plain-text help hint", () => {
  assert.equal(PORTFOLIO_GREETING, "Brian Zeng's Portfolio");
  assert.equal(TERMINAL_GREETING_HINT, "Type 'help' to explore.");
  assert.equal(PORTFOLIO_GREETING_ART, renderAsciiText(PORTFOLIO_GREETING));
  assert.equal(renderAsciiText("Brian Zeng"), FORWARD_NAME_ART);
  assert.equal(renderAsciiText("  brian   zeng  "), FORWARD_NAME_ART);
  assert.equal(renderAsciiText("  "), "");
  assert.match(PORTFOLIO_GREETING_ART, /^[\x20-\x7e\n]+$/);
  const rows = PORTFOLIO_GREETING_ART.split("\n");
  assert.equal(rows.length, FORWARD_NAME_ART.split("\n").length);
  assert.ok(rows.every((row) => row.length <= 399 && row === row.trimEnd()));
  assert.doesNotMatch(Object.values(APP_COMMANDS).join("\n"), /projects/i);
});

test("greeting words have eight-column gaps without changing letters or their spacing", () => {
  const words = ["BRIAN", "ZENG'S", "PORTFOLIO"].map((word) => {
    const letters = [...word].map((letter) => renderNameGlyph(letter).rows);
    return letters[0].map((_, row) => letters.map((letter) => letter[row]).join(" "));
  });
  const expected = words[0].map((_, row) => words.map((word) => word[row]).join(" ".repeat(8)).trimEnd());
  while (expected.length && !expected[0].trim()) expected.shift();
  while (expected.length && !expected.at(-1).trim()) expected.pop();
  assert.equal(PORTFOLIO_GREETING_ART, expected.join("\n"));
});

test("new greeting letters share the same unshaded fronts and forward-tilted edge shading", () => {
  for (const letter of "SPOTFL'") {
    const forward = renderNameGlyph(letter);
    const backward = renderNameGlyph(letter, { ...FORWARD_NAME_POSE, pitch: -FORWARD_NAME_POSE.pitch });
    assert.equal(forward.faceCount, backward.faceCount);
    assert.ok(forward.pixelsByFace.front > 0);
    assert.ok(forward.pixelsByFace.top > 0);
    assert.equal(forward.pixelsByFace.bottom, 0);
    assert.ok(backward.pixelsByFace.bottom > 0);
    const front = renderNameGlyph(letter, { pitch: 0, yaw: 0 });
    assert.deepEqual(front.visibleFaces, ["front"]);
    assert.doesNotMatch(front.rows.join("\n"), /:/);
  }
  const apostrophe = renderNameGlyph("'").rows;
  assert.equal(apostrophe.length, renderNameGlyph("S").rows.length);
  assert.ok(apostrophe.slice(0, 7).some((row) => row.trim()));
  assert.ok(apostrophe.slice(7).every((row) => !row.trim()), "apostrophe stays raised on the shared baseline");
});

test("ASCII activity animation is bounded and preserves contribution values", () => {
  const days = Array.from({ length: 28 }, (_, i) => ({ date: `day-${i}`, count: i % 5 }));
  const before = JSON.stringify(days);
  const resting = formatPulseGraph(days, null);
  for (let cursor = -1; cursor <= PULSE_COLUMNS; cursor++) {
    const art = formatPulseGraph(days, cursor);
    assert.match(art, /^[\x20-\x7e\n]+$/);
    const rows = art.split("\n");
    assert.equal(rows.length, PULSE_ROWS + 3);
    assert.equal(rows[0].length, rows[PULSE_ROWS + 1].length);
    assert.ok(rows.slice(1, PULSE_ROWS + 1).every((row) => row.length === rows[0].length));
    assert.equal(art.split("o").length - 1, 1);
    assert.match(resting[art.indexOf("o")], /[_/\\|]/, "the read-head stays on the rendered stroke");
  }
  assert.equal(JSON.stringify(days), before);
  assert.doesNotMatch(formatPulseGraph(days, null), /o|\^/);
  assert.doesNotThrow(() => formatPulseGraph([], 0));
  assert.equal(PULSE_CYCLE_MS, 56 * 120, "the denser chart retains the original scan duration");
});

test("smooth pulse interpolation preserves every daily value without overshoot", () => {
  const days = [0,0,0,0,56,21,7,0,16,0,0,22,0,9,0,0,0,0,0,7,0,0,8,0,0,0,0,0]
    .map((count, index) => ({ count, date: `day-${index}` }));
  const samples = samplePulseValues(days);
  assert.equal(samples.length, PULSE_COLUMNS);
  days.forEach(({ count }, index) => assert.equal(samples[index * 6], count));
  for (let index = 0; index < days.length - 1; index++) {
    const lower = Math.min(days[index].count, days[index + 1].count);
    const upper = Math.max(days[index].count, days[index + 1].count);
    assert.ok(samples.slice(index * 6, (index + 1) * 6 + 1).every((value) => value >= lower && value <= upper));
  }
  assert.equal(Math.max(...samples), 56);
  assert.ok(samplePulseValues([]).every((value) => value === 0));
  assert.ok(samplePulseValues([{ date: "one", count: 7 }]).every((value) => value === 7));
});

test("ASCII slopes use connected baseline-aligned diagonal strokes", () => {
  for (const descending of [false, true]) {
    const days = Array.from({ length: 28 }, (_, i) => ({ date: `day-${i}`, count: descending ? 27 - i : i }));
    const heights = samplePulseValues(days).map((value) => PULSE_ROWS - 1 - Math.round(value / 27 * (PULSE_ROWS - 1)));
    const rows = formatPulseGraph(days, null).split("\n").slice(1, PULSE_ROWS + 1).map((row) => row.slice(6, -1));
    for (let column = 0; column < PULSE_COLUMNS - 1; column++) {
      const left = heights[column], right = heights[column + 1];
      const expected = right < left ? "/" : right > left ? "\\" : "_";
      assert.equal(rows[Math.max(left, right)][column], expected);
    }
  }
  const large = formatPulseGraph([{ date: "a", count: 100000 }, { date: "b", count: 0 }], null).split("\n");
  assert.ok(large.slice(0, PULSE_ROWS + 2).every((row) => row.length === large[0].length), "large counts do not misalign the frame");
});
