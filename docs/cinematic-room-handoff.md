# Current room and bookshelf work — September 10, 2026

Current local release: **v149-approved-project-covers**. All room, monitor, diploma and shelf footage now uses `public/room/v149/`, with matching current shelf geometry and a freshly rendered cursor-light mask. The five approved front/back pairs use v4 artwork plus the final v7 F1 front; unchanged spines and versioned textures are packed into v149. The saved greeting camera has been restored to the approved full-room framing. See `docs/room-release-v149.md` for reproduction and scope.

Validation: 136 Node checks and `pnpm build` pass. Eleven silent 1080p/24 fps videos are under 6 MB each; all 19 raw endpoint comparisons have SSIM >= 0.999992. The greeting image is 82,812 bytes and the idle loop 1,215,990 bytes. Local browser checks covered all approved cover textures, shelf cubby moves, photos, monitor/diploma returns and 390px reduced-motion book page navigation. No deployment occurred. Detailed record-playback choreography and multipart book prototypes remain on the separate review route; rerendering does not itself promote that interaction state machine into the main shelf.

## Earlier milestones (historical)

Latest approval-only update: **v148-delayed-record-spin** adds a 0.5-second landed hold followed by clockwise 33⅓ RPM rotation, with a small label mark and continued local-preview playback. Existing flight, arm and redirect timing are unchanged. Eleven checks pass. Production room remains v137; no rerecord or deployment.

Previous **v147-personal-polaroids** packs Brian's four faithful grayscale, square-cropped photos onto the existing Polaroids (D,C,B,A in viewer left-to-right order). Original images are retained; no generative edits were used. Review has a Polaroids tab, with browser QA and audit under `blender/outputs/review-v147/`.

Previous **v146-seated-blank-vinyl** closes the viewer-right decorative sleeve gap and seats its foot at its neighbor's shelf height, preserving lean and coherent child transforms. See `blender/outputs/review-v146/contact-audit.json` and `sleeve-contact.png`.

Latest approval-only update: **v145-lit-player-wireframe** removes the small black rest-socket tab; adds thin J-arm/pivot feature curves driven by the existing record-player traveling-light material. The browser now composites the solid sleeve against the background for a smooth whole-cover fade, retaining the 0.2s delay. Lighting metadata survives export and animates in the approval preview. Eight checks, playback/reset and build pass. Source: `blender/wire_player_v145.py`. Main room footage remains v137 pending approval.

Latest approval-only update: **v144-themed-player-delayed-fade** adds a 0.2s sleeve-fade delay and themed matte gray player parts with thin silhouette-only contours. Browser review handles front-face culling for the reversed contour shells and material roughness. Source and audit: `blender/theme_player_v144.py`, `blender/outputs/review-v144/theme-audit.json`. Seven checks and build pass; production room remains v137 pending approval.

Latest approval-only update: v143 simplifies the pivot by hiding the rear lift shoe and two side cap/screw assemblies. Sleeve opacity fades across frames 12–44 while preserving its original movement. Review assets are refreshed at `/review/player-books`; main room remains v137. Source: `lofi-room-cathode-glm53f-city-v143-simplified-pivot-sleeve-fade.blend`. Build and six regression checks pass.

September 9: the separate player/book **approval review** now uses v142 with a photo/official-diagram-led stepped pivot, nested bearings, shaft collar and molded rest clamp. The J arm, fixed-pivot motion, fine needle and half-height base are preserved. See `docs/tonearm-reference-research-v142.md` and `docs/player-book-review-v138.md`. The website and production footage described below deliberately remain v137 until Brian approves the new models and motion.

The current scene is `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v137-shelf-book-lamp-glow.blend`.
Earlier scenes and the unsaved Blender GUI session were preserved. Work remains local-only.

