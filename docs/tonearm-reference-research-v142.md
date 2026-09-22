# Pivot and arm-rest reconstruction — v142

Subsequent user-directed simplification in v143: the rear lift shoe and left/right side caps, screws and slots are hidden, not deleted. The tiered base, yoke, shaft housing/collar and rest clamp remain. This intentionally simplifies the researched reference. See `blender/simplify_pivot_fade_v143.py` and `blender/outputs/review-v143/cleanup-audit.json`.

## Evidence and limits

Brian's close-ups are the primary visual reference. The overall J-arm and base are consistent with the Audio-Technica AT-LP70X family; the photos alone do not establish its exact Bluetooth/color variant.

Official sources checked:

- [AT-LP70X user manual](https://docs.audio-technica.com/all/AT-LP70X-UM-EN.pdf), printed page 8 (tonearm assembly), page 12 (rest clamp and setup), pages 31–33 (overall dimensions/specifications).
- [Official labeled tonearm diagram](https://www.audio-technica.co.jp/document/AT-LP70X/en/Content/Turntable/AT-LP70X/part-names/names-tonearm.html). This distinguishes the lift-control lever, rear tonearm lift, and forward rest with clamp.
- [Official manual operation instructions](https://www.audio-technica.co.jp/document/AT-LP70X/en/Content/Turntable/AT-LP70X/using/wired-manual-operation.html) distinguish raising, moving and slowly lowering the arm.
- [Official parts listing](https://www.audio-technica.co.jp/support/parts/search/result/AT-LP70X) was checked for component information; it did not provide a dimensioned pivot assembly drawing.

No public dimensioned pivot blueprint or exploded service drawing was found in this search. The manual supplies 220 mm effective arm length and 400 × 330 × 110 mm overall dimensions, not individual bearing measurements. This is a visual reconstruction fitted to the existing scene, not a manufacturing model or repair guide. All local part dimensions are inferred from the photographs.

## Visible-part analysis and assembly

1. Thin silver outer mounting flange, black lower skirt, middle and upper concentric terraces, smaller raised bearing drum. Every tier touches the preceding tier. Radius decreases as height increases; narrow parting seams and interrupted molded pads articulate the steps.
2. Outer solid U-shaped yoke with rounded corners, separate inset tilting bearing body and side bearing caps/screw heads. The shaft enters a bore in the inner body. The outer assembly follows yaw; the inner socket follows the existing small shaft pitch.
3. Tapered dark shaft socket, narrow silver front collar and retained slim rear shaft extension. These are separate parts, not an oversized counterweight.
4. A low curved lift shoe beneath the rear shaft. The crossed-out hand-operated cue lever is deliberately omitted.
5. Forward rest: light-gray cylindrical mounting socket with dark slot, short black stem, thick curved saddle, tall back cheek, separate open retaining clamp, thumb tab and hinge cap. The clamp remains open/unlatched so playback requires no extra unlocking animation. The low exit lip faces the arm's swing direction.

## Files and approval boundary

Latest review source: `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v142-detailed-pivot-rest.blend`.

`detail_pivot_rest_v142.py` creates it from v141, preserving earlier objects hidden in the version and retaining the previous file. `finish_rest_v142.py` records the socket-height refinement already incorporated in the creation script. The existing exporter updates only the separate `/review/player-books` assets. `review_tonearm_v140.py` generates close-up diagnostic stills from v142 without saving scene changes.

The J arm, hair-fine needle, half-height plinth, record flight and frame-122 needle cue remain unchanged. No book changes, production re-recording or deployment. Approval is still pending.

Validation: six targeted exported-asset tests pass, including contiguous decreasing-radius tiers and separate clamp/bearing pieces. Browser playback completes and Reset returns to frame 1. `pnpm build` passes. Inspected pivot, unoccupied-rest and raised-arm close-ups; the rest's low exit lip is on the swing side. Existing main-room media remains v137. Review JSON is about 5.9 MB uncompressed; production asset optimization remains part of post-approval integration.
