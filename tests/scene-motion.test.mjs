import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');

function loadMotion() {
  const frames = [];
  const exports = {};
  vm.runInNewContext(ts.transpileModule(read('app/components/sceneMotion.ts'), { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, {
    exports,
    requestAnimationFrame: fn => { frames.push(fn); return frames.length; },
    cancelAnimationFrame: () => {},
  });
  return { exports, frames };
}

test('the rate curve launches moving, accelerates to the peak, then eases into the landing', () => {
  const { exports } = loadMotion();
  for (const profile of [exports.SCENE_MOTION, exports.SHELF_MOTION]) {
    const rate = p => exports.transitionRate(p, profile);
    assert.ok(rate(0) > 1, 'never slower than the render');
    assert.equal(rate(0), profile.start);
    assert.equal(rate(profile.peakAt), profile.peak);
    assert.equal(rate(1), profile.end);
    let previous = rate(0);
    for (let i = 1; i <= 50; i++) { const next = rate(profile.peakAt * i / 50); assert.ok(next >= previous, `accelerating at step ${i}`); previous = next; }
    for (let i = 1; i <= 50; i++) { const next = rate(profile.peakAt + (1 - profile.peakAt) * i / 50); assert.ok(next <= previous + 1e-9, `decelerating at step ${i}`); previous = next; }
  }
});

test('room moves finish in roughly half the rendered time, shelf moves in two thirds', () => {
  const { exports } = loadMotion();
  const room = exports.acceleratedDuration(5.04);
  assert.ok(room > 2.3 && room < 2.7, `monitor approach ${room.toFixed(2)}s`);
  const scene = exports.acceleratedDuration(3.04);
  assert.ok(scene > 1.4 && scene < 1.65, `shelf approach ${scene.toFixed(2)}s`);
  const shelf = exports.acceleratedDuration(1.54, exports.SHELF_MOTION);
  assert.ok(shelf > 0.85 && shelf < 1.05, `cubby move ${shelf.toFixed(2)}s`);
});

test('the driver sets the launch rate before playback and follows the clip until stopped', () => {
  const { exports, frames } = loadMotion();
  const listeners = {};
  const video = { playbackRate: 1, currentTime: 0, duration: NaN, ended: false,
    addEventListener(type, fn) { listeners[type] = fn; }, removeEventListener(type) { delete listeners[type]; } };
  const stop = exports.driveTransitionRate(video, exports.SCENE_MOTION);
  assert.equal(video.playbackRate, exports.SCENE_MOTION.start);
  video.duration = 4; video.currentTime = 0;
  listeners.play();
  assert.equal(video.playbackRate, exports.SCENE_MOTION.start);
  video.currentTime = 4 * exports.SCENE_MOTION.peakAt;
  frames.shift()();
  assert.equal(video.playbackRate, exports.SCENE_MOTION.peak);
  video.currentTime = 4;
  frames.shift()();
  assert.ok(Math.abs(video.playbackRate - exports.SCENE_MOTION.end) < 1e-9);
  stop();
  assert.deepEqual(Object.keys(listeners), []);
  video.currentTime = 0; frames.shift()();
  assert.ok(Math.abs(video.playbackRate - exports.SCENE_MOTION.end) < 1e-9, 'a stopped driver leaves the rate alone');
});

test('acceleration is on for the home page and the review route', () => {
  const room = read('app/components/CinematicRoom.tsx');
  const shelf = read('app/components/BookshelfExperience.tsx');
  assert.match(room, /driveTransitionRate\(video, SCENE_MOTION\)/);
  assert.match(room, /if \(!fastTransitions \|\| !traveling \|\| !video\) return;/);
  assert.match(room, /onPointerEnter=\{\(\) => hover\("approach"\)\}/);
  assert.match(room, /fastTransitions=\{fastTransitions\}/);
  assert.match(shelf, /driveTransitionRate\(video, SHELF_MOTION\)/);
  assert.match(read('app/review/scene-motion/page.tsx'), /fastTransitions/);
  assert.match(read('app/page.tsx'), /fastTransitions/);
});
