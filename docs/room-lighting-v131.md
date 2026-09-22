# Traveling highlights — v131

Based on the approved v130 scene. No geometry, cameras, soft lamps, room brightness, amber interaction cues, or lightning timing are changed.

## Motion

Each random-looking staggered trigger starts a four-second traveling contour highlight instead of the previous quarter-second whole-object flash. At 24 fps, the spatial front takes approximately 2.19 seconds to cross an object's full extent. Each point brightens over 0.35 seconds and fades over 1.31 seconds; the remaining event time carries the leading/trailing edges outside the model. The peak remains 0.65, with black outlines at rest.

All constituent meshes share one world-space projection and material per logical model. No meshes are joined. Bounds come from evaluated geometry in render-enabled collections, excluding archived source models that would otherwise distort the sweep distance. In particular, old hidden V41 bridge geometry is excluded; the fitted bridge's sweep follows its roughly 55-unit longitudinal extent.

The ten-second loop uses deterministic staggered starts and periodic shader phase. An active pass is not retriggered before its tail finishes. Sweeps crossing the loop boundary remain continuous.

The visible portions of the public [Three UI Cathode Workstation preview](https://threeui.com/hero/cathode-page/workstation) show moving localized highlights over dim outlines. The Pro overlay obscures much of the scene and the live renderer is gated. The timing above is an interpretation of Brian's request, not recovered Three UI settings.

## Delivery

Scene: `lofi-room-cathode-glm53f-city-v131-traveling-pulses.blend`.

Render with `render_room_v130.py -- --v131`, then `encode_room_v130.ps1 -Revision 131`. This reuses the verified camera/world-clock handling and full 1080p/24 fps settings. Output is staged under `public/room/v131` until all seven movies and four plates are complete. The v130 cursor mask is intentionally retained because geometry and framing did not change.

Previous scene versions and media remain available. Work stays local.

All seven movies and four plates are complete and integrated into the local preview. The idle loop is 1.21 MB at 1920×1080/24 fps; its greeting image is 84 KB. Every individual movie remains below the existing 6 MB release budget.

## Checks

`audit_pulses_v131.py` evaluates the actual Blender shader graph and cyclic animation curve at points across each of the 24 models. All locations receive full illumination, a sustained fade, and an ordered traveling peak. It also compares vertex hashes, topology counts, object/camera matrices, and lamp settings with v130; all are unchanged. There are 658 participating visible outline components. The regression suite covers the same timing and seam conditions independently.

Final verification: 101 tests pass and `pnpm build` completes (existing large lazy-loaded chunk warning remains). All seven movies decode without errors and report 1080p, 24 fps, and the expected frame counts. The raw vinyl arrival frame and close-up plate are identical (SSIM 1.0). Browser checks reached all three destinations and returned successfully using v131 media, with no exposed room layer in the sampled return states; reduced-motion mode omits idle and transition videos. The preview was left on the animated greeting view. No deployment was performed.
