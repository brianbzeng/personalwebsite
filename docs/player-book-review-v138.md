# Player and book approval review — September 9, 2026

Status: the separate interactive model review remains at `/review/player-books`. The current source is **v149-approved-project-covers**, and its exported review models now use the approved versioned cover textures. Room footage has been rerecorded and integrated locally as v149; no deployment occurred. The main shelf still uses its existing inspection interaction; detailed player playback and multipart book binding distribution remain separate integration work. See `docs/room-release-v149.md`.

## Latest approval version — v148

`lofi-room-cathode-glm53f-city-v148-delayed-record-spin.blend` holds the landed record at frame 88 until frame 100 (0.5 seconds at 24 fps), then rotates clockwise at 33⅓ RPM. Position, flight, sleeve fade, tonearm and navigation cues are unchanged. A discreet label mark makes rotation readable. The local preview continues spinning after the playback timeline ends; Reset clears it and reduced-motion mode suppresses continued motion. Eleven regression checks pass. Production footage remains v137.

## Previous approval version — v147

`lofi-room-cathode-glm53f-city-v147-personal-polaroids.blend` adds Brian's four original photos to the Polaroids in viewer left-to-right order. Deterministic grayscale conversion and subject-aware square crops preserve the photos without generated changes. Images are packed; existing card geometry and transforms remain unchanged. Use the Polaroids tab on `/review/player-books` to inspect. Ten checks pass. See `docs/polaroid-v147-pending.md` for processing and QA details. Production footage remains v137.

## Previous approval version — v146

`lofi-room-cathode-glm53f-city-v146-seated-blank-vinyl.blend` seats the viewer-right blank sleeve (`INTERACT_Vinyl_0`) against its neighbor (`INTERACT_Vinyl_1`). Its original lean is preserved. The complete child assembly moves 8.95mm toward the neighbor and 8.86mm down to the shared shelf level; outlines nearly touch with 0.15mm clearance rather than intersecting. Seven timeline samples confirm the contact stays stable. Nine regression checks pass and isolated geometry QA confirms the contact. Existing room footage remains unchanged until re-recording is approved.

## Previous approval version — v145

`lofi-room-cathode-glm53f-city-v145-lit-player-wireframe.blend` hides the circled rest-socket tab and adds 0.12mm-radius physical feature lines to the J-arm and pivot. Lines share the room's `CATHODE_V131_Travel_record-player` material; contour shells use a culled copy of the same traveling-light shader. The web exporter carries the existing world-space sweep bounds/timing into the approval preview, including its 240-frame cycle and 96-frame traversal. Reduced-motion suppresses the idle light clock.

The 0.2s fade delay and smooth 1.33s ramp remain. Fixed the visual onset pop in the browser: the sleeve stays opaque in the scene, and a full-scene/background composite fades it as one image. No mid-fade transparency/depth-write switch and no rear-face reveal. Inspected frames 16/17/18/33/49, full playback/reset, and the lit/unlit contours. Eight regression checks and the build pass. No production room footage was re-recorded.

## Previous approval version — v144

`lofi-room-cathode-glm53f-city-v144-themed-player-delayed-fade.blend` adds a 0.2-second hold after sleeve sliding starts, then preserves the 1.33-second smooth fade (frames 16.8–48.8 at 24fps). Sleeve poses and record/arm timing are unchanged. New player parts now use object-specific matte charcoal/graphite materials, muted gray collars/rims and thin reverse-wound silhouette contours, not polygon wireframes. The rest socket no longer uses the pale record-label material. Exported contour culling and roughness are honored in the local review. Seven regression checks, full browser playback/reset and the build pass. No room footage was re-recorded.

## Previous approval version — v143

`lofi-room-cathode-glm53f-city-v143-simplified-pivot-sleeve-fade.blend` removes the visible rear lift shoe and both side bearing-cap/screw assemblies at Brian's request. Hidden originals remain recoverable. The sleeve now fades smoothly from frame 12 to 44 (1.33 seconds), beginning with its slide. All 144 sampled sleeve poses are unchanged. Six regression checks and the production build pass; browser playback and reset were checked. No room footage was re-recorded.

## Previous approval version — v142

The current review is `lofi-room-cathode-glm53f-city-v142-detailed-pivot-rest.blend` in the same Blender output directory. The researched multi-part pivot/rest supersedes the simpler v141 assembly. See `docs/tonearm-reference-research-v142.md` for official sources, photo-derived geometry, reproduction scripts and evidence limits. The existing J arm, fixed bearing motion, contact timing and half-height plinth remain unchanged.

## Previous approval version — v141

`blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v141-solid-pivot-j-arm.blend` supersedes v140 for review. The diagonal bearing is a solid beveled body with an actual shaft bore, not an open supporting strap. It rotates with the arm's yaw while retaining a fixed bearing center; the shaft's small pitch remains independent inside the bore.

The arm now has a smooth 45-degree J bend. The headshell, cartridge and fine needle follow its terminal direction. The base body is exactly half-height (75 → 37.5 mm), anchored at its original bottom, with rebuilt constant-thickness edge contours. Platter and arm sit lower; the record flight endpoint and needle contact were recalculated for the new heights and geometry. The rest has been repositioned onto the straight shaft and shortened accordingly. Contact remains frame 122, followed by the existing sound/new-tab sequence.

Reproduce with `rebuild_player_v141.py` on v140, then `export_review_v138.py` on v141. The existing `review_tonearm_v140.py` also accepts v141 for non-mutating diagnostic stills. Tests check half-height base, fixed housing/shaft bearing, J offset, thin needle and corrected contact. No bookshelf distribution or production footage was changed.

