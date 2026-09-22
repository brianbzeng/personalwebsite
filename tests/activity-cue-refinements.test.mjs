import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';

const component = readFileSync(new URL('../app/components/ActivityCues.tsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../app/components/activityCues.css', import.meta.url), 'utf8');
const pureSource = component.slice(component.indexOf('export const ACTIVITY_CUE_SETTLE_MS'), component.indexOf('function pointArrow'));
const helpers = {};
new Function('exports', ts.transpileModule(pureSource, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText)(helpers);
const { placeViewportCue, shortenCueTail, stableCueTarget } = helpers;

test('refined arrow proportions remain opt-in and every presentation stays stationary', () => {
  assert.match(component, /refined = false/);
  assert.match(component, /data-refined=\{refined\}/);
  assert.doesNotMatch(css, /@keyframes|activity-cue-subtle-float|activity-cue-bounce/);
  assert.match(css, /animation: none/);
});

test('refined point shafts are half their original length in every orientation', () => {
  const tip = { x: 300, y: 280 };
  for (const start of [{ x: 300, y: 240 }, { x: 300, y: 320 }, { x: 260, y: 280 }, { x: 340, y: 280 }, { x: 210, y: 230 }]) {
    const next = shortenCueTail(start, tip, true);
    assert.equal(Math.hypot(next.x - tip.x, next.y - tip.y), Math.hypot(start.x - tip.x, start.y - tip.y) / 2);
    assert.equal(shortenCueTail(start, tip, false), start);
    assert.deepEqual(tip, { x: 300, y: 280 });
  }
});

test('larger scroll guidance stays page-centered and inside narrow phone edges', () => {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 926, height: 322 }, { width: 667, height: 300 }]) {
    const size = { width: 140, height: 80 };
    const box = placeViewportCue({ x: 0, y: 0, width: 1, height: 1 }, viewport, size, { x: .955, y: .5 });
    assert.ok(box);
    assert.equal(box.y + box.height / 2, viewport.height / 2);
    assert.ok(box.x + box.width <= viewport.width - 12);
    assert.ok(box.x >= 12);
  }
  assert.match(component, /if \(!rect && spec.viewportAnchor\) rect =/);
});

test('fixed viewport labels never overlap an actual target or neighboring note', () => {
  const viewport = { width: 1000, height: 600 };
  const size = { width: 100, height: 60 };
  const anchor = { x: .95, y: .5 };
  assert.equal(placeViewportCue({ x: 880, y: 200, width: 120, height: 200 }, viewport, size, anchor), null);
  assert.equal(placeViewportCue({ x: 0, y: 0, width: 1, height: 1 }, viewport, size, anchor, 'right', [{ x: 880, y: 250, width: 100, height: 90 }]), null);
});

test('every target follows the pan until ready, then stays anchored without opt-in or reinsetting', () => {
  const cache = new Map();
  const spec = { id: 'book', label: 'Click', targetInset: { left: .2 } };
  const first = { x: 100, y: 200, width: 50, height: 100 };
  stableCueTarget(spec, first, cache, false);
  assert.equal(cache.size, 0);
  const settled = stableCueTarget(spec, { ...first, x: 200 }, cache, true);
  assert.deepEqual(settled, { x: 210, y: 200, width: 40, height: 100 });
  const hovered = { x: 240, y: 175, width: 80, height: 120 };
  assert.deepEqual(stableCueTarget(spec, hovered, cache, true), settled);
  assert.deepEqual(stableCueTarget(spec, hovered, cache, false), settled);
  cache.clear();
  assert.notDeepEqual(stableCueTarget(spec, hovered, cache, true), settled);
  assert.match(component, /viewportKey !== frozenViewport.*frozenTargets.clear\(\)/);
});
