"""Move the existing rug out of the center and reshape it beneath the bed."""
import bpy, os, json, sys
from mathutils import Vector
s = bpy.context.scene
root = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(root, 'outputs/web-room-v136'); os.makedirs(out, exist_ok=True)
target = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v136-lamps-bedside-rug.blend')
assert 'v135-translucent-lamps' in bpy.data.filepath
assert not os.path.exists(target) or '--refine-owned-preview' in sys.argv
s.frame_set(1)
names = ['RUG_Base', 'CATHODE_WIREFRAME_RUG_Base']
before = {o.name: tuple(v for row in o.matrix_world for v in row) for o in s.objects}
old = ((-1.62, .78), (-1.75, .65))
new = ((.50, 2.65), (-2.70, .40))
for name in names:
    obj = bpy.data.objects[name]
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        p = obj.matrix_world @ vertex.co
        for axis in (0, 1):
            p[axis] = new[axis][0] + (p[axis]-old[axis][0]) * (new[axis][1]-new[axis][0])/(old[axis][1]-old[axis][0])
        vertex.co = inverse @ p
    obj.data.update()
bpy.context.view_layer.update()
# Refit only the rug's world-space light sweep to its new rectangle.
outline = bpy.data.objects[names[1]]
mat = outline.material_slots[0].material.copy()
mat.name = 'CATHODE_V131_Travel_rug_Bedside_V136'
outline.material_slots[0].link = 'OBJECT'; outline.material_slots[0].material = mat
nodes = mat.node_tree.nodes
dot = next(n for n in nodes if n.type == 'VECT_MATH' and n.operation == 'DOT_PRODUCT')
offset = next(l.to_node for l in mat.node_tree.links if l.from_node == dot and l.to_node.type == 'MATH' and l.to_node.operation == 'SUBTRACT')
scale = next(l.to_node for l in mat.node_tree.links if l.from_node == offset and l.to_node.type == 'MATH' and l.to_node.operation == 'DIVIDE')
axis = Vector(dot.inputs[1].default_value)
points = [outline.matrix_world @ Vector(p) for p in outline.bound_box]
values = [p.dot(axis) for p in points]
offset.inputs[1].default_value = min(values)
scale.inputs[1].default_value = max(values)-min(values)
mat['bounds_min'] = min(values); mat['bounds_span'] = max(values)-min(values)
assert all(before[n] == tuple(v for row in bpy.data.objects[n].matrix_world for v in row) for n in before)
assert new[1][1]-new[1][0] > (new[0][1]-new[0][0])*1.4
s.camera = bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
bpy.ops.wm.save_as_mainfile(filepath=target)
with open(os.path.join(out, 'rug-audit.json'), 'w') as f:
    json.dump(dict(objects=names, oldXY=old, newXY=new, rugMeters=[2.15,3.10], originalObjectTransformsUnchanged=True, sweepBoundsUpdated=True), f, indent=2)
s.render.resolution_percentage = 100; s.eevee.taa_render_samples = 16
for frame in [1, 91, 128]:
    s.frame_set(frame); s.render.filepath = os.path.join(out, f'room-probe-{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
print('V136_RUG_PREPARED', flush=True)
