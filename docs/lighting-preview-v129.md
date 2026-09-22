# Lamp lighting study — v129

Preview scene: `blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v129-lamp-lighting-preview.blend`.

Built from v127, not the older v121 scene left open in Blender. No website footage is replaced by this study.

- New tall lamp in the window-side corner, viewer-left of the main bookshelf. Reuses the desktop lamp's polygonal shade, base, stem, and matching outline geometry, with a taller stem.
- Desk plant moves to the old lamp position; desk lamp and its outlines move to the old plant position.
- Both shades are open at their top and bottom. Four soft spotlights illuminate upward/downward; there are no opaque beam meshes. Downlights are slightly offset within the shade footprint to avoid being blocked by the lamp stems.
- Indoor flat gray fills retain a reduced self-lit base (55% of previous strength) and receive diffuse light. Exterior, amber cue materials, and lightning animation remain separate.
- Legacy weather lights retain their timing and volume illumination, with diffuse influence reduced to 1.5% to avoid overexposing the newly light-reactive floor and furniture during lightning.
- Normal outlines briefly flash as logical groups, using baked keys over a 240-frame cycle. No script auto-execution is needed. Roughly quarter-second events replace the slow spatial white sweeps.
- Existing geometry, cameras, vinyl labels, and website transitions are preserved in the source version. Approach-only amber fade drivers are disabled in this idle study so camera-pan timing cannot extinguish cues while the home camera is stationary.

Rebuild using `preview_lamps_v129.py` with v127 loaded in background Blender. It refuses to overwrite the preview unless `--refine-own-preview` is supplied explicitly. Render the saved study with `render_lighting_v129.py`.

Before replacing website footage, review brightness, lamp position, and flash rhythm. Then rerender transitions and regenerate the cursor-outline mask to include the moved plant/lamp and new floor lamp.

`lighting-preview.mp4` is a ten-second 1080p, 12 fps lighting study (every other frame of the 24 fps scene). Final website footage should retain 24 fps and higher render samples. The still `greeting.png` uses 32 samples. `verification.json` checks the floor lamp/bookshelf clearance and four soft lights; `animation-audit.json` records flash strengths and retained weather lightning across the sampled loop.
