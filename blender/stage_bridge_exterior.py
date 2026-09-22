"""Stage exterior contour curves. Original imported objects stay untouched."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

root = Path(bpy.data.filepath).parents[2]
loops_by_side = json.loads((root / 'bridge-audit-exterior-loops.json').read_text())
bvh = bpy.app.driver_namespace['audit_bvh']
collection = bpy.data.collections.get('BRIDGE_V102_Individual_Cable_Outlines')
if collection is None:
    collection = bpy.data.collections.new('BRIDGE_V102_Individual_Cable_Outlines')
    bpy.context.scene.collection.children.link(collection)
matrix = bpy.data.objects['Object_2'].matrix_world.copy()
mat = bpy.data.materials['BRIDGE_AUDIT_White_Diagnostic']
stats = {}
for side, loops in loops_by_side.items():
    # Each side is derived independently, never mirrored or nearest-point snapped.
    for face in ('outer', 'inner'):
        increasing = (side == 'R') == (face == 'outer')
        origin_x = (110 if side == 'R' else 75) if increasing else (90 if side == 'R' else 55)
        direction = Vector((-1 if increasing else 1, 0, 0))
        curves = {}
        misses = 0
        count = 0
        for loop_index, loop in enumerate(loops):
            run = []
            broken = False
            for a, b in zip(loop, loop[1:]):
                za, ya = a
                zb, yb = b
                length = math.hypot(zb-za, yb-ya)
                if length < .0001:
                    continue
                if abs(ya+123) < .03 and abs(yb+123) < .03:
                    if len(run) > 1:
                        curves.setdefault(loop_index, []).append(run)
                    run = []
                    broken = True
                    continue
                nz, ny = -(yb-ya)/length, (zb-za)/length
                for j in range(max(1, math.ceil(length / .3))):
                    t = j / max(1, math.ceil(length / .3))
                    z, y = za+(zb-za)*t, ya+(yb-ya)*t
                    hit = None
                    for inset in (.04, .1, .2, .4):
                        loc, normal, index, distance = bvh.ray_cast(Vector((origin_x, y+ny*inset, z+nz*inset)), direction, 20)
                        if loc is not None:
                            hit = (loc.x + (.13 if increasing else -.13), y, z, 1)
                            break
                    if hit is None:
                        misses += 1
                        broken = True
                        if len(run) > 1:
                            curves.setdefault(loop_index, []).append(run)
                        run = []
                    else:
                        if run and abs(run[-1][0]-hit[0]) > 1.5:
                            if len(run)>1:
                                curves.setdefault(loop_index,[]).append(run)
                            run=[]
                            broken=True
                        run.append(hit)
                        count += 1
            if len(run) > 1:
                if not broken:
                    run.append(run[0])
                curves.setdefault(loop_index, []).append(run)
        groups = {}
        def owner(a, b):
            z = (a[2]+b[2])/2
            y = (a[1]+b[1])/2
            center = round((z-7)/20)*20+7
            if abs(a[2]-b[2]) < .08 and abs(z-center) < 2.7 and y < -142:
                if min(abs(center-t) for t in (487,1187,1887,2587)) > 10:
                    return f'Suspender_{center:04d}'
            if y < -150 and min(abs(z-t) for t in (487,1187,1887,2587)) > 12:
                span = sum(z > t for t in (487,1187,1887,2587))
                return f'MainCable_Span_{span+1}'
            return 'Attachment_and_Deck_Boundaries'
        for runs in curves.values():
            for points in runs:
                key = None
                chunk = []
                for a,b in zip(points,points[1:]):
                    newkey = owner(a,b)
                    if newkey != key:
                        if len(chunk)>1:
                            groups.setdefault(key,[]).append(chunk)
                        chunk = [a]
                        key = newkey
                    chunk.append(b)
                if len(chunk)>1:
                    groups.setdefault(key,[]).append(chunk)
        for name, runs in groups.items():
            data = bpy.data.curves.new(f'V102_{side}_{face}_{name}', 'CURVE')
            data.dimensions = '3D'
            data.bevel_depth = .34
            data.bevel_resolution = 2
            for points in runs:
                spline = data.splines.new('POLY')
                spline.points.add(len(points)-1)
                for p, co in zip(spline.points, points):
                    p.co = co
            object_name = f'V102_{side}_{face}_{name}'
            obj = collection.objects.get(object_name)
            if obj is None:
                obj = bpy.data.objects.new(object_name, data)
                collection.objects.link(obj)
            else:
                obj.data = data
            obj.matrix_world = matrix.copy()
            data.materials.append(mat)
            obj['physical_cable_id'] = f'{side}_{name}'
            obj['method'] = 'Independent side silhouette; first exterior ray hit; no mirrored or nearest-surface contours'
            obj['audit_status'] = 'Pending visual acceptance'
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D' and area.spaces.active.local_view:
                    obj.local_view_set(area.spaces.active, True)
        stats[f'{side}_{face}'] = {'points': count, 'misses': misses, 'groups':len(groups)}
print(stats)
