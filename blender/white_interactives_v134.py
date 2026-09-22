"""Restore white discoverability pulses, preserving v133 camera/scene/animation."""
import bpy, os, json, sys

s = bpy.context.scene
root = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(root, 'outputs/web-room-v134')
os.makedirs(out, exist_ok=True)
target = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v134-white-interactives.blend')
assert 'v133-rounded-monitor-pan' in bpy.data.filepath
assert not os.path.exists(target) or '--refine-owned-preview' in sys.argv
s.frame_set(1)
before = {o.name: tuple(v for row in o.matrix_world for v in row) for o in s.objects}
materials = [m for m in bpy.data.materials if m.use_nodes and m.node_tree.nodes.get('Selected target fades to black')]
assert len(materials) == 4
shared = bpy.data.node_groups['INTERACT_SharedAmberRhythm_v119']
users = [m.name for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type == 'GROUP' and n.node_tree == shared]
assert sorted(users) == sorted(m.name for m in materials)
# The old per-material emitters are disconnected. The shared group is the live
# branch feeding each selected-target mixer; leave legacy nodes untouched.
emitter = shared.nodes['Emission']
color = emitter.inputs['Color']
rgba = tuple(color.default_value)
assert not color.is_linked and rgba[0] > .9 and .3 < rgba[1] < .5 and rgba[2] < .1
drivers = [(f.data_path, f.array_index, f.driver.expression) for f in shared.animation_data.drivers]
color.default_value = (1, 1, 1, rgba[3])
changes = [dict(group=shared.name, before=rgba, after=list(color.default_value), users=users)]
strengths = []
for frame in range(1, 242):
    s.frame_set(frame)
    assert tuple(color.default_value) == (1, 1, 1, 1)
    strengths.append(emitter.inputs['Strength'].default_value)
assert abs(strengths[0]-strengths[-1]) < 1e-6
assert min(strengths) < .21 and max(strengths) > 1.39
assert drivers == [(f.data_path, f.array_index, f.driver.expression) for f in shared.animation_data.drivers]
s.frame_set(1)
assert before == {o.name: tuple(v for row in o.matrix_world for v in row) for o in s.objects}
# Retain material/object names: the renderer uses these identities for selecting
# the monitor, vinyls and diploma independently. Pulse drivers/links are intact.
home = bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
s.camera = home
bpy.ops.wm.save_as_mainfile(filepath=target)
with open(os.path.join(out, 'white-highlight-audit.json'), 'w') as f:
    json.dump(dict(changes=changes, transformsUnchanged=True, animationUnchanged=True, pulseMin=min(strengths), pulseMax=max(strengths), drivers=drivers), f, indent=2)
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.render.resolution_percentage = 50
s.render.image_settings.file_format = 'PNG'
s.eevee.taa_render_samples = 8
for frame in (1, 31, 61, 91):
    s.frame_set(frame)
    s.render.filepath = os.path.join(out, f'white-probe-{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
print('V134_WHITE_PREPARED', flush=True)
