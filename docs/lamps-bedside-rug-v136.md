# Translucent lamps and bedside rug

The v135 lamp preparation starts from v134's white-interactive scene. It copies materials onto only the desk and floor lampshades: 12% transparent shader, 30% translucent fabric in the remaining surface, and a restrained warm center-to-rim glow. Small soft internal lights (3 W desk, 4 W floor) provide actual backlighting; original top/bottom spotlights remain unchanged. Separate shade outlines retain their existing materials.

The v136 scene retains that lighting and moves/reshapes the existing center rug into a 2.15 × 3.10 m rectangle beneath the bed, extending along its exposed side and foot. The rug and its outline move together. The rug's world-space traveling-light bounds are refitted, while cameras and all other object transforms remain unchanged. Previous scenes preserve the original rug.

Full-resolution greeting, dim-phase and lightning-phase probes were inspected before media rendering. Both preparation scripts assert preservation of their unrelated scene properties. A new cursor-outline mask is rendered for v136 so the old center rug does not leave an invisible hover outline.

Combined source: `lofi-room-cathode-glm53f-city-v136-lamps-bedside-rug.blend`. Local media refresh is generated as `/room/v136/`; no public deployment is requested.

## Verification

All seven 1080p/24 fps movies, four stills, and the new pointer mask are integrated. All movies decode without errors and stay below the existing 6 MB individual limit. The idle loop is 1,215,822 bytes; the pointer mask is 123,342 bytes. Its white RGB uses a compact 16-level alpha coverage channel.

All 115 automated tests pass and the production build succeeds with the existing lazy-chunk size warning. Browser verification after refreshing the local development server confirms v136 idle and pointer-mask URLs, all six camera-transition URLs, loaded vinyl/diploma stills, terminal `exit` returning to the room, and the v136 reduced-motion greeting still. The top-right menu placement is preserved.

The previous scene versions remain recoverable. No public deployment or replacement of the user's unsaved Blender GUI scene was performed.
