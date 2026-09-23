"""Brighten the pitch-black record baked into the shelf plates.

The idle shelf composites the photographic plate; the 3D player only renders
in the playback close-up. The plates (v155/v156 vinyl-background/still) bake
the playback record at ~(0-7) with groove rings down to ~(1), which reads as a
black hole at shelf distance. This lifts the disc region toward the tonality
of the live playback shot (grays 40-65) with a smooth radial falloff, leaving
the platter base and everything outside the disc untouched.

Disc centers are measured per plate (darkest radial center of the record):
  v156 background/still: (350, 772), v155 background/still: (354, 758),
record radius ~100 px on the 1920x1080 plates.

Usage: python blender/brighten_plate_disc_v157.py
"""
from PIL import Image, ImageDraw
import math
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
PLATES = {
    "public/room/v156/vinyl-background.webp": (350, 772),
    "public/room/v156/vinyl-still.webp": (350, 772),
    "public/room/v155/vinyl-background.webp": (354, 758),
    "public/room/v155/vinyl-still.webp": (354, 758),
}
RADIUS = 100   # record edge; cosine fade reaches zero here
LIFT = 40      # added at the disc center


def brighten(path, cx, cy):
    image = Image.open(path).convert("RGB")
    w, h = image.size
    # Soft mask: 1 at center, cosine fade to 0 at the rim, untouched outside.
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    for r in range(RADIUS, 0, -1):
        strength = int(255 * (0.5 + 0.5 * math.cos(math.pi * r / RADIUS)))
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=strength)
    pixels = image.load()
    mask_data = mask.load()
    for x in range(max(0, cx - RADIUS), min(w, cx + RADIUS)):
        for y in range(max(0, cy - RADIUS), min(h, cy + RADIUS)):
            m = mask_data[x, y] / 255
            if m <= 0:
                continue
            r, g, b = pixels[x, y]
            pixels[x, y] = (min(255, int(r + LIFT * m)), min(255, int(g + LIFT * m)), min(255, int(b + LIFT * m)))
    center_before = image.getpixel((cx, cy))
    image.save(path, "WEBP", quality=100, method=6)
    print(f"{path}: disc at ({cx},{cy}) r={RADIUS}, center {center_before} -> {pixels[cx, cy]}")


for plate, center in PLATES.items():
    brighten(os.path.join(ROOT, plate), *center)
