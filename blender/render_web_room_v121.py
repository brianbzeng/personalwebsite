"""Render website media from the approved scene without saving scene changes."""
import bpy, os, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.context.scene
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
out = os.path.join(root, 'blender', 'outputs', 'web-room-v121')
os.makedirs(out, exist_ok=True)
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.taa_render_samples = 8
scene.eevee.volumetric_samples = 8
home = bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
pan = bpy.data.objects['CAM_Website_Pans_v119']
scene.frame_set(1)
scene.camera = home
targets = {}
for label, names in {
    'monitor': ['INTERACT_Monitor_Screen'],
    'vinyls': ['INTERACT_Vinyl_' + str(i) for i in range(7)],
    'frame': ['CATHODE_CLEAN_OUTLINE_DiplomaFrame_v109'],
}.items():
    pts = [world_to_camera_view(scene, home, bpy.data.objects[n].matrix_world @ Vector(v))
           for n in names for v in bpy.data.objects[n].bound_box]
    targets[label] = {'left': min(p.x for p in pts)*100,
                      'top': (1-max(p.y for p in pts))*100,
                      'width': (max(p.x for p in pts)-min(p.x for p in pts))*100,
                      'height': (max(p.y for p in pts)-min(p.y for p in pts))*100}
with open(os.path.join(out, 'hotspots.json'), 'w') as f:
    json.dump(targets, f, indent=2)

def render_sequence(name, frames, camera):
    scene.camera = camera
    folder = os.path.join(out, name)
    os.makedirs(folder, exist_ok=True)
    for index, frame in enumerate(frames):
        scene.frame_set(frame)
        scene.render.filepath = os.path.join(folder, f'{index:04d}.png')
        if not os.path.exists(scene.render.filepath):
            bpy.ops.render.render(write_still=True)
        print('WEB_FRAME', name, index, flush=True)

# All approach and return frames are separate assets so hidden destinations
# cost nothing on initial load. The shared amber animation is five seconds.
# Hold selection fades at zero for the greeting loop, without changing the blend.
for material in bpy.data.materials:
    if not material.use_nodes:
        continue
    node = material.node_tree.nodes.get('Selected target fades to black')
    if node:
        node.inputs[0].driver_remove('default_value')
        node.inputs[0].default_value = 0
render_sequence('idle', range(1, 121), home)
# Reopen the source to restore selection drivers before rendering approaches.
bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.taa_render_samples = 8
scene.eevee.volumetric_samples = 8
pan = bpy.data.objects['CAM_Website_Pans_v119']
render_sequence('monitor-in', range(13, 86), pan)
render_sequence('monitor-out', range(109, 182), pan)
print('WEB_RENDER_COMPLETE', out, flush=True)
