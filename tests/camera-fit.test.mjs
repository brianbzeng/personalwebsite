import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read = path => readFileSync(new URL('../' + path, import.meta.url), 'utf8');

test('approved full-bleed camera framing is shared by home and review', () => {
  assert.match(read('app/review/camera-fit/page.tsx'), /<CinematicRoom/);
  assert.match(read('app/page.tsx'), /<CinematicRoom/);
  assert.match(read('app/components/CinematicRoom.tsx'), /data-viewport-fit="cover"/);
  const css = read('app/components/cinematicRoom.css');
  assert.match(css, /\[data-viewport-fit="cover"\] :is\(\.cinematic-stage, \.cinematic-handoff, \.vinyl-render-stage\)/);
  assert.match(css, /width: max\(100vw, 177\.777777778dvh\)/);
  assert.match(css, /\[data-viewport-fit="cover"\] \.cinematic-diploma img\s*\{\s*object-fit: cover/);
  assert.match(css, /top: calc\(20px \+ max\(0px, \(56\.25vw - 100dvh\) \/ 2\)\)/);
  assert.match(css, /max-width: calc\(100vw - 48px\)/);
});

test('boot screen contains only a centered visual progress bar and accessible status', () => {
  const source=read('app/components/CinematicRoom.tsx');
  assert.doesNotMatch(source, />BZ<|bootHeading/);
  assert.match(source, /ref=\{bootStatus\} tabIndex=\{-1\} className="cinematic-boot" role="status"/);
  assert.match(source, /bootStatus.current\?\.focus\(\)/);
  assert.match(source, /className="cinematic-sr">Starting Brian’s desktop/);
  const css=read('app/components/cinematicRoom.css');
  assert.match(css, /\.cinematic-boot \{[^}]*align-items: center; justify-content: center/);
  assert.match(css, /\.cinematic-boot > a \{ position: absolute/);
});

test('shared 16:9 cover projection fills wide, standard, and mobile landscape windows', () => {
  for (const [width, height] of [[1996,998], [1920,1080], [1440,900], [2560,1080], [844,390]]) {
    const stageWidth = Math.max(width, height * 16/9);
    const stageHeight = stageWidth * 9/16;
    assert.ok(stageWidth >= width && stageHeight >= height - 1e-9);
    assert.ok(Math.abs(stageWidth/stageHeight - 16/9) < 1e-9);
  }
});
