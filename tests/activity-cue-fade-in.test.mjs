import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
const component = read('app/components/ActivityCues.tsx');
const pureSource = component.slice(component.indexOf('export const ACTIVITY_CUE_SETTLE_MS'), component.indexOf('function pointArrow'));
const pureJs = ts.transpileModule(pureSource, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const helpers = {};
new Function('exports', pureJs)(helpers);
const { activityCueOpacity, activityCueEndMs, ACTIVITY_CUE_SETTLE_MS, ACTIVITY_CUE_FADE_MS } = helpers;

test('approved cues fade in and out within a two-second visible lifetime', () => {
  assert.equal(ACTIVITY_CUE_SETTLE_MS, 600);
  assert.equal(ACTIVITY_CUE_FADE_MS, 450);
  for (const [elapsed, opacity] of [
    [0, 0], [599, 0], [600, 0], [825, .5], [1050, 1],
    [1600, 1], [2150, 1], [2375, .5], [2600, 0], [3000, 0],
  ]) assert.equal(activityCueOpacity(elapsed, 2000, true), opacity, `elapsed ${elapsed}`);
  assert.equal(activityCueEndMs(2000, true), 2600);
});

test('intro and outro opacity use matching speeds at every sampled point', () => {
  for (let age = 0; age <= 2000; age += 25) {
    assert.equal(
      activityCueOpacity(600 + age, 2000, true),
      activityCueOpacity(600 + 2000 - age, 2000, true),
      `visible age ${age}`,
    );
  }
  assert.equal(activityCueOpacity(600 + 112.5, 2000, true), .25);
  assert.equal(activityCueOpacity(600 + 337.5, 2000, true), .75);
});

test('legacy timing remains unchanged without fade-in opt-in', () => {
  assert.equal(activityCueOpacity(600, 2000), 1);
  assert.equal(activityCueOpacity(2600, 2000), 1);
  assert.equal(activityCueOpacity(2825, 2000), .5);
  assert.equal(activityCueOpacity(3050, 2000), 0);
  assert.equal(activityCueEndMs(2000), 3050);
  assert.equal(activityCueOpacity(600), 1);
  assert.equal(activityCueOpacity(4825), .5);
  assert.equal(activityCueOpacity(5050), 0);
});

test('fade lifetime helper drives both animation completion and geometry polling', () => {
  assert.match(component, /activityCueOpacity\(clock\.current\.elapsed, visibleMs, fadeIn\)/);
  assert.equal((component.match(/clock\.current\.elapsed >= activityCueEndMs\(visibleMs, fadeIn\)/g) || []).length, 2);
  assert.match(component, /\[key, ready, fontReady, visibleMs, fadeIn\]/);
  assert.match(component, /\[key, touch, fontReady, visibleMs, fadeIn\]/);
});

test('approved production and review routes opt into fade-in without review behavior on home', () => {
  const room = read('app/components/CinematicRoom.tsx');
  const shelf = read('app/components/BookshelfExperience.tsx');
  assert.match(room, /cueFadeIn = false/);
  assert.match(room, /<VinylShelf[^>]*cueFadeIn=\{cueFadeIn\}/);
  assert.equal((room.match(/<ActivityCues fadeIn=\{cueFadeIn\}/g) || []).length, 2);
  assert.match(shelf, /cueFadeIn=false/);
  assert.match(shelf, /<ActivityCues fadeIn=\{cueFadeIn\}/);
  assert.match(read('app/review/activity-cues/page.tsx'), /<CinematicRoom[^>]*cueFadeIn/);
  assert.match(read('app/review/book-cues/page.tsx'), /<BookshelfExperience[^>]*cueFadeIn/);
  assert.match(read('app/page.tsx'), /cueFadeIn/);
  assert.doesNotMatch(read('app/page.tsx'), /shelfReview/);
  assert.doesNotMatch(read('app/desktop/page.tsx'), /cueFadeIn/);
});
