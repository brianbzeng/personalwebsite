"""Union projected cable surfaces so imported part seams are not outlined."""
import sys
import json
from pathlib import Path
sys.path.insert(0, 'C:/Users/BrianZ~1/AppData/Local/Temp/codex-bridge-geometry')
from shapely.geometry import Polygon
from shapely import union_all

root = Path(__file__).parent / 'outputs'
raw = json.loads((root / 'bridge-side-projection.json').read_text())
polygons = [Polygon(p) for p in raw]
polygons = [p for p in polygons if p.area > 0.00001 and p.is_valid]
shape = union_all(polygons, grid_size=0.01)
# Close subpixel cracks between touching pieces without rounding cable corners.
shape = shape.buffer(0.08, join_style='mitre').buffer(-0.08, join_style='mitre')
parts = list(shape.geoms) if hasattr(shape, 'geoms') else [shape]
loops = []
for part in parts:
    if part.area < 1:
        continue
    loops.append(list(part.exterior.simplify(0.03).coords))
    loops.extend(list(r.simplify(0.03).coords) for r in part.interiors if Polygon(r).area > 1)
(root / 'bridge-side-contours.json').write_text(json.dumps(loops))
print({'parts': len(parts), 'contours': len(loops), 'points': sum(map(len, loops)), 'bounds': shape.bounds})
