from pathlib import Path
import bpy, json

root = Path(__file__).resolve().parent
src = root / 'outputs' / 'blender' / 'lofi-room-cathode-v121-outside-short-interactive-rays.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))

keys = ('SHELF_Camera', 'BED_', 'Mouse', 'MOUSE', 'mouse', 'Mug', 'MUG', 'mug')
items = []
for ob in bpy.data.objects:
    if any(k in ob.name for k in keys):
        dims = tuple(round(v, 5) for v in ob.dimensions)
        loc = tuple(round(v, 5) for v in ob.location)
        entry = {'name': ob.name, 'type': ob.type, 'loc': loc, 'dims': dims, 'parent': ob.parent.name if ob.parent else None}
        if ob.type == 'MESH':
            entry.update({'verts': len(ob.data.vertices), 'edges': len(ob.data.edges), 'faces': len(ob.data.polygons)})
        items.append(entry)

print('TARGETS=' + json.dumps(items, indent=2))

for name in ('BED_Blanket_FacetedContinuous', 'BED_Mattress', 'CATHODE_WIREFRAME_BED_Blanket_FacetedContinuous'):
    ob = bpy.data.objects.get(name)
    if ob and ob.type == 'MESH':
        coords = [ob.matrix_world @ v.co for v in ob.data.vertices]
        print(name, 'BOUNDS', tuple(round(x, 5) for x in (
            min(v.x for v in coords), max(v.x for v in coords), min(v.y for v in coords), max(v.y for v in coords), min(v.z for v in coords), max(v.z for v in coords))))
        if 'WIREFRAME' in name:
            print(name, 'OUTLIERS', [(v.index, tuple(round(c, 5) for c in (ob.matrix_world @ v.co))) for v in ob.data.vertices if abs((ob.matrix_world @ v.co).z) > 1.5])
