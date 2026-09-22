# Rounded monitor approach

The v133 monitor path replaces the earlier rightward waypoint with two straight runs connected by a tangent quadratic bend. Its plan-view virtual corner is `(0, -4.2)`, on the monitor centerline. The curve remains at `x <= 0`, so the camera never crosses to the right and then corrects left.

- Greeting position and rotation are retained from `CAM_APPROVED_GREETING_Restored_v119`.
- Height decreases continuously with traveled distance, from `9.207818` to `1.40280008`; the final straight is still descending, as requested.
- An arc-length lookup gives continuous travel speed across the straight/bend joins. One overall smoothstep eases departure and arrival.
- The endpoint remains `(0, 2.15, 1.40280008)`, with the existing screen target, 50 mm lens, and full-screen handoff.
- The return uses the same camera poses in reverse while the ambient animation continues normally.

Only the new camera is added to the v132 scene. Preparation asserts every original object transform is unchanged, checks the endpoints, and samples 1,001 positions for monotonic descent and no rightward overshoot. Its report and framing probes are in `blender/outputs/web-room-v133`.

The saved scene is `lofi-room-cathode-glm53f-city-v133-rounded-monitor-pan.blend`. Only the two monitor clips are re-rendered at 1920 × 1080, 24 fps, 121 frames each. The greeting, idle loop, lighting, room objects, vinyl clips, and diploma clips remain v132. Earlier scenes and media remain available.

## Verification

- 106 Node tests pass; production build passes (existing large lazy-chunk warning remains).
- Browser confirmed both v133 clips decode at 1920 × 1080 and 5.041667 seconds. Approach reaches the live desktop; terminal `exit` plays the new return and restores the room.
- Reduced motion skips both clips and still supports entering/exiting the desktop.
- Approach first frame and return last frame each have SSIM 0.999998 against the existing greeting render, retaining its framing and lighting at the join.
- Approach: 3,099,635 bytes; return: 3,150,715 bytes. Unchanged room assets are reused rather than copied.
- Verified locally only; no deployment or push.
