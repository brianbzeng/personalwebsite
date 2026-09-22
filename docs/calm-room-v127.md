# Calmer room and monitor approach — v127

Local-only revision based on the saved v126 project-vinyl scene. Earlier Blender versions and the user's open Blender scene are preserved.

## Visual changes

- The monitor approach is 121 frames at 24 fps (about five seconds). It dives toward room coordinate `(1.35, -1.6, 2.85)`, then follows a straight descending segment to the existing screen endpoint. It has no separate sideways window-look excursion.
- The return follows the same camera route in reverse. Both room endpoints exactly match the approved centered greeting camera.
- Traveling white outline gain is reduced from 4.6 to 0.52, with one sweep per 240 frames instead of two. Ordinary room wireframe modifiers are 60% of their former width. Hand-cleaned bridge contours, physical vinyl edges, and amber interactable outline widths are preserved.
- The idle export now includes all 240 frames. The existing lightning action peaks at frame 128, beyond the previous 120-frame export. Its authored flicker and window/floor projections are retained.
- A 48 KB floor visibility mask enables a cursor-following CSS glow. It is generated with furniture as occluders, so the effect only reaches exposed grid lines. It fades after movement stops, ignores touch input, and is absent while motion is paused, the page is hidden, or reduced motion is preferred. No additional 3D runtime is loaded for this effect.

## Reference boundary

The public [ThreeUI Workstation preview](https://threeui.com/hero/cathode-page/workstation) was inspected at multiple points in its ten-second video. It supports the finer/dimmer outline direction. Its live renderer and controls are Pro-gated; no access controls were bypassed. Cursor interaction was implemented from Brian's description, not claimed as independently tested on the gated reference.

## Verification

- Production build passes; 95 automated tests pass.
- Blender camera audit: exact start, screen endpoint and return; maximum deviation from the final straight segment is below `0.000001` scene units.
- Authored lightning values verified at frames 127–133; full-HD browser idle video is ten seconds and shows the flash at approximately 5.29 seconds.
- Browser checks confirm floor glow follows the cursor, fades to zero, and is removed for paused/reduced-motion modes.
- Monitor approach reaches the live desktop. With the return download delayed 650 ms, the desktop stays mounted and the transition remains hidden until a decoded frame is ready; the five-second return then reaches the room.
- Targeted lint still reports two existing `CinematicRoom` findings (the boot effect's state change and the no-JavaScript fallback's ordinary projects link); neither was introduced by this revision.
- All seven final clips verify as 1920×1080: idle 240 frames, monitor directions 121 each, vinyl/diploma directions 73 each. All are below 3.3 MB individually. Final 95-test run passes against the replacement media. Vinyl and diploma browser round-trips pass with v127 plates.

Reproduction: load v126 in background Blender with `blender/render_calm_room_v127.py`, then run `blender/encode_calm_room_v127.ps1`. The script saves v127 only if it does not already exist and resumes completed PNG frames. Run `blender/audit_calm_room_v127.py` against v127 for the numerical camera/lightning audit.
