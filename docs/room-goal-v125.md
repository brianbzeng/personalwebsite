# Room goal: implemented and verified locally

## Implemented

- Geometry remains square and unchanged. Greeting lens shift centers top/bottom
  margins at approximately 108/110 pixels in the 1080p render.
- Monitor approach deliberately looks through the windows before landing on the
  blank screen. Boot, embedded desktop, and return remain intact.
- Diploma has only its camera close-up and return, without an About redirect.
- Vinyl holder enters a close-up. The seven original sleeve meshes are exported
  as compact JSON, with two holder meshes used as invisible depth occluders.
- Five existing projects map to the five upright inner sleeves. The two outer
  decorative sleeves retain their original geometry, including the leaning one.
- Hover uses the original 0.085 world-unit travel, with smoothly interruptible
  interpolation. Selection extracts the sleeve into an inspection pose.
- Drag to turn/tilt, front/back control, project icon and title on front, summary
  on back, and a partially exposed record that links to the project when clicked.
- Keyboard/touch controls, return-to-holder, and non-WebGL project links included.
- Three.js is dynamically loaded only for the vinyl close-up, not the greeting.

## Media

`render_release_room_v125.py` produces 1920×1080, 32-sample footage from the
preserved v121 Blender source. It modifies cameras only in the background copy.
`encode_release_room_v125.ps1` produces silent 24 fps H.264 CRF 18 fast-start files.
All six camera clips and the idle loop are now encoded in public/room.
The idle loop is 888,798 bytes. Transition clips are approximately 1.8–2.4 MB each
and are only loaded on demand. Geometry plus occlusion data is only a few KB.

## Verification

The continued goal explicitly requested interaction verification. Browser checks
were completed against the local site at desktop and narrow-screen sizes:

- Actual sleeve hover changed the rendered position; clicking the NBA spine
  selected NBA Odds Predictor, rather than a neighboring sleeve.
- Selection, pointer drag, front/back, and return-to-holder exercised.
- Back texture orientation corrected after screenshot review.
- Outline raycasts were intercepting disc clicks; non-mesh intersections are
  now excluded. Clicking the exposed disc navigated to /projects/castingcompass.
- All five project selections produced their correct case-study links.
- Diploma stayed on the homepage, showed the close-up, and returned.
- Monitor approached, booted, displayed the existing terminal greeting in the
  desktop iframe, and returned.
- Narrow-screen inspection expands its stage for readable sleeve content;
  reduced motion omitted transition videos and had no horizontal overflow.
- Latest page console had no errors. Seven regression tests and build passed.
- All seven final video assets decoded successfully with ffmpeg.

Screenshots are in blender/outputs/vinyl-browser-*, vinyl-back-fixed.png,
vinyl-front-settled.png, and vinyl-mobile-back.png. The mobile screenshot precedes
the final increase in back-summary text size.

No deployment, scene overwrite, or Git commit was made.

Sites building skill governed this existing-site implementation. Publication is
not part of this local validation pass; obtain approval for existing site audience
before publishing. The previous first-slice handoff describes superseded media.
