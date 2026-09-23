# Greeting player consistency — approved release

Based on fetched `origin/main` at `4b5da9a` (including GLM's Notes and player work).
Brian approved the staging result and requested production publication on 2026-09-22.
The production entry point now enables `coherentGreeting`. Review remains at
`/review/greeting-consistency`; the component default remains false for legacy review routes.

## Root cause

The room greeting image and ambient loop use v149. The previous disc-polish
change patched v155/v156 *cubby* plates, not these greeting assets. Books and
photos pans already use the corrected player materials in v159/v160, while
the monitor and diploma pans still use the old v149 materials.

## Fix

Re-render the original v149 greeting, ambient loop, monitor in/out, diploma
in/out and diploma still with exactly the player material substitution used
by `restore_playback_v156.py`: source model RGB, emission strength `2**.3`,
and existing animated sweep/outline materials preserved. No arbitrary pixel
brightness adjustment or new sheen is added here.

Original camera paths, 24 fps timing, 1920×1080 resolution, 16 samples, scene
geometry and lighting are retained. The source blend and old public assets
are not overwritten. The new version is `public/room/v161`.

The first uncompressed greeting frame differs from the original by more than
3/255 at only 692 pixels, all within the player rectangle (1056,358)–(1097,382).
Six idle samples (0,48,96,120,192,239) have maximum differences of only 1/255
outside the player. The platter region at the beginning of the existing
vinyl/books/photos pans matches the new greeting within 2/255; corrected
monitor/diploma starts match within 1/255.

## Reproduce

```powershell
& 'D:/Blender5.2/blender.exe' -b --python blender/render_greeting_consistency_v161.py
& ./blender/encode_greeting_consistency_v161.ps1
```

`-- --probes` renders the greeting still only. Completed raw frames are reused
on restart. Raw frames and source blends remain ignored local authoring files.

## Review gate

Build, TypeScript and the 273-test regression suite pass. All five encoded
clips retain 1920×1080, 24 fps and their original frame counts (240/121/121/73/73).
Browser checks cover the idle loop and book/photo/monitor/diploma round trips.
The staging server
uses port 3001 because port 3000 belongs to GLM's separate checkout; that
checkout and server are untouched.

Published version: `58a836a7-ed3c-47ae-b9f9-3d8fd938030c`.
Rollback reference: `afb2dc84-99d3-4155-b85a-1305d4343961`.
Production home includes the approved flag; home, desktop and Spotify API return
200. All seven live v161 asset SHA-256 hashes match the approved local files.
