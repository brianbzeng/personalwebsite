import assert from 'node:assert/strict';
import test from 'node:test';
import { manicGlyphs } from '../app/components/manicVariants.ts';

test('every letter can use an alternate, not only repeated letters', () => {
  const glyphs = manicGlyphs('abcdefghijklmnopqrstuvwxyz', 'room-note');
  assert.equal(new Set(glyphs.map(glyph => glyph.variant)).size, 4);
  assert.ok(glyphs.some(glyph => glyph.variant !== 0));
  for (let index = 1; index < glyphs.length; index++) {
    assert.notEqual(glyphs[index].variant, glyphs[index - 1].variant);
  }
});

test('seeded choices are repeatable across renders and differ between cue instances', () => {
  const first = manicGlyphs('Click to Enlarge', ':R1:');
  manicGlyphs('seventeen', 'another-note');
  assert.deepEqual(manicGlyphs('Click to Enlarge', ':R1:'), first);
  assert.notDeepEqual(manicGlyphs('Click to Enlarge', ':R2:'), first);
  assert.deepEqual(manicGlyphs('Drag'), manicGlyphs('Drag'));
  assert.deepEqual(manicGlyphs(''), []);
});

test('random sequences do not devolve into a fixed repeating face cycle', () => {
  const faces = manicGlyphs('a'.repeat(100), 42).map(glyph => glyph.variant);
  assert.ok(faces.some((face, index) => index >= 4 && face !== faces[index - 4]));
  assert.ok(faces.every(face => Number.isInteger(face) && face >= 0 && face <= 3));
  assert.ok(faces.every((face, index) => !index || face !== faces[index - 1]));
});

test('punctuation and spaces remain regular without consuming a letter choice', () => {
  const plain = manicGlyphs('ee', 'shared-seed');
  const spaced = manicGlyphs('e! ! e', 'shared-seed');
  assert.deepEqual(spaced.filter(glyph => glyph.letter === 'e'), plain);
  assert.ok(spaced.filter(glyph => glyph.letter !== 'e').every(glyph => glyph.variant === 0));
});

test('Unicode graphemes and original letter case stay intact', () => {
  const text = 'é e\u0301 👩‍💻 aAaaA';
  const glyphs = manicGlyphs(text, 'unicode');
  assert.equal(glyphs.map(glyph => glyph.letter).join(''), text);
  assert.equal(glyphs.filter(glyph => glyph.letter === '👩‍💻').length, 1);
  assert.ok(glyphs.filter(glyph => glyph.letter === '👩‍💻').every(glyph => glyph.variant === 0));
  assert.equal(glyphs.filter(glyph => glyph.letter === 'e\u0301').length, 1);
});
