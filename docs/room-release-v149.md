# Approved covers and room rerender — v149

Local-only update requested after approval of the final F1 flag. No deployment, commit, or push.

## Source and artwork

Source: `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v149-approved-project-covers.blend`.

All five front/back pairs use the approved v4 artwork, except the F1 front, which uses v7 (smaller rectangular checker field, square checkers, contrasting gray pole and outline). Spines are unchanged. Exact PNG files are copied into `public/room/vinyl-art/v149/` and packed into Blender. The source retains the separate player/book review rigs and animations.

The v148 review source had the named greeting camera moved to a book close-up. `restore_greeting_v149.py` restores it from the unchanged monitor path's first pose. The numerical camera audit compares all six release cameras at twelve sampled timeline positions against v137; framing, lens and shifts match.

## Render preparation

`prepare_room_render_v149.py` makes render-only changes without saving them:

- Restores the source CastingCompass sleeve hidden for the separate playback demonstration.
- Hides the demonstration sleeve/disc copies and freezes the player arm at its parked frame-one pose; room lighting still advances normally.
- Re-exports active sleeve poses, decorative sleeve occluders and the packed report book geometry from the current scene.
- Preserves the corrected leaning blank cover, updated player pieces, four personal Polaroids and all existing room geometry.

## Reproduction

1. `apply_approved_covers_v149.py` on v148 creates v149 and refuses to overwrite it. Then run `restore_greeting_v149.py` on the newly owned v149 file.
2. `audit_cameras_v149.py` compares against the approved v137 source. `prepare_room_render_v149.py` rejects a misplaced greeting camera.
3. In one Blender process, run `prepare_room_render_v149.py`, then `render_shelf_v137.py -- --v149`. This renders seven plates and eleven 1080p/24 fps sequences (929 PNGs). Existing completed frames are resumable.
4. Run `prepare_room_render_v149.py`, then `render_hover_mask_v130.py -- --v149` in a separate Blender process. Reversed silhouette-shell backface culling is preserved in the mask.
5. `encode_room_v149.ps1` produces versioned WebP/H.264 media. `verify_room_v149.mjs` checks exact approved artwork, silent 1080p/24 fps video streams, frame counts, 6 MB per-clip budgets and decoded-pixel endpoint continuity.
6. `export_review_v138.py` on unprepared v149 refreshes the separate animated review assets with the approved textures. Do not freeze review rigs before this export.

For this run only, the greeting close-up was caught during QA after part of the sequence had rendered. The saved camera was restored, and `finish_room_v149.ps1` rerenders only the greeting and idle sequence after the remaining correct camera clips finish, before mask generation and encoding.

## Scope boundary

This release updates room footage, current shelf geometry, photos and approved cover artwork. The separate `/review/player-books` route retains the detailed player playback and book-binding demonstrations. Promoting that playback state machine to all five records and distributing multipart book bindings throughout the shelf are separate integration work, not effects produced by rerendering footage alone.

Earlier Blender sources and `public/room/v137/` remain available for rollback.

## Completed validation

- 136 Node tests and `pnpm build` pass. The Sites build wrapper could not resolve its Windows launcher; the project's existing build command succeeded. Its pre-existing lazy 3D chunk-size warning remains.
- All eleven videos are silent 1920×1080/24 fps, with correct frame counts and below 6 MB each. Greeting WebP: 82,812 bytes. Idle video: 1,215,990 bytes. Cursor mask: 121,067 bytes.
- All nineteen decoded-frame endpoint comparisons pass; fourteen are pixel-exact and five measure SSIM 0.999992–1.000000. All shelf arrivals/departures and inspection plates are pixel-exact.
- Browser checks loaded only v149 room media and the fifteen approved versioned textures. All five cover inspections retained their existing project URLs. Shelf movement, photos, book opening/page controls, and monitor/diploma returns work locally.
- A sampled monitor return recorded no uncovered frame before the video was presented. At 390px, reduced motion rendered no videos, forward/backward book page controls worked, and document width stayed within the viewport. The first narrow-screen attempt clicked before hydration completed; repeating after hydration passed without source changes.
- Browser console had no current errors in the final check. Earlier root navigation showed the existing missing favicon. Local development was restarted through the Node CLI after the fallback package-manager launcher failed to start its worker runtime. The server remains available at `http://127.0.0.1:3000/`.
