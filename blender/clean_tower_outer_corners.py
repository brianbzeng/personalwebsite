"""Build non-destructive tower corner guides from coplanar flange envelopes."""
import json
import sys
from pathlib import Path
sys.path.insert(0, 'C:/Users/BrianZ~1/AppData/Local/Temp/codex-bridge-geometry')
from shapely.geometry import Polygon, LineString
from shapely import union_all

root = Path(__file__).parent / 'outputs'
data = json.loads((root / 'bridge-v103-tower-faces.json').read_text())
result = {}
for key, faces in data.items():
    shape = union_all([Polygon(f).buffer(0) for f in faces], grid_size=.005)
    shape = shape.buffer(.025, join_style=2).buffer(-.025, join_style=2)
    profiles = [[], []]
    for step in range(549):
        y = -301.5 + step * .5
        cut = shape.intersection(LineString([(40,y),(124,y)]))
        if cut.is_empty:
            continue
        xmin, _, xmax, _ = cut.bounds
        profiles[0].append([xmin,y])
        profiles[1].append([xmax,y])
    result[key] = [list(LineString(p).simplify(.045).coords) for p in profiles]
    print(key, 'parts', len(getattr(shape,'geoms',[shape])), 'corners', [len(p) for p in result[key]], 'bounds',shape.bounds)
(root / 'bridge-v103-tower-corners.json').write_text(json.dumps(result))
