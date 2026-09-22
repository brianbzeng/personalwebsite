# Activity cue staging

Review route: `/review/activity-cues`. Book close-up mockups: `/review/book-cues` (mouse/touch selector).
Approved and published on 2026-09-16 as version `de1da3d6-5c98-4a5c-bd8e-c205ddfecf61`. The production home enables the approved cues and mobile layout, without review-mode redirect suppression. Replay controls remain staging-only.

## Follow-up refinement — approved and published

Brian approved publication on 2026-09-16. Both `refinedCues` and `coherentBooks` are enabled on production, version `2679504d-cbfb-40e5-bc15-b03ae1674f5b`, without review-only replay or redirect suppression. Review routes remain available for future iteration.

- Point-arrow shafts are half-length, with fixed tips. Greeting arrow motion is 6 seconds over 1.5px instead of 1 second over 5px; lettering drifts gently over 9 seconds. The room book pointer shifts left to the interactive book.
- Revised notes hold for 2 seconds before their existing 450ms fade. Top-cubby book target freezes after settling instead of following hover movement.
- Scroll/Swipe is 35% larger, page-centered vertically at the right edge with phone-safe clamping.
- Shelf photographs say Click/Tap; enlarged-gallery and diploma prompts retain Click/Tap to Enlarge.
- Per-room memory consumes each visited cubby's prompts after fading or leaving. It survives leaving/reopening the shelf and resets on refresh. Successful wheel/touch navigation suppresses both hover and scroll guidance. Staging Replay notes explicitly clears this memory for review only.
- Six corrected v160 top-cubby plates/clips replace the stale book-view vinyl geometry in staging. See `book-consistency-v160-review.md`.

Verification: 61 focused tests and production build pass. Browser-verified scrolling removes Hover/Scroll, revisited photo cubby has zero cue opacity, and dismissal survives returning to the room. Checked right-edge cue at 926×322; captured room, records, photos, top-books and phone previews in `docs/previews/*-v3.png`. Corrected direct book clip loads with readyState 4 and no media error. Typecheck continues to report only the two existing legacy VinylPortfolio Vector2 errors.

## Shared behavior

Inspection anchoring correction published on 2026-09-16, version `668c479a-79ed-42ba-8434-483e93ffa2a2`: the 3D scene clears old bounds on selection and publishes selected-object cue targets only after motion settles. This ensures the frozen layout uses the final close-up, not the starting shelf slot. Verified in browser and with actual Three.js projection regression tests.

Stationary layout and interaction dismissal were published directly at Brian's request on 2026-09-16, version `0bb2362a-5bb7-4680-8e15-905e67570327`. This supersedes the earlier floating/bouncing behavior described in the refinement history.

Approved and published on 2026-09-16: production home, `/review/activity-cues`, and `/review/book-cues` enable `cueFadeIn`. Following the existing invisible 600ms settling delay, each cue fades in for 450ms, remains fully visible for 1100ms, and fades out for 450ms: exactly 2000ms total visible lifetime. Both geometry polling and completion use the same end timestamp; existing hidden-tab/dialog/busy pause behavior is retained. Production version: `d6a239df-3499-4cec-a237-227a850ea87c`.

- Approved Manic regular plus three alternate faces, seeded randomized selection for every letter, avoiding adjacent identical faces. Each instance differs; rerenders never change its lettering.
- Small white handwriting and soft glow. All cue lettering and arrows are stationary: no rocking, floating, bouncing, or object tracking.
- Production waits for the view and fonts to settle (600 ms), then uses a 450ms fade-in, 1100ms hold and 450ms fade-out. Greeting arrows never return after fading or leaving until refresh.
- A press/touch, wheel gesture, or navigation/activation key immediately hides and consumes the current cues, before dragging or another object animation begins. Resizing also dismisses rather than repositioning visible notes. No event is prevented or intercepted.
- Hover never dismisses a note. Hidden tabs, modal dialogs, and busy views do not consume its reading time.
- Notes never intercept pointer events. Staging-only `Replay notes` restarts shelf/diploma notes only; greeting arrows cannot be replayed.
- Target bounds come from the rendered objects or live DOM once the view is ready. The entire initial layout is frozen and geometry polling stops; text stays outside the target and pointing tips overlap by only 1.5 px. Removed cues stay removed without repositioning the others.
- Phone inspection reserves a stable top lane for Drag/photo notes. Fading does not resize or shift the object.

## Coverage

Room: arrow-only pointers to monitor, records, books, photos, diploma, with tighter book/photo anchors.

Shelf: choose books/records/photos, hover records, vertical scroll/swipe, open book, previous/next page, figure zoom. Record labels: Drag, Flip, Redirect. Photos: one centered Click to Enlarge / Tap to Enlarge caption without arrows; no caption over an already enlarged photo.

Diploma: enlarge.

Workstation: all activity notes and their message handshake removed. Legacy activity-desktop review URL is a cue-free mobile desktop alias.

Mouse labels use Click/Hover/Scroll; coarse-pointer devices use Tap/Swipe. Per final approval, next-page swipe points right; previous-page swipe points left. Gesture behavior is unchanged. Desktop page arrows aim at the lower turning corners.

Existing controls remain available for accessibility and review; redundant-control removal is not bundled into this staging change.

## Verification

Focused cue, integration, Manic, mobile layout, book motion, playback and photo tests pass. Build succeeds. TypeScript still reports the two pre-existing VinylPortfolio Vector2 errors at lines 344 and 383; no new errors introduced.

Captured previews are under `docs/previews/activity-*.png` for remote review.
