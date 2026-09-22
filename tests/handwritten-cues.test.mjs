import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const component = readFileSync(new URL('../app/components/HandwrittenCue.tsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../app/components/handwrittenCue.css', import.meta.url), 'utf8');
const review = readFileSync(new URL('../app/review/handwritten-cues/page.tsx', import.meta.url), 'utf8');

function rule(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]+)\\}`));
  assert.ok(match, `missing CSS rule for ${selector}`);
  return match[1];
}

function numericProperty(selector, property, unit) {
  const match = rule(selector).match(new RegExp(`(?:^|;)\\s*${property}:\\s*([\\d.]+)${unit}(?:;|$)`));
  assert.ok(match, `missing ${property} in ${unit} for ${selector}`);
  return Number(match[1]);
}

test('cue labels use actual Manic webfonts and explicit alternate spans', () => {
  assert.match(component, /ManicLettering text="Swipe Right"/);
  assert.match(component, /ManicLettering text="Drag"/);
  assert.match(component, /manicGlyphs\(text, seed \?\? `\$\{instanceId\}:\$\{text\}`\)/);
  assert.match(component, /const instanceId = useId\(\)/);
  assert.match(component, /data-manic-variant=\{variant\}/);
  for (const name of ['Regular', 'Alternates1', 'Alternates2', 'Alternates3']) {
    const file = readFileSync(new URL(`../public/review/fonts/manic/MANIC-${name}.woff2`, import.meta.url));
    assert.equal(file.subarray(0, 4).toString(), 'wOF2');
    assert.ok(css.includes(`MANIC-${name}.woff2`));
  }
});

test('decorative cue loops cannot intercept an interaction and honor reduced motion', () => {
  assert.match(component, /aria-hidden="true"/);
  assert.match(component, /focusable="false"/);
  assert.match(css, /pointer-events: none/);
  assert.match(css, /prefers-reduced-motion: reduce/);
  assert.match(css, /animation: none/);
  assert.doesNotMatch(component, /setInterval|setTimeout|onClick|onPointer/);
});

test('Manic retains its own shapes without random deformation or automatic substitutions', () => {
  assert.doesNotMatch(component, /PEN_RHYTHM|const LETTERS|strokeWidth: pen/);
  assert.match(css, /font-synthesis: none/);
  assert.match(css, /font-variant-ligatures: none/);
  assert.match(css, /'calt' 0/);
  assert.match(review, /ManicLettering text="seventeen"/);
  assert.doesNotMatch(component, /Math\.random|Date\.now|performance\.now/);
});

test('both cue samples are smaller than the previous iteration', () => {
  assert.ok(numericProperty('.handwritten-cue', 'width', 'px') < 168);
  assert.ok(numericProperty('.cue-review__swipe', 'width', '%') < 34);
  assert.ok(numericProperty('.cue-review__drag', 'width', '%') < 40);
});

test('gesture loops clear their objects throughout the floating envelope', () => {
  const percent = (selector, property) => numericProperty(selector, property, '%') / 100;
  const sceneAspect = numericProperty('.cue-review__scene', 'aspect-ratio', '');
  // Conservative six SVG-unit allowance covers translation and small rotation.
  // All values below are normalized to scene width, so these guards apply at
  // every responsive sample size rather than only one desktop screenshot.
  const motionAllowance = width => width * 6 / 248;
  const bookRight = percent('.cue-review__book', 'left') + percent('.cue-review__book', 'width');
  const swipeLeft = percent('.cue-review__swipe', 'left');
  const swipeWidth = percent('.cue-review__swipe', 'width');
  assert.ok(swipeLeft - motionAllowance(swipeWidth) > bookRight, 'the whole Swipe Right loop stays beside the book');

  const dragWidth = percent('.cue-review__drag', 'width');
  const dragBottom = percent('.cue-review__drag', 'top') / sceneAspect + dragWidth * 150 / 248;
  const vinylTop = percent('.cue-review__vinyl', 'top') / sceneAspect;
  assert.ok(dragBottom + motionAllowance(dragWidth) < vinylTop, 'the whole Drag loop stays above the cover');

  // The sleeve spans x=12..259 within the 340-unit cover+disc SVG.
  assert.match(review, /M12 6H259V281H12Z/);
  const sleeveCenter = percent('.cue-review__vinyl', 'left') + percent('.cue-review__vinyl', 'width') * 135.5 / 340;
  const dragCenter = percent('.cue-review__drag', 'left') + dragWidth / 2;
  assert.ok(Math.abs(dragCenter - sleeveCenter) < .001, 'Drag is centered on the sleeve, not the disc-inclusive SVG');
});

test('isolated cue review includes both styles and a pause control', () => {
  assert.match(review, /kind="swipe-right"/);
  assert.match(review, /kind="drag"/);
  assert.match(review, /aria-pressed=\{paused\}/);
  assert.match(review, /Existing controls stay until the notes are approved/);
});

test('cue styling remains review-only until each floating note is approved', () => {
  const home = readFileSync(new URL('../app/page.tsx', import.meta.url), 'utf8');
  const room = readFileSync(new URL('../app/components/CinematicRoom.tsx', import.meta.url), 'utf8');
  const shelf = readFileSync(new URL('../app/components/BookshelfExperience.tsx', import.meta.url), 'utf8');
  // Approved 2026-09-21: the room "New!" notes redirect may use the Manic lettering
  // primitive. Gesture cues and the cue stylesheet stay review-only.
  const approved = /import \{ ManicLettering \} from ['"]\.\/HandwrittenCue['"];?\r?\n/g;
  assert.doesNotMatch((home + room + shelf).replace(approved, ''), /HandwrittenCue|handwrittenCue\.css/);
  assert.match(review, /staging only/);
  assert.match(review, /each floating note gets its own staging preview/);
  assert.match(review, /Nothing is live yet/);
});
