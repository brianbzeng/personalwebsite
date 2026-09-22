# Manic cue review

Staging-only font update to `/review/handwritten-cues`.

The four original WOFF2 files were extracted unchanged from Brian's supplied `Manic-Font.zip` into `public/review/fonts/manic`. No font conversion or alteration. These assets are not imported by the production room.

`manicGlyphs` resets its counter per label, uses the regular face on the first occurrence of each letter, then cycles Alternate One, Two, Three on repeats. Case and Unicode graphemes are preserved. Automatic contextual substitutions/ligatures are disabled so they cannot override the selected face. There is no randomized per-render selection or artificial glyph distortion.

The existing arrow animation, smaller sizing and clear-of-object placement remain. The review also includes `seventeen` to demonstrate four distinct e variants. Twelve focused tests and lint pass. No approval or production deployment implied by the font upload; public licensing must be appropriate when a release is requested.
