import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import * as f1Data from "../app/components/f1ForecastData.ts";
import * as desktopState from "../app/components/desktopState.ts";
import { INITIAL_DESKTOP_SESSION, desktopWindowReducer as reduce, managedWindowTitle } from "../app/components/desktopWindowManager.ts";

const read = (file) => readFileSync(new URL(`../${file}`, import.meta.url), "utf8");
const forecast = JSON.parse(read("app/data/f1-forecast.json"));
const standings = JSON.parse(read("app/data/f1-standings.json"));

test("F1 is closed at startup, opens once, and restores without disturbing Terminal or Notes", () => {
  assert.deepEqual(INITIAL_DESKTOP_SESSION.windows.map((item) => item.id), ["terminal-1"]);
  let state = reduce(structuredClone(INITIAL_DESKTOP_SESSION), { type: "open-notes" });
  const existing = state.windows;
  state = reduce(state, { type: "open-f1" });
  assert.equal(state.active, "f1");
  assert.deepEqual(state.windows.slice(0, 2), existing);
  assert.equal(managedWindowTitle(state.windows.at(-1)), "F1 Forecast");
  state = reduce(state, { type: "minimize", id: "f1" });
  assert.equal(state.active, "notes");
  state = reduce(state, { type: "open-f1" });
  assert.equal(state.windows.filter((item) => item.id === "f1").length, 1);
  assert.equal(state.windows.at(-1).minimized, false);
  state = reduce(reduce(state, { type: "show-desktop" }), { type: "show-desktop" });
  assert.equal(state.active, "f1");
  state = reduce(state, { type: "close-terminals" });
  assert.deepEqual(state.windows.map((item) => item.id), ["notes", "f1"]);
  state = reduce(state, { type: "close", id: "f1" });
  assert.equal(state.active, "notes");
});

test("all original probability views sort correctly and use the updated standings", () => {
  const copy = structuredClone(forecast);
  const teams = f1Data.currentConstructorForecast(forecast.teams, standings.teams);
  assert.equal(teams.length, 11);
  for (const metric of Object.keys(f1Data.F1_METRICS)) {
    const sorted = f1Data.sortedConstructors(teams, metric);
    assert.equal(new Set(sorted.map((team) => team.name)).size, 11);
    assert.ok(sorted.every((team, index) => index === 0 || sorted[index - 1][metric] >= team[metric]));
  }
  assert.equal(teams.find((team) => team.name === "Mercedes").currentPoints, 468);
  assert.equal(teams.find((team) => team.name === "Racing Bulls").currentRank, 5);
  assert.equal(teams.find((team) => team.name === "Audi").currentRank, 8);
  assert.deepEqual(forecast, copy);
  assert.throws(() => f1Data.currentConstructorForecast([], standings.teams), /Missing forecast/);
});

test("current championship snapshot includes Monza while forecast provenance stays explicit", () => {
  assert.equal(standings.asOf, "2026-09-07");
  assert.equal(standings.through, "Italian Grand Prix");
  assert.equal(standings.completedRaces, 13);
  assert.equal(standings.totalRaces, 23);
  assert.equal(standings.completedSprints, 5);
  assert.deepEqual(standings.teams.map((team) => team.currentRank), Array.from({ length: 11 }, (_, i) => i + 1));
  for (const metric of ["title", "top3", "top5"]) {
    assert.ok(forecast.teams.every((team) => team[metric] >= 0 && team[metric] <= 100));
    const target = metric === "title" ? 100 : metric === "top3" ? 300 : 500;
    assert.ok(Math.abs(forecast.teams.reduce((total, team) => total + team[metric], 0) - target) < .1);
  }
  assert.ok(forecast.teams.every((team) => team.title <= team.top3 && team.top3 <= team.top5));
  assert.equal(new URL(standings.source).hostname, "www.formula1.com");
});

test("F1 window stays inside the desktop across small and full-HD workareas", () => {
  for (const [width, height] of [[1920, 1052], [1280, 692], [800, 572], [390, 720]]) {
    const frame = desktopState.fitFrameToArea(f1Data.F1_INITIAL_FRAME, { width, height }, f1Data.F1_MINIMUM_SIZE);
    assert.ok(frame.x >= 0 && frame.y >= 0 && frame.x + frame.width <= 1 && frame.y + frame.height <= 1);
    assert.ok(frame.width * width >= Math.min(width, f1Data.F1_MINIMUM_SIZE.width) - .001);
  }
});

test("F1 renders real forecast rows inside the shared desktop window with grayscale bars", () => {
  const require = createRequire(import.meta.url);
  function component(file, mocks = {}) {
    const { outputText } = ts.transpileModule(read(`app/components/${file}`), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 } });
    const module = { exports: {} };
    new Function("require", "module", "exports", outputText)((id) => id in mocks ? mocks[id] : id.endsWith(".css") ? {} : require(id), module, module.exports);
    return module.exports;
  }
  const F1 = component("DesktopF1.tsx", {
    "./DesktopWindow": component("DesktopWindow.tsx", { "./desktopState": desktopState }),
    "./DesktopIcon": { default: () => null }, "./f1ForecastData": f1Data,
    "../data/f1-forecast.json": { default: forecast }, "../data/f1-standings.json": { default: standings },
  }).default;
  const html = renderToStaticMarkup(createElement(F1, { active: true, foreground: true, minimized: false, zIndex: 10, onActivate() {}, onClose() {}, onMinimize() {} }));
  for (const label of ["Close F1 Forecast", "Minimize F1 Forecast", "Enter full screen for F1 Forecast", "Forecast metric", "Constructor results table"]) assert.ok(html.includes(`aria-label="${label}"`), label);
  assert.match(html, /Italian Grand Prix/);
  assert.ok(html.includes(f1Data.f1Date(forecast.asOf)));
  assert.ok(html.includes(f1Data.f1Date(standings.asOf)));
  for (const team of standings.teams) assert.ok(html.includes(team.name));
  assert.equal((html.match(/<tr>/g) ?? []).length, 12);
  assert.match(html, /aria-pressed="true">Title/);
  assert.match(html, /Top 3/);
  assert.match(html, /Top 5/);
  assert.match(html, /Standings/);
  assert.doesNotMatch(html, /<iframe|style="[^"]*#[0-9a-f]{6}/);
  const desktop = read("app/components/MonitorDesktop.tsx");
  assert.match(desktop, /if \(app === "f1"\) \{ launchAfterPause\(app, \(\) => dispatch\(\{ type: "open-f1" \}\)/);
  assert.match(desktop, /Hide F1 Forecast/);
  assert.match(desktop, /Close F1 Forecast/);
  assert.match(read("app/components/MacDock.tsx"), /"notes", "f1"/);
});
