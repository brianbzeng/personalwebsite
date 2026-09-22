# Desktop icon sources

All four PNG files have actual alpha transparency. The desktop renders them in grayscale using CSS; SVG viewBoxes remove empty padding at display time to give the artwork a consistent maximum dimension without stretching the original images.

- `terminal.png`: unchanged user-supplied Windows Terminal icon, 256 × 256.
- `recycle-bin.png`: unchanged user-supplied Windows Recycle Bin icon, 250 × 250.
- `mail.png`: Microsoft Mail app icon, 64 × 64, from [Wikipedia's file record](https://en.wikipedia.org/wiki/File:Microsoft_Mail_app_Icon.png), [original PNG](https://upload.wikimedia.org/wikipedia/en/9/9d/Microsoft_Mail_app_Icon.png). Windows app artwork by Microsoft. Replaces the supplied white-background reference with the existing transparent app asset. Its file record documents the source and reuse rationale; Microsoft retains ownership of its icon.
- `user.png`: transparent cutout of the supplied profile silhouette, 1254 × 1254. Created with the built-in imagegen tool. The desktop displays the silhouette in light gray via CSS so it remains visible on the dark wallpaper.

## Profile cutout prompt

Use case: background-extraction
Asset type: website icon, transparent PNG cutout
Input image 1: exact edit target, existing black user/profile silhouette consisting of a circular head and a separate rounded torso.
Primary request: Remove all white background, including the white gap between head and torso, and replace it with actual transparent alpha. Preserve every black part of the original silhouette exactly.
Constraints: Same image, no redraw. Keep the black circle and torso exact original geometry, positions, dimensions, proportions, edge contours, solid black color and internal appearance unchanged. Do not recolor, restyle, add objects, add shadow, or alter composition. Only remove white background pixels; preserve crisp antialiased icon edges without white halos.
Output: RGBA PNG with a genuinely transparent background everywhere outside the two black shapes, not a rendered checkerboard and not a white background. Keep canvas framing matching the source.

Validation: profile output has transparent exterior and head/torso gap; the generated edge pixels and framing are not pixel-identical to the source. The generated mail candidate had a baked-in checkerboard and was rejected; it is not included in this project.
