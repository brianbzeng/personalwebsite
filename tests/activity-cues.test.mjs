import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';

const component = readFileSync(new URL('../app/components/ActivityCues.tsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../app/components/activityCues.css', import.meta.url), 'utf8');
const pureSource = component.slice(component.indexOf('export const ACTIVITY_CUE_SETTLE_MS'), component.indexOf('function pointArrow'));
const pureJs = ts.transpileModule(pureSource, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const helpers = {};
new Function('exports', pureJs)(helpers);
const { placeActivityCue, cueRectsOverlap, activityCueOpacity, insetCueTarget } = helpers;

test('notes settle then remain visible for four seconds before a gentle fade', () => {
  assert.equal(activityCueOpacity(0), 0);
  assert.equal(activityCueOpacity(599), 0);
  assert.equal(activityCueOpacity(600), 1);
  assert.equal(activityCueOpacity(4599), 1);
  assert.equal(activityCueOpacity(4825), .5);
  assert.equal(activityCueOpacity(5050), 0);
});

test('preferred top-middle label stays outside the sleeve on desktop and phone', () => {
  for (const [viewport, target] of [
    [{ width: 1440, height: 900 }, { x: 530, y: 220, width: 380, height: 380 }],
    [{ width: 926, height: 322 }, { x: 370, y: 90, width: 190, height: 190 }],
  ]) {
    const box = placeActivityCue(target, viewport, { width: 90, height: 51 }, 'top');
    assert.ok(box);
    assert.equal(box.side, 'top');
    assert.equal(box.x + box.width / 2, target.x + target.width / 2);
    assert.ok(box.y + box.height < target.y);
    assert.equal(cueRectsOverlap(box, target, 6), false);
  }
});

test('a constrained mobile target falls back to free space, never on the object', () => {
  const target = { x: 190, y: 5, width: 310, height: 280 };
  const box = placeActivityCue(target, { width: 667, height: 300 }, { width: 95, height: 55 }, 'top');
  assert.equal(box.side, 'right');
  assert.equal(cueRectsOverlap(box, target, 6), false);
  assert.ok(box.x + box.width <= 655);
  assert.equal(placeActivityCue({ x: 0, y: 0, width: 667, height: 300 }, { width: 667, height: 300 }, { width: 95, height: 55 }), null);
});

test('neighboring points of interest and labels are excluded from placement', () => {
  const target = { x: 240, y: 140, width: 200, height: 160 };
  const neighbor = { x: 200, y: 10, width: 280, height: 100 };
  const box = placeActivityCue(target, { width: 926, height: 420 }, { width: 100, height: 60 }, 'top', [neighbor]);
  assert.ok(box);
  assert.notEqual(box.side, 'top');
  assert.equal(cueRectsOverlap(box, neighbor, 6), false);
});

test('all Manic faces load before timing and lifetime ignores changing geometry', () => {
  assert.match(component, /document\.fonts\.load/);
  for (const family of ['Manic Regular', 'Manic Alternate One', 'Manic Alternate Two', 'Manic Alternate Three']) assert.ok(component.includes(family));
  assert.match(component, /document\.fonts\.ready/);
  assert.match(component, /\[key, ready, fontReady, visibleMs, fadeIn\]/);
  assert.match(component, /document\.hidden/);
  assert.match(component, /visibilitychange/);
  assert.match(component, /bz-replay-cues/);
  assert.doesNotMatch(component, /localStorage|onMouse|onPointer|onTouch/);
});

test('notes are decorative, motion-safe, and never intercept clicks', () => {
  assert.match(component, /aria-hidden="true"/);
  assert.match(component, /focusable="false"/);
  assert.match(css, /pointer-events: none !important/);
  assert.match(css, /animation: none/);
  assert.doesNotMatch(css, /@keyframes/);
  assert.match(component, /ManicLettering text=\{cue.label\}/);
});

test('touch can substitute an accurately leftward swipe without changing desktop pointing', () => {
  assert.match(component, /touchGesture\?: CueGesture/);
  assert.match(component, /touch && sourceSpec\.touchGesture/);
  assert.match(component, /gesture: sourceSpec\.touchGesture/);
  assert.match(component, /kind === 'swipe-left' \? 'translate\(200 0\) scale\(-1 1\)'/);
});

test('geometry polling stops after its first settled placement or completion', () => {
  assert.match(component, /layoutKey\.current === key/);
  assert.match(component, /if \(next\.length > 0\) \{ layoutKey\.current = key; return; \}/);
  assert.match(component, /clock\.current\.key === key/);
  assert.match(component, /if \(!done\) frame = requestAnimationFrame\(measure\)/);
  assert.match(component, /\[key, touch, fontReady, visibleMs, fadeIn\]/);
});

test('greeting arrows can hold three seconds and ignore staging replay', () => {
  assert.equal(activityCueOpacity(3599, 3000), 1);
  assert.equal(activityCueOpacity(3825, 3000), .5);
  assert.equal(activityCueOpacity(4050, 3000), 0);
  assert.match(component, /if \(!allowReplay\) return/);
  assert.match(component, /allowReplay \? replayKey : 0/);
  assert.match(component, /completedKey\.current !== key/);
  assert.match(component, /completionRef\.current\?\.\(\)/);
});

test('inset target bounds anchor arrows to visible art instead of oversized hitboxes', () => {
  const rect = { x: 100, y: 200, width: 100, height: 80 };
  assert.deepEqual(insetCueTarget(rect, { top: .65, right: .25 }), { x: 100, y: 252, width: 75, height: 28 });
  assert.equal(insetCueTarget(rect), rect);
  const clamped = insetCueTarget(rect, { top: 1, bottom: 1, left: -.5, right: 1 });
  assert.ok(clamped.width > 0 && clamped.height > 0);
});

test('arrow-only cues use compact stationary slots; text-only has no arrows', () => {
  assert.match(component, /const width = arrowOnly \? 28/);
  assert.match(component, /\{!arrowOnly &&/);
  assert.match(component, /!textOnly && \(arrowOnly \|\| !hasGesture\)/);
  assert.doesNotMatch(css, /activity-cue-bounce|--cue-bounce/);
  assert.match(css, /\.activity-cues__float[^}]*animation: none/);
});

test('long labels reserve actual widest glyph widths while retaining small font scale', () => {
  assert.match(component, /measureText\(letter\)\.width/);
  assert.match(component, /textWidth \* \(compact \? \.46 : \.52\)/);
  assert.match(component, /viewBox=\{`0 0 \$\{cue.textWidth\}/);
  assert.match(component, /inputMode === 'auto' \? deviceTouch : inputMode === 'touch'/);
});
