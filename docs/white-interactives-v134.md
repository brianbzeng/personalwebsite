# White interactive highlights

The monitor's inner and outer borders, vinyl rack cue, and diploma frame share `INTERACT_SharedAmberRhythm_v119`. Its historical name is retained for compatibility; the live emission color is now neutral white `(1, 1, 1, 1)` rather than amber `(1, .38, .065, 1)`.

The pulse driver remains `0.8+0.6*sin(2*pi*(frame-1)/120)`, with emission strength ranging from 0.2 to 1.4 and a five-second cycle at 24 fps. All four target materials still use their existing black selection branches. The room's traveling highlights, pointer-follow mask, lamp illumination, camera paths and geometry are unchanged.

`blender/white_interactives_v134.py` starts from the saved v133 scene, asserts that the shared shader has only the four intended material users, verifies white color throughout 241 frames, checks pulse bounds/loop closure, and verifies original object transforms. It saves `lofi-room-cathode-glm53f-city-v134-white-interactives.blend`; earlier versions remain available.

The room media must be refreshed together: idle, incoming/outgoing monitor, vinyl and diploma clips, plus greeting and close-up stills. The existing v132 pointer mask remains valid because the geometry and greeting camera are unchanged.

## Local preview verification

All seven movies and four stills are now served from `/room/v134/`, including both shelf fallback images. Movies remain 1920×1080 at 24 fps: a ten-second idle loop, 121-frame monitor clips, and 73-frame vinyl/diploma clips. Every asset is below the existing 6 MB budget; idle is 1,207,534 bytes. Matching room and project-control accents are neutral white.

The shared shader audit passed across 241 frames, and full-resolution bright/dim and close-up renders were inspected. `node --test tests/*.test.mjs` passes all 111 tests; `pnpm build` succeeds with the existing large lazy-chunk warning. Browser checks verified all six new transition URLs, loaded close-up stills, monitor entry and terminal `exit`, and return to the greeting view from all three destinations. Reduced-motion checks verified static white artwork and direct destination access without transition movies.

Only the local preview was updated. Earlier Blender versions and media remain intact; the user's unsaved Blender GUI scene was not replaced.
