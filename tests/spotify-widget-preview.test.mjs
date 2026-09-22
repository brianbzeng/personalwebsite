import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import * as data from "../app/components/spotifyData.ts";
import * as refresh from "../app/components/spotifyRefresh.ts";

const require = createRequire(import.meta.url);
const source = readFileSync(new URL("../app/components/SpotifyWidget.tsx", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 } }).outputText;
const module = { exports: {} };
new Function("require", "module", "exports", compiled)((id) => {
  if (id === "./spotifyData") return data;
  if (id === "./spotifyRefresh") return refresh;
  if (id.endsWith(".css")) return {};
  return require(id);
}, module, module.exports);
const Widget = module.exports.default;
const fixture = { ...data.EMPTY_SPOTIFY_FEED, status: "ready", isPlaying: true, song: { id: "sample", name: "Sample song", artist: "Preview artist", image: null, url: "https://open.spotify.com/search/Sample%20song" } };

test("review equalizer is decorative and preserves the song link", () => {
  const html = renderToStaticMarkup(createElement(Widget, { previewFeed: fixture }));
  assert.match(html, /spotify-widget is-playing/);
  assert.match(html, /<span class="spotify-passive-levels" aria-hidden="true">/);
  assert.doesNotMatch(html, /spotify-listen-along|spotify-listen-label|Listen along/);
  assert.match(html, /<a class="spotify-song" href="https:\/\/open.spotify.com\/search\/Sample%20song"/);
  assert.equal((html.match(/<i><\/i>/g) ?? []).length, 5);
});

test("paused preview retains the last song but stops playback indication", () => {
  const html = renderToStaticMarkup(createElement(Widget, { previewFeed: { ...fixture, isPlaying: false } }));
  assert.doesNotMatch(html, /spotify-widget is-playing/);
  assert.match(html, /A little quiet for now/);
  assert.match(html, /class="spotify-song" href=/);
});

test("main default also uses decorative bars without an interactive equalizer", () => {
  const html = renderToStaticMarkup(createElement(Widget));
  assert.doesNotMatch(html, /spotify-listen-along|spotify-listen-label|Listen along/);
  assert.match(html, /spotify-passive-levels/);
  assert.doesNotMatch(source, /passiveEqualizer/);
});

test("review fixture skips live polling and route supplies sample data explicitly", () => {
  assert.match(source, /useEffect\(\(\) => \{\s*if \(previewFeed\) return;/);
  const route = readFileSync(new URL("../app/review/spotify-widget/page.tsx", import.meta.url), "utf8");
  assert.match(route, /<SpotifyWidget previewFeed=/);
  assert.match(route, /Sample data, not live listening/);
  const css = readFileSync(new URL("../app/components/spotifyWidget.css", import.meta.url), "utf8");
  assert.match(css, /\.spotify-passive-levels \{[^}]*pointer-events: none/);
  assert.match(css, /\.spotify-widget\.is-playing \.spotify-passive-levels \{ opacity: 1; \}/);
});
