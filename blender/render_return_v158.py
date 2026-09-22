"""Full-rate three-second return pan, after the disc has completely faded."""
import bpy,json,os,math,shutil
from mathutils import Vector,Quaternion
project=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
source=os.path.join(project,'blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v156-restored-playback.blend')
bpy.ops.wm.open_mainfile(filepath=source)
s=bpy.context.scene
with open(os.path.join(project,'app/data/shelf-return.json')) as f:timing=json.load(f)
with open(os.path.join(project,'public/review/v138/player.json')) as f:player=json.load(f)
with open(os.path.join(project,'public/room/v156/shelf-geometry.json')) as f:shelf=json.load(f)
# Ephemeral clean-plate state, exactly as v156. Never save over the authoring scene.
s.frame_set(1)
for name in ('V138_Playback_Record_Rig','V138_Playback_Sleeve_Rig'):
    for obj in bpy.data.objects[name].children_recursive:obj.hide_render=True
for name in ('V138_Tonearm_Rig','V138_Pivot_YawRig'):
    obj=bpy.data.objects[name];basis=obj.matrix_basis.copy();obj.animation_data_clear();obj.matrix_basis=basis
for name in ('INTERACT_Vinyl_6','PROJECT_VINYL_V126_Outline_6','PROJECT_VINYL_V126_Record_6'):bpy.data.objects[name].hide_render=False
s.frame_set(73)
targets={slot.material.name for obj in s.objects if 'Vinyl' in obj.name for slot in obj.material_slots if slot.material}
for mat in bpy.data.materials:
    if mat.use_nodes:
        fade=mat.node_tree.nodes.get('Selected target fades to black')
        if fade:fade.inputs[0].default_value=1 if mat.name in targets else 0
for slot in range(2,7):
    obj=bpy.data.objects[f'INTERACT_Vinyl_{slot}'];obj.hide_render=True
    for child in obj.children_recursive:child.hide_render=True
for part in player['meshes']:
    if part['name'].startswith(('V138_','V148_LabelMark','INTERACT_RecordPlayer_Base')) and not (part.get('rig') or '').startswith('V138_Playback_'):
        obj=bpy.data.objects.get(part['name'])
        if obj:obj.hide_render=True
cam=bpy.data.objects.new('CAM_V158_Return',bpy.data.cameras.new('CAM_V158_Return'));s.collection.objects.link(cam)
cam.rotation_mode='QUATERNION';cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36;cam.data.shift_x=cam.data.shift_y=0;s.camera=cam
s.render.resolution_percentage=100;s.render.resolution_x=1920;s.render.resolution_y=1080
s.eevee.taa_render_samples=32;s.eevee.volumetric_samples=16
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
start=shelf['cubbies'][1];end=player['camera']
def quat(v):return Quaternion((v[3],v[0],v[1],v[2]))
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
out=os.path.join(project,'blender/outputs/web-room-v158/return');os.makedirs(out,exist_ok=True)
total=timing['panStart']+timing['panDuration']+timing['revealDuration']+timing['insertDuration']
audit=[];cache={}
# Retain the exact previous endpoints; render new in-between camera poses.
cache[1.0]=os.path.join(project,'blender/outputs/web-room-v156/playback/0137.png')
cache[0.0]=os.path.join(project,'blender/outputs/web-room-v156/vinyl-background.png')
for i in range(math.ceil(total*timing['fps'])+1):
    weight=ease(1-(i/timing['fps']-timing['panStart'])/timing['panDuration'])
    cam.location=Vector(start['camera']).lerp(Vector(end['position']),weight)
    cam.rotation_quaternion=quat(start['quaternion']).slerp(quat(end['quaternion']),weight)
    vfov=start['verticalFov']+(end['fov']-start['verticalFov'])*weight
    cam.data.lens=36/(2*math.tan(math.radians(vfov)/2)*(16/9))
    path=os.path.join(out,f'{i:04d}.png');key=round(weight,10)
    if key in cache:shutil.copyfile(cache[key],path)
    else:
        s.render.filepath=path;bpy.ops.render.render(write_still=True);cache[key]=path
    audit.append({'frame':i,'seconds':i/timing['fps'],'weight':weight,'position':list(cam.location),'lens':cam.data.lens})
    print('V158_FRAME',i,flush=True)
with open(os.path.join(os.path.dirname(out),'camera-audit.json'),'w') as f:json.dump(audit,f)
print('V158_COMPLETE',flush=True)
