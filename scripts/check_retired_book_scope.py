"""Read-only verification: greeting correction is confined to the retired book."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1] / 'blender/outputs'
outside = np.ones((1080, 1920), dtype=bool)
outside[280:340, 1035:1100] = False
results = []
for frame in (0, 48, 96, 120, 192, 239):
    relative = f'idle/{frame:04d}.png'
    before, after = root/'web-room-v161'/relative, root/'web-room-v162'/relative
    if not after.exists():
        continue
    a = np.asarray(Image.open(before).convert('RGB')).astype(int)
    b = np.asarray(Image.open(after).convert('RGB')).astype(int)
    delta = np.max(np.abs(a-b), axis=2)
    maximum = int(delta[outside].max())
    changed = np.argwhere(delta > 3)
    results.append({'frame':frame,'outsideBookMaximumDelta':maximum,
        'changedBoundsYX':[changed.min(axis=0).tolist(),changed.max(axis=0).tolist()] if changed.size else None})
    assert maximum <= 3, f'Unexpected change outside book: {frame}: {maximum}'
print(json.dumps(results, indent=2))
