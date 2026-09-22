# Landscape mobile review — approved and published

Review routes:
- `/review/mobile-layout`: opt-in room/shelf changes, and the mobile desktop iframe.
- `/review/mobile-desktop`: isolated workstation sizing review.
- `/review/handwritten-cues`: separate animated white SVG cue study.

Approved and published on 2026-09-16 as version `de1da3d6-5c98-4a5c-bd8e-c205ddfecf61`. Production now uses `<CinematicRoom coherentPhotos mobileLayout activityCues />`; direct `/desktop` also enables the responsive layout. Review-only redirect suppression and replay controls are excluded. The notes below describe the original staging implementation; final cue coverage is documented in `activity-cues-review.md`.

## Changes

- Short landscape layouts (width <=1024px, height <=600px) use a right-side room menu, compact controls, and viewport-fitted books, records, photo galleries and enlarged photos. Authored shelf resting poses and camera paths are preserved.
- The workstation has separate terminal and scrollable widget lanes, compact typography, and no automatic touch keyboard activation.
- Diploma artwork opens in an accessible native dialog on both desktop and phone in the review route. Escape/backdrop/Close dismiss it and restore trigger focus.
- In the review route, Play record has no arrow and transitional shelf status remains available to assistive technology without visible overlay text.
- Handwritten Swipe Right and Drag are scalable SVG/CSS loops, not raster GIF files. They ignore pointer input, respect reduced motion, and are not yet integrated into the room. Existing action buttons remain pending cue approval.

## Verification

- Browser inspection: room menu, book, vinyl, four-photo lineup, enlarged photo and diploma at 926x322; workstation at 926x322 and 667x300; cue study at desktop size.
- `pnpm build` passes (existing large-chunk warning).
- 21 focused mobile, cinematic, cue and photo tests pass; additional camera-fit/pan-handoff regression checks also passed.
- `pnpm exec tsc --noEmit` reports only two pre-existing Vector2 argument errors in legacy `VinylPortfolio.tsx` (lines344/383). No new type errors from this review.
- Physical iOS/Safari testing still recommended before approval; viewport testing is not a substitute for hardware/browser validation.

## Approval boundary

Do not remove redundant controls, promote this layout, or deploy until Brian approves the corresponding preview. Preserve desktop sizing apart from the requested shared diploma and UI-cleanup changes when promoting.
