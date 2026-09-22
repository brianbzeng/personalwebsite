"""Read-only analysis of actual cable face planes; no scene meshes are merged."""
import json
import sys
from pathlib import Path
sys.path.insert(0, 'C:/Users/BrianZ~1/AppData/Local/Temp/codex-bridge-geometry')
from shapely.geometry import Polygon, LineString
from shapely import union_all

root = Path(__file__).parent / 'outputs'
raw = json.loads((root / 'bridge-audit-planes.json').read_text())
result = []
for x, coords in sorted(raw.items(), key=lambda kv: float(kv[0])):
    polygons = [Polygon(c) for c in coords]
    polygons = [p for p in polygons if p.is_valid and p.area > 0.00001]
    if sum(p.area for p in polygons) < 1000:
        continue
    shape = union_all(polygons, grid_size=0.01)
    parts = list(shape.geoms) if hasattr(shape, 'geoms') else [shape]
    cut = shape.intersection(LineString([(750, -325), (750, -123)]))
    print(x, 'area', round(shape.area), 'parts', len(parts), 'holes', sum(len(p.interiors) for p in parts if p.geom_type == 'Polygon'), 'cut', str(cut))
    shape = shape.buffer(0.035, join_style='mitre').buffer(-0.035, join_style='mitre')
    parts = list(shape.geoms) if hasattr(shape, 'geoms') else [shape]
    loops = []
    for p in parts:
        if p.geom_type != 'Polygon' or p.area < 1:
            continue
        loops.append(list(p.exterior.simplify(0.015).coords))
        loops.extend(list(r.simplify(0.015).coords) for r in p.interiors if Polygon(r).area > 1)
    result.append({'x': float(x), 'loops': loops})
(root / 'bridge-audit-plane-contours.json').write_text(json.dumps(result))