## Previous tonearm corrections — v139/v140

Latest review update: **v140-reference-tonearm.blend**, in the same Blender output directory. This replaces the tall solid pivot and barrel counterweight with a shallow annular mounting housing, one diagonal bent support, and a 26 mm continuation of the arm shaft. The cartridge now has a 0.48 mm cantilever and a tapered stylus ending at a 0.07 mm contact diameter. All 144 arm poses from v139 are unchanged. Earlier models are hidden and retained, not deleted. `refine_tonearm_shape_v140.py` creates the version; `review_tonearm_v140.py` captures isolated top/oblique stills. Export with the existing review exporter. Approval boundary remains unchanged.

- Latest approval file: `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v139-anchored-tonearm.blend`. The v138 source is preserved.
- Removed the entire arm's 14 mm vertical translation. Its rear bearing stays at the same world position for all 144 frames. A one-degree rotation about that bearing raises the needle end only 3.48 mm, followed by a horizontal swing and gentle lowering.
- Needle lands at a 114.46 mm radius on the 120 mm record, with 0.05 mm surface clearance. Contact/sound at frame 122 and project handoff at 138 remain unchanged.
- Reproduce with `fix_tonearm_pivot_v139.py` on v138, then `export_review_v138.py` on v139. The review keeps its stable `public/review/v138/` asset URLs. Do not run the older `refine_review_v138.py` after this fix.
- Evaluated Blender positions and exported-mesh tests check the fixed pivot, small tip lift, and outer-groove landing. Browser swing/contact stills and the numerical audit are in `blender/outputs/review-v139/`. Full preview playback and reset were checked locally. No room footage has been re-recorded.

## Saved Blender files

- `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v138-review-source.blend` preserves the unsaved v137 GUI state before this work. The GUI file was not replaced.
- `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v138-player-book-review.blend` is the new approval file, not the production render source yet.
- Its main scene opens on `CAM_V138_Player_Review`, frames 1–144 at 24 fps. This is a selected-record demonstration: the original CastingCompass sleeve is hidden while its inspection copy is out of the rack.
- `V138_Book_Prototypes` contains the separate hardback and paperback assets, with cover hinges, lining paper, page blocks, sparse page-edge geometry, and three separately hinged/curling blank leaves. Frames 1–78 open the cover; later frames turn the leaves. Models have not been distributed through the shelf.

## Decisions and changes

- Back-right player pivot uses +X/-Y; platter shifted viewer-left (+Y). New parked arm points forward (-X) and sits in a small rest. Old player components are hidden and retained, including their old outlines; the original base stays.
- Record is a thin ring with an actual spindle hole, label, and subtle grooves. The record transform is identical at every sampled frame 1–42. Sleeve moves +Y (viewer-left) and fades before the disc flies and flips onto the platter.
- Landing frame 88; arm lifts, swings, lowers; needle contact/sound frame 122; project handoff frame 138. Spin begins on landing. Browser demonstration uses CastingCompass. The same choreography can be reused for the other existing project URLs after approval.
- Brian chose a new tab, subtle needle-drop sound, and hardback for the report book. The browser uses an original short filtered-noise cue, never music. Delayed new-tab blocking has a normal accessible link fallback. Reset/unmount/view switches cancel pending navigation.
- Top run still uses the original books. `BOOK_Mid_9` lean changes from 8° to 4° and its actual outline has 0.15 mm clearance to its neighbor. Other contour clearances are 0.7 mm. All existing object transforms except the ten packed books and their paired outlines remain unchanged.
- Hardcover page block is visibly inset with separate thicker cover slabs; paperback covers are thin and nearly flush. No report text or new cover art was invented.

## Reproducible pipeline

1. `prepare_review_v138.py` on the review-source snapshot (refuses to overwrite the target).
2. `refine_review_v138.py`, then `finish_review_v138.py` on the owned approval file.
3. `export_review_v138.py` exports real model meshes and sampled Blender rig matrices to `public/review/v138/`. These assets only load on the separate review route.
4. `review_v138_probes.py` renders a few approval stills, not production clips. Browser QA captures are in `blender/outputs/review-v138/`.

## Approval boundary / next integration

After approval: decide seeded binding distribution, replace bookshelf book bodies with the approved multi-part assets, preserve existing dimensions/orientations and contour spacing, export the report book's components, and integrate the record playback state machine for all five existing projects. Re-render backgrounds without moving arm/headshell/record pieces to avoid double geometry. Re-record the updated room/shelf clips only then. Keep two viewer-right sleeves blank and non-interactive.

## Checks

- Numerical asset tests: stationary disc, sleeve direction/fade, landing/arm ordering, separate book components, positive outline gaps, and v137 production-media isolation.
- Browser: record reveal/flight/landing, book cover and both bottom-corner page directions, and new-tab callback ordering. The needle cue fired ~0.67 seconds before the project callback; cancellation produced neither a late cue nor a redirect. External navigation was stubbed during QA, so no third-party page was opened by the tests.
- Final checks: 125 tests and `pnpm build` pass. Delayed-popup fallback retains a `_blank` link. Paperback opening/page changes work at 390px with reduced motion and no horizontal overflow. Browser test stubs were removed by a final reload.
- Existing unrelated issues remain: two `VinylPortfolio.tsx` Vector2 TypeScript diagnostics and missing `/favicon.ico`. No new TypeScript diagnostics from the review components.
- The Sites build wrapper could not launch the package manager on this Windows environment; the existing `pnpm build` workflow was used successfully instead. Existing lazy Three.js chunk warning remains.
