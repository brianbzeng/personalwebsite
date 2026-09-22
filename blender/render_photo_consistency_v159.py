"""Photo cubby and its pans from the approved v156 sleeve/player scene.

Never modify the source blend or existing public media. Use --probes for stills;
full run resumes already rendered frames in this version's private output folder.
"""
import bpy, json, math, os, sys

root = os.path.dirname(os.path.abspath(__file__))
source = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v156-restored-playback.blend')
bpy.ops.wm.open_mainfile(filepath=source)
s = bpy.context.scene
out = os.path.join(root, 'outputs/web-room-v159')
os.makedirs(out, exist_ok=True)

def sample(frame):
    whole = math.floor(frame)
    s.frame_set(whole, subframe=frame-whole)
    bpy.context.view_layer.update()

def pose(obj):
    return (obj.matrix_world.translation.copy(), obj.matrix_world.to_quaternion(), obj.data.lens, obj.data.shift_y)

def ease(t):
    return t*t*(3-2*t)

# Reuse the exact approved v154 camera keys, not a newly approximated path.
authored = bpy.data.objects['CAM_PhotosApproach_v154']
photo_poses = {}
for reverse in (False, True):
    values = []
    for i in range(91):
        sample((121 if reverse else 1)+i)
        values.append(pose(authored))
    photo_poses['photos-out' if reverse else 'photos-in'] = values

sample(1)
for name in ('V138_Playback_Record_Rig', 'V138_Playback_Sleeve_Rig'):
    for obj in bpy.data.objects[name].children_recursive:
        obj.hide_render = True
for name in ('V138_Tonearm_Rig', 'V138_Pivot_YawRig'):
    obj = bpy.data.objects[name]
    basis = obj.matrix_basis.copy()
    obj.animation_data_clear()
    obj.matrix_basis = basis
for name in ('INTERACT_Vinyl_6', 'PROJECT_VINYL_V126_Outline_6', 'PROJECT_VINYL_V126_Record_6'):
    bpy.data.objects[name].hide_render = False

camera = bpy.data.objects.new('CAM_V159_ConsistentPhotos', authored.data.copy())
s.collection.objects.link(camera)
camera.data.animation_data_clear()
camera.rotation_mode = 'QUATERNION'
targets = {slot.material.name for obj in s.objects if 'Vinyl' in obj.name for slot in obj.material_slots if slot.material}
photos = [obj for obj in s.objects if any('SHELF_Polaroid_'+letter+'_' in obj.name for letter in 'ABCD')]
assert len(photos) == 16, 'All four cards, pictures and outlines must be included'
sample(73)
cubby_poses = {i: pose(bpy.data.objects['CAM_Shelf_'+name+'_v137']) for i,name in ((1,'records'),(2,'photos'))}

s.render.resolution_percentage = 100
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.eevee.taa_render_samples = 16
s.eevee.volumetric_samples = 16
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGB'
audit = {'source': os.path.basename(source), 'photos': len(photos), 'sleeves': {}, 'frames': []}
for slot in range(7):
    obj = bpy.data.objects[f'INTERACT_Vinyl_{slot}']
    audit['sleeves'][str(slot)] = list(obj.matrix_world.translation)

def paint(name, value, ambient=73, amount=1):
    sample(ambient)
    camera.location, camera.rotation_quaternion, camera.data.lens, camera.data.shift_y = value
    s.camera = camera
    for material in bpy.data.materials:
        fade = material.node_tree.nodes.get('Selected target fades to black') if material.use_nodes else None
        if fade:
            fade.inputs[0].default_value = amount if material.name in targets else 0
    bpy.context.view_layer.update()
    path = os.path.join(out, name+'.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        s.render.filepath = path
        bpy.ops.render.render(write_still=True)
    audit['frames'].append({'name':name, 'position':list(camera.location), 'quaternion':list(camera.rotation_quaternion), 'lens':camera.data.lens, 'ambient':ambient})
    print('V159_FRAME', name, flush=True)

paint('photos-still', cubby_poses[2])
for obj in photos:
    obj.hide_render = True
paint('photos-background', cubby_poses[2])
for obj in photos:
    obj.hide_render = False
if '--probes' not in sys.argv:
    for name, values in photo_poses.items():
        reverse = name == 'photos-out'
        for i,value in enumerate(values):
            paint(f'{name}/{i:04d}', value, (73 if reverse else 1)+72*i/90, min(1,2*ease(1-i/90 if reverse else i/90)))
    for a,b in ((1,2),(2,1)):
        start, end = cubby_poses[a], cubby_poses[b]
        for i in range(37):
            t = ease(i/36)
            value = (start[0].lerp(end[0],t), start[1].slerp(end[1],t), start[2]*(1-t)+end[2]*t, start[3]*(1-t)+end[3]*t)
            paint(f'shelf-{a}-{b}/{i:04d}', value)
with open(os.path.join(out,'scene-audit.json'),'w') as handle:
    json.dump(audit,handle,indent=2)
print('V159_COMPLETE', flush=True)
