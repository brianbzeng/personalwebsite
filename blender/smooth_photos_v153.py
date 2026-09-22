"""Render smooth, full-duration direct photo pans; preserve the v152 source."""
import bpy, os, json, math

s = bpy.context.scene
root = os.path.dirname(os.path.abspath(__file__))
source_tag = globals().get('SOURCE_TAG', 'v152-direct-polaroid-camera')
target_tag = globals().get('TARGET_TAG', 'v153-smooth-photo-camera')
version = globals().get('OUTPUT_VERSION', 153)
assert bpy.data.filepath.endswith(source_tag + '.blend')
target = bpy.data.filepath.replace(source_tag, target_tag)
assert not os.path.exists(target), 'Preserve existing Blender versions'
out = os.path.join(root, f'outputs/web-room-v{version}')
os.makedirs(out, exist_ok=True)
old = bpy.data.objects['CAM_Website_Pans_v119']
home = bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
end = bpy.data.objects['CAM_Shelf_photos_v137']

def sample(frame):
    whole = math.floor(frame)
    s.frame_set(whole, subframe=frame-whole)
    bpy.context.view_layer.update()

def pose(obj):
    return (obj.matrix_world.translation.copy(), obj.matrix_world.to_quaternion(), obj.data.lens, obj.data.shift_y)

def ease(t):
    return t*t*(3-2*t)

sample(1)
start = pose(home)
finish = pose(end)
sample(277)
offset = finish[0] - pose(old)[0]
c = bpy.data.objects.new(f'CAM_PhotosApproach_v{version}', home.data.copy())
s.collection.objects.link(c)
c.data.animation_data_clear()
c.rotation_mode = 'QUATERNION'
poses = []
# Three seconds at 30 fps. Sample the authored approach at fractional frames;
# never round to alternating one/two-frame jumps as in v152.
for i in range(91):
    t = i/90
    weight = ease(t)
    sample(205 + 72*t)
    p = pose(old)
    poses.append((p[0] + offset*weight, start[1].slerp(finish[1], weight),
                  start[2] + (finish[2]-start[2])*weight,
                  start[3] + (finish[3]-start[3])*weight))
assert (poses[0][0]-start[0]).length < 1e-5
assert (poses[-1][0]-finish[0]).length < 1e-5
for reverse in (False, True):
    for i, value in enumerate(reversed(poses) if reverse else poses):
        frame = (121 if reverse else 1) + i
        c.location, c.rotation_quaternion, c.data.lens, c.data.shift_y = value
        c.keyframe_insert('location', frame=frame)
        c.keyframe_insert('rotation_quaternion', frame=frame)
        c.data.keyframe_insert('lens', frame=frame)
        c.data.keyframe_insert('shift_y', frame=frame)
c['clip_ranges'] = '1-91 room to photos; 121-211 exact reversed path; 30 fps'
s.render.fps = 30
s.render.fps_base = 1
sample(1)
s.camera = home
bpy.ops.wm.save_as_mainfile(filepath=target)

# Ephemeral release state only, not saved into the authoring scene.
for name in ('INTERACT_Vinyl_6', 'PROJECT_VINYL_V126_Outline_6', 'PROJECT_VINYL_V126_Record_6'):
    bpy.data.objects[name].hide_render = False
for name in ('V138_Playback_Record_Rig', 'V138_Playback_Sleeve_Rig'):
    for obj in bpy.data.objects[name].children_recursive:
        obj.hide_render = True
for name in ('V138_Tonearm_Rig', 'V138_Pivot_YawRig'):
    obj = bpy.data.objects[name]
    basis = obj.matrix_basis.copy()
    obj.animation_data_clear()
    obj.matrix_basis = basis
c.animation_data_clear()
c.data.animation_data_clear()
targets = {slot.material.name for obj in s.objects if 'Vinyl' in obj.name for slot in obj.material_slots if slot.material}
s.render.resolution_percentage = 100
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.eevee.taa_render_samples = 16
s.eevee.volumetric_samples = 16
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGB'
audit = []
for reverse in (False, True):
    name = 'photos-out' if reverse else 'photos-in'
    folder = os.path.join(out, name)
    os.makedirs(folder, exist_ok=True)
    for i, value in enumerate(reversed(poses) if reverse else poses):
        sample((73 if reverse else 1) + 72*i/90)
        c.location, c.rotation_quaternion, c.data.lens, c.data.shift_y = value
        s.camera = c
        for material in bpy.data.materials:
            fade = material.node_tree.nodes.get('Selected target fades to black') if material.use_nodes else None
            if fade:
                fade.inputs[0].default_value = min(1, 2*ease(1-i/90 if reverse else i/90)) if material.name in targets else 0
        bpy.context.view_layer.update()
        audit.append({'clip': name, 'frame': i, 'position': list(c.location), 'rotation': list(c.rotation_quaternion)})
        s.render.filepath = os.path.join(folder, f'{i:04d}.png')
        bpy.ops.render.render(write_still=True)
        print('V153_FRAME', name, i, flush=True)
with open(os.path.join(out, 'camera-audit.json'), 'w') as handle:
    json.dump(audit, handle)
print('V153_COMPLETE', flush=True)
