# Player disc polish — staged, awaiting Brian's approval

## The bug Brian reported
The record player's disc read as pitch black in the **idle shelf (main menu) view**, but looked correct during camera pans / the playback close-up.

## Root cause (verified empirically, 2026-09-22)
- In idle, the WebGL canvas paints **nothing** in the turntable area (only thin wire outlines). The whole player body comes from the **photographic plates** (`/room/v155/` + `/room/v156/` `vinyl-background.webp` / `vinyl-still.webp`).
- Those plates bake the record at ~0-7/255 with rings at ~34 — a black hole at shelf distance. The plates were re-baked in the v155/v156 "seamless playback" iterations, which is when it became noticeable.
- The 3D player model (`public/review/v138/player.json`) is byte-identical since its original commit; it was never the problem. Not a three.js issue (renderer outputColorSpace/ColorManagement verified correct).

## Changes (all on `main`, **not deployed**)
1. `blender/brighten_plate_disc_v157.py` — asset patch lifting the baked disc in the four plates (radial cosine falloff, `LIFT=40`, `RADIUS=100`, disc centers v156 (350,772) / v155 (354,758)). Encoded WEBP quality=100; measured ≤2/255 diff outside the disc. **Re-run this script after any plate re-bake.**
2. Cache-busting: plate URLs now carry `?v=157` (`panHandoff.ts`, `CinematicRoom.tsx`, `shelfPlaybackStaging.ts`) so browsers/CDNs drop the stale black-disc copies. **Bump `?v` whenever the plates change again.**
3. `shelfRecordPlayer.ts` — the 3D disc surfaces (platter, rim, record, grooves, label, spindle) ride the same white sweep band as the tonearm (`DISC_SWEEP`), the record/label carry a rotation-invariant radial sheen (`DISC_SHEEN`), and the label base color is lifted to 0.14. Affects the playback close-up only (idle uses the plates).
4. `/review/player-polish` staging route (records cubby, review mode). Verified in-browser: idle disc samples 35-88 gray with rings (was 0-15 black).
5. Tests: `tests/player-disc-polish.test.mjs` (sweep band parity, sheen, cache-bust pins); `tests/white-interactives.test.mjs` pins the `?v=157` URL. Full suite 270/270 green; `tsc --noEmit` clean.

## Pending
- Brian's approval of the staging look (`pnpm dev` → http://127.0.0.1:3000/review/player-polish). Possible tuning: `LIFT` in the patch script (disc brightness vs playback shot) or sheen/sweep intensities in `shelfRecordPlayer.ts`.
- After approval: promote (nothing to flip — the plates/URLs are already the main experience's assets; the staging route is just for review) and deploy per `docs/production-release.md`.
- Optional "proper" fix if Brian prefers: re-bake the plates in Blender with lightened disc materials instead of the pixel patch (see `blender/` bake scripts, e.g. `seamless_player_v155.py`, `restore_playback_v156.py`).
