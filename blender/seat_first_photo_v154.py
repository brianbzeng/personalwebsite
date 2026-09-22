"""Seat only the left photo on C, preserving its XY placement and all other cards."""
import bpy, json, math, os, runpy
from mathutils import Matrix, Vector

root = os.path.dirname(os.path.abspath(__file__))
project = os.path.dirname(root)
assert bpy.data.filepath.endswith('v153-smooth-photo-camera.blend')
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
pivot = Vector((2.465, 1.52, .978))
# Triangle-overlap contact solve includes both cards' outlined geometry.
# D clears C by .00015 and the shelf by .000224; no intersecting borders.
transform = (Matrix.Translation((0, 0, -.01100466)) @ Matrix.Translation(pivot)
             @ Matrix.Rotation(math.radians(-4.5), 4, 'X') @ Matrix.Translation(-pivot))
members = [o for o in bpy.context.scene.objects if 'SHELF_Polaroid_D_' in o.name]
assert len(members) == 4
for obj in members:
    obj.matrix_world = transform @ obj.matrix_world
bpy.context.view_layer.update()
with open(os.path.join(project, 'public/review/v138/photos.json')) as handle:
    model = json.load(handle)
for mesh in model['meshes']:
    if 'SHELF_Polaroid_D_' in mesh['name']:
        values = mesh['positions']
        mesh['positions'] = [component for i in range(0, len(values), 3)
                             for component in transform @ Vector(values[i:i+3])]
card = bpy.data.objects['SHELF_Polaroid_D_Card']
q = card.matrix_world.to_quaternion()
model['shelfPoses'] = {'D': {'center': list(card.matrix_world.translation),
                           'quaternion': [q.x, q.y, q.z, q.w]}}
destination = os.path.join(project, 'public/review/v154')
os.makedirs(destination, exist_ok=True)
with open(os.path.join(destination, 'photos.json'), 'w') as handle:
    json.dump(model, handle, separators=(',', ':'))
runpy.run_path(os.path.join(root, 'smooth_photos_v153.py'), init_globals={
    'SOURCE_TAG': 'v153-smooth-photo-camera',
    'TARGET_TAG': 'v154-seated-first-photo', 'OUTPUT_VERSION': 154})
