# Scene transitions — staging

Review route: `/review/responsive`.

Clicking a room scene still plays the approved camera clip. The clip is buffered before the click, and the destination (shelf, desktop, or diploma) starts loading once the movie is on screen, so the landing cut does not sit on a frozen frame. Shelf cubby moves and the return to the room are buffered the same way.

Portrait phones on this route keep one shared 16:9 frame for the room, the camera move, the handoff still, and the landing scene. Scene shortcuts sit in the space under that frame. The approved landscape cover framing is unchanged.

## Accelerated camera moves

Review route: `/review/scene-motion`. Home uses the same curve (`fastTransitions`), approved 2026-09-22.

The approved clips play unchanged, but their playback rate follows an acceleration curve (`sceneMotion.ts`): the move launches at 1.5×, accelerates to 3.2× at the midpoint, and eases back to 1.6× for the landing cut. Room moves finish in about half the rendered time (monitor approach ≈2.5 s instead of 5 s, shelf/diploma approaches ≈1.5 s instead of 3 s); shelf cubby moves use a gentler curve (≈1 s instead of 1.5 s). Hovering a hotspot also primes its clip so the first frame is decoded before the click.

Production home does not enable `responsiveLayout`. The shared preload and overlapped destination load do apply to every room, including home, because they do not change the approved framing.
