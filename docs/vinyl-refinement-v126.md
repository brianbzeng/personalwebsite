# Project vinyl refinement — verified locally

The supplied screen recording showed an unlabeled-to-labeled handoff at the end of the vinyl approach, weaker outlines in WebGL, and a greeting-frame flash when starting the return.

## Changes

- Keep the departing close-up/desktop mounted until the return video presents a decoded frame. Remove the opacity crossfade that exposed the room underneath.
- Bake shared front, back, and spine textures into a separately saved Blender scene. Use those identical texture files and exported UVs in Three.js. Only spine lettering rotates 180 degrees; covers remain upright.
- Seven selectable sleeves, viewer-left to viewer-right: CastingCompass, Amazon, F1 Constructor, NBA Home Win Predictor, TTB Label, Coming soon, Data Science Report Hub.
- Direct destinations are centralized in `app/data/vinyls.json`. The two future records have no destination.
- All sleeves have square faces (0.2585 × 0.2585 scene units). The rightmost sleeve retains its authored lean.
- Twelve physical edge outlines per sleeve, shared radius 0.0013; no dependence on one-pixel WebGL lines. Holder depth masks remain.
- Upward drag tips the top edge forward. Horizontal direction remains unchanged. Front/Back selects an exact opposite face and resets tilt, using a camera-facing quaternion basis.
- The labeled Blender still stays visible while the interactive scene and textures load.
- Re-rendered all six camera clips and idle loop, retaining the approved camera paths and full-HD compression settings.

## Verification

- Reviewed the supplied recording as a temporal contact sheet, then inspected the new Blender close-up and browser front/back images.
- Browser: all seven selections, five direct links, coming-soon no-navigation, and exposed-record navigation (destination request intercepted to avoid leaving the test in an external app).
- Browser: upward/horizontal drag followed by a straight-on, upright back-face snap.
- Delayed the return-video request and sampled rendered states: no uncovered greeting/idle layer before the transition became visible.
- Browser: 390 × 844 layout without horizontal overflow, reduced-motion path without transition videos.
- Eleven focused tests pass; production build passes; all seven encoded videos decode successfully.
- Full TypeScript check still reports the two pre-existing Vector2 argument errors in the unused legacy `VinylPortfolio.tsx`; no new TypeScript errors were reported.

## Preserved work

Original v121 scene and unrelated user edits are untouched. New packed-texture scene: `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v126-project-vinyls.blend`.

No deployment, commit, push, or external account changes were performed. The existing local preview remains running.
