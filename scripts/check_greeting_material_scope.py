"""Read-only comparison of local uncompressed greeting render frames.

Requires Pillow and NumPy; raw authoring renders intentionally are not in Git.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1] / 'blender/outputs'
outside = np.ones((1080, 1920), dtype=bool)
outside[345:400, 1045:1110] = False
results = []
for frame in (0, 48, 96, 120, 192, 239):
    relative = f'idle/{frame:04d}.png'
    before, after = root / 'web-room-v149' / relative, root / 'web-room-v161' / relative
    if not after.exists():
        continue
    a = np.asarray(Image.open(before).convert('RGB')).astype(int)
    b = np.asarray(Image.open(after).convert('RGB')).astype(int)
    delta = np.max(np.abs(a-b), axis=2)
    maximum = int(delta[outside].max())
    results.append({'frame': frame, 'outsidePlayerMaximumDelta': maximum})
    assert maximum <= 3, f'Unexpected non-player change in frame {frame}: {maximum}'
print(json.dumps(results, indent=2))