- v137 preserves all existing object transforms, the rug, rounded monitor path, white highlights, and lightning loop. Both translucent lamp heads now have stronger soft radial light and a restrained fabric glow.
- Only five records are interactive. The two viewer-right covers are blank, retain their authored placement/lean, and stay baked into both full and background plates.
- The old v126 export captured a stale -0.29-radian lean instead of the current -0.2583 pose. v137 re-exports evaluated transforms and does not duplicate the decorative covers in WebGL.
- Shelf entry now centers the entire record cubby. Up/down moves cover only the top three cubbies: books, records, and camera/polaroids.
- `BOOK_Mid_9` is the viewer-left book in the top vertical run. It slides forward, presents a closed front-facing cover, opens, and turns through three blank spreads. Report content and polaroid images are intentionally deferred.
- Browser tests cover navigation boundaries, page direction, fixed book orientation, existing record links/flip, reduced motion, narrow view, keyboard return/focus, and failed/stalled loading recovery.
- PNG comparisons: full shelf still equals both entry endpoint and return start exactly; the fixed-cover crop also equals its background plate exactly (SSIM 1.0).
- `prepare_shelf_v137.py` creates the new source and compact geometry. `bake_shelf_cameras_v137.py` retains the exact approach and shelf-navigation moves as editable Blender cameras. `render_shelf_v137.py` and `encode_shelf_v137.ps1` produce the 1080p/24 fps media in `public/room/v137/`.
- All room, monitor, diploma, and shelf media now use the completed v137 render set. All clips are 1080p/24 fps and under the 6 MB per-clip release budget; shelf navigation clips are under 350 KB each.
- Final validation: all 121 Node tests and `pnpm build` pass. The complete v137 monitor, diploma, shelf, and open-book return routes were checked in the local browser, with no browser console errors. The build retains its existing lazy 3D chunk size warning.
- TypeScript still reports the two pre-existing Vector2 errors in the separate `VinylPortfolio.tsx` route, not in the new shelf components.

## Historical initial slice (superseded)

The homepage now uses CinematicRoom instead of the former Three.js vinyl homepage.
Existing desktop, projects, and about routes are preserved. No deployment made.

## Working implementation

- Approved room greeting image and compressed animated loop.
- Projected clickable regions; text shortcuts provide usable mobile targets.
- Monitor approach, boot reveal, embedded live desktop, and return movie.
- Transition media and desktop are mounted only when needed.
- Reduced-motion preference, manual motion toggle, hidden-tab video pause,
  autoplay image fallback, skip control, and transition timeout fallback.

## Assets

Source scene: city v121 blank-idle-monitor. Original scene remains untouched.
Render scripts: render_web_room_v121.py and render_monitor_targeted_v122.py.
The second script corrects the camera aim while preserving its path positions.
Source PNG sequences remain under blender/outputs/web-room-v121 and web-room-v122.

All videos are 1280×720 at 24 fps, silent H.264 with fast-start metadata.
The idle loop uses a half-second wrap dissolve to smooth the lighting seam.

| Public asset | Bytes |
| --- | ---: |
| greeting.webp | 29,674 |
| idle.mp4 | 282,803 |
| monitor-in.mp4 | 668,096 |
| monitor-out.mp4 | 689,850 |

## Validation and remaining work

- Production build passes. Four source/asset regression checks pass.
- Local homepage returns HTTP 200.
- Rendered greeting, approach midpoint, and endpoint inspected as images.
- Browser interaction/mobile QA not yet performed; source tests do not prove playback.
- TypeScript check still reports two pre-existing Vector2 argument errors in
  VinylPortfolio.tsx, the old homepage component; no new component errors reported.
- Vinyl and diploma still link to existing pages: their new transitions and final
  content treatment remain to be built. Left-side vinyl clarification is unresolved.
- Camera aim correction exists in the render script, not saved over the user's blend.
- Recheck visual continuity, desktop loading failures, narrow screens, media behavior,
  and actual homepage network payload before treating this as release-ready.
- Sites building skill used; publishing is deferred until the requested final
  experience is complete and the existing site's publication audience is approved.
