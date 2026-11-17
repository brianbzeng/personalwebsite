# Retired book highlight correction

The disabled book's white outline was baked into the room media. Removing its
hotspot/menu did not remove the rendered material.

The v162 render overrides only `CATHODE_WIREFRAME_BOOK_Mid_9` with the adjacent
decorative book's material. It does not edit the shared interactive pulse used
by the monitor, records or diploma, or save over any source blend.

Greeting and monitor/diploma frames reuse the v161 setup; vinyl pans reuse the
saved v155 scene and render-only parked-arm state; photos reuse v159. Original
cameras, ambient frames, samples and durations are retained. A camera-projected
render border limits replacement to the book region and composites onto the
original raw frame, preserving pixels outside that region. The greeting probe
and early ambient frames were full-frame renders; photo stills are full-frame.

Run sequentially (one Blender process at a time):

```powershell
& 'D:/Blender5.2/blender.exe' --factory-startup -b --python blender/render_greeting_consistency_v161.py -- --retire-book
& 'D:/Blender5.2/blender.exe' --factory-startup -b --python blender/render_book_retired_shelf_v162.py
& 'D:/Blender5.2/blender.exe' --factory-startup -b --python blender/render_photo_consistency_v159.py -- --retire-book
& ./blender/encode_book_retired_v162.ps1
python scripts/check_retired_book_scope.py
```

Runtime selects `/room/v162/` while `BOOK_EXPERIENCE_ENABLED` is false. Existing
vinyl cubby plates are unchanged. All previous media and animation sources remain
available in the repo. Raw render outputs stay local and ignored.

## v163 alignment correction (approved and published)

The v162 compositor used requested integer borders, but Blender quantizes its
normalized border coordinates as float32. Idle frame 42 onward therefore placed
the patch one pixel too high; the first 42 frames were full renders. The patch
included a shelf edge, making the discrepancy visible as a jump after 1.75s.

`scripts/repair_book_patch_alignment.py` recomposes the existing crop renders
against the original full frames using Blender's float32 multiply/truncate
placement. No resampling, scene changes, or old asset overwrites. Future renders
use a half-pixel border bias to keep each bound inside its intended integer bin.
`scripts/check_book_patch_alignment.py` independently checks unchanged high-
gradient crop margins; the former scope check could not detect errors inside
the excluded book rectangle.

Encode with `blender/encode_book_retired_v162.ps1 -Version 163`. Review all eleven
clips at `/review/shelf-alignment`. Brian approved the correction and the live
runtime now uses v163. New raw outputs are on `D:/CodexRenderCorrections` via junctions in
`blender/outputs`, because C: ran out of space; original raw frames are untouched.

Verification: all 738 gradient-rich patches pass the independent full-frame
alignment scan (no missing frames or failures); all 284 application tests and
TypeScript checks pass. Eleven encoded clips retain 1920x1080 and original frame
counts. Published as Worker version `128a5b8f-1888-4130-b7b2-bee9297681e1`.
All 15 live media hashes match local assets; home selects the v163 greeting.
