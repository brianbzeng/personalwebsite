export type ManicVariant = 0 | 1 | 2 | 3;
export type ManicGlyph = { letter: string; variant: ManicVariant };

/** Seeded variation keeps actual Manic faces random-looking without render flicker. */
export function manicGlyphs(text: string, seed: string | number = text): ManicGlyph[] {
  const letters = typeof Intl.Segmenter === 'function'
    ? Array.from(new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(text), entry => entry.segment)
    : Array.from(text);
  // No browser-only entropy: server rendering and hydration choose the same faces.
  let state = 2166136261;
  for (const codePoint of `${seed}`) {
    state = Math.imul(state ^ codePoint.codePointAt(0)!, 16777619) >>> 0;
  }
  const random = () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = Math.imul(state ^ (state >>> 15), 1 | state);
    value ^= value + Math.imul(value ^ (value >>> 7), 61 | value);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
  let previous: ManicVariant | undefined;

  return letters.map(letter => {
    if (!/\p{L}/u.test(letter)) return { letter, variant: 0 };
    // Change the face after every letter, not only when a letter repeats.
    // Punctuation does not consume a random choice or reset the rhythm.
    const choices = ([0, 1, 2, 3] as ManicVariant[]).filter(face => face !== previous);
    const variant = choices[Math.floor(random() * choices.length)];
    previous = variant;
    return { letter, variant };
  });
}
