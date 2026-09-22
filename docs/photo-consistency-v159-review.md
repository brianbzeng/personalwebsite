# Photo cubby consistency — staging v159

Status: approved and deployed to brianbzeng.com on 2026-09-15 (local time). Version `ceebd94b-74dc-490b-8917-b7709934a311`.

Preview: `http://127.0.0.1:3000/review/photo-consistency`.

## Cause and correction

The photo cubby still used v154/v152 plates and v155 inter-cubby movies, while the records view used v156. Those older baked assets contained the former sleeve transforms and black player materials.

Re-rendered the photo still, photo-free background, room↔photos pans, and records↔photos pans from the saved v156 scene. The approved v154 direct camera keyframes, v137 cubby poses, v154 Polaroid geometry/placement and photo materials remain unchanged. Source blend and existing published media were not overwritten.

The `coherentPhotos` flag routes all six assets together, including the WebGL background readiness loader. Following approval, the home route now enables it. The independent `shelfReview` flag disables project auto-redirects only in the review route, preserving production behavior.

## Reproduce

- `D:/Blender5.2/blender.exe --background --python blender/render_photo_consistency_v159.py`
- `powershell -ExecutionPolicy Bypass -File blender/encode_photo_consistency_v159.ps1`

Rendering resumes completed frames in `blender/outputs/web-room-v159`; compiled media lives in `public/room/v159`. Raw renders are not deployment assets.

## Verification

- 258 authored frames/stills audited in private `scene-audit.json`.
- Direct pans: 91 frames each, 30 fps, 1920×1080.
- Inter-cubby pans: 37 frames each, 24 fps, 1920×1080.
- Photo still vs inter-cubby photo endpoints: pixel-identical before compression.
- Records inter-cubby endpoints: pixel-identical in both directions.
- Direct photo pan endpoint vs still: mean absolute RGB difference 0.000276/255 (subpixel camera precision).
- Lighting probe vs approved v156 records still: background crop pixel-identical. Apparent bands in the image-inspection preview were display/transcoding artifacts; no lighting change was applied.
- 12 focused tests passed: photo consistency, pan handoff, camera fit, Polaroid gallery and Polaroid review.
- Browser QA: room→photos, photos→records→photos, four-card gallery open/return, and photo→room paths checked; corrected player and sleeve silhouettes retained, no console warnings/errors in the preview.
- Production build passed. Typecheck still reports two pre-existing `Vector2` argument errors in `VinylPortfolio.tsx` at lines 344 and 383, outside this patch.

Release validation: 26 focused tests, production build and Wrangler dry run passed. All six live v159 assets returned HTTP 200 and SHA-256 matched the approved local assets; home and desktop returned 200, and Spotify reported ready. The old media remains available for rollback. Previous production version: `0d230168-f146-4d29-b4ca-5af2b4feb38f`.
