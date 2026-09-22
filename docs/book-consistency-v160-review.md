# Top cubby consistency — staging v160

Status: approved and published on 2026-09-16, version `2679504d-cbfb-40e5-bc15-b03ae1674f5b`. All six live runtime media hashes match the approved local assets.

## Cause and correction

The top book cubby still used v149 still/background plates, v150 direct room pans, and v155 books↔records pans. These baked assets predated the v156 sleeve clearance and record-player material corrections, so looking down from the book cubby reintroduced the old clipped vinyl edges.

The six v160 assets are rerendered from the saved corrected v156 scene. The original `CAM_BooksApproach_v150` camera keys, 73-frame direct pans, 37-frame adjoining cubby pans, camera framing, and book transforms are preserved. Only the movable report book and its outline are hidden for the interactive background plate. Source blend and previously published media remain untouched.

`coherentBooks` independently opts into the v160 plates and camera paths. The component default remains false; the approved production home explicitly enables it. `coherentPhotos` continues selecting the separately approved v159 photo assets.

## Reproduce

- `D:/Blender5.2/blender.exe --background --python blender/render_book_consistency_v160.py`
- `powershell -ExecutionPolicy Bypass -File blender/encode_book_consistency_v160.ps1`

Raw output and the camera/transform audit remain in `blender/outputs/web-room-v160`. Runtime-only media is in `public/room/v160`. Renders resume completed frames without modifying source files.

## Verification

- Old/new stills visually inspected: sleeve top/back edges are complete in v160 rather than disappearing into the cubby wall.
- Independent opt-in routing and preservation of approved records/photo assets covered by `tests/book-consistency.test.mjs`.
- 222 frames/stills rendered and camera poses audited. Direct pans retain 73 frames at 24 fps; adjoining pans retain 37 frames at 24 fps. All assets are 1920×1080.
- Both book-side inter-cubby endpoints are pixel-identical to the new book still (SSIM 1.0).
- Both records-side endpoints are pixel-identical to each other and to the approved v159 records→photos starting frame (SSIM 1.0).
- Direct room→books endpoint and books→room start match the book still at SSIM 0.999999 (subpixel camera precision).
- Nine focused book/photo consistency and pan handoff tests pass.
