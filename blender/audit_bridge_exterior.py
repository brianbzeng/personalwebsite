"""Exterior-only silhouette analysis of separate cable assemblies."""
import json
import sys
from pathlib import Path
sys.path.insert(0, 'C:/Users/BrianZ~1/AppData/Local/Temp/codex-bridge-geometry')
from shapely import union_all
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

root = Path(__file__).parent / 'outputs'
raw = json.loads((root / 'bridge-audit-exterior.json').read_text())
result = {}
for side, faces in raw.items():
    polys = [Polygon(p) for p in faces]
    polys = [p for p in polys if p.is_valid and p.area > .000001]
    shape = union_all(polys, grid_size=.005)
    shape = shape.buffer(.025, join_style='mitre').buffer(-.025, join_style='mitre')
    parts = list(shape.geoms) if hasattr(shape, 'geoms') else [shape]
    loops = []
    for p in parts:
        if p.geom_type != 'Polygon' or p.area < 1:
            continue
        p = orient(p, sign=1)
        loops.append(list(p.exterior.simplify(.012).coords))
        loops.extend(list(r.simplify(.012).coords) for r in p.interiors if Polygon(r).area > 1)
    result[side] = loops
    print(side, len(loops), sum(map(len, loops)))
(root / 'bridge-audit-exterior-loops.json').write_text(json.dumps(result))
