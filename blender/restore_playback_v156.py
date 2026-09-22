"""Original web playback camera, complete environment, root-only sleeve clearance."""
import bpy, json, math, os, shutil
from mathutils import Matrix, Vector, Quaternion
root=os.path.dirname(os.path.abspath(__file__))
project=os.path.dirname(root)
s=bpy.context.scene
assert bpy.data.filepath.endswith('v154-seated-first-photo.blend')
target=bpy.data.filepath.replace('v154-seated-first-photo','v156-restored-playback')
assert not os.path.exists(target)
out=os.path.join(root,'outputs/web-room-v156');os.makedirs(out,exist_ok=True)
with open(os.path.join(project,'public/review/v138/player.json')) as f:player=json.load(f)
with open(os.path.join(project,'public/room/v149/shelf-geometry.json')) as f:shelf=json.load(f)
s.frame_set(1)
# Outlines and records are children of their sleeve. Translate the root ONCE.
before={}
for slot in range(7):
    obj=bpy.data.objects.get(f'INTERACT_Vinyl_{slot}')
    if obj:
        before[obj.name]=list(obj.matrix_world.translation)
        obj.matrix_world=Matrix.Translation((-.01,0,0))@obj.matrix_world
bpy.context.view_layer.update()
parts=[p for p in player['meshes'] if p['name'].startswith(('V138_','V148_LabelMark','INTERACT_RecordPlayer_Base')) and not (p.get('rig') or '').startswith('V138_Playback_')]
for part in parts:
    obj=bpy.data.objects.get(part['name'])
    if not obj:continue
    for index,item in enumerate(part['materials']):
        if item.get('sweep'):continue
        mat=bpy.data.materials.new('V156_'+part['name']+'_'+str(index));mat.use_nodes=True
        nodes=mat.node_tree.nodes;nodes.clear();emit=nodes.new('ShaderNodeEmission')
        emit.inputs['Color'].default_value=(*item['color'],1);emit.inputs['Strength'].default_value=2**.3
        output=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(emit.outputs[0],output.inputs['Surface'])
        mat.diffuse_color=(*item['color'],1);mat.use_backface_culling=bool(item.get('frontSide'))
        obj.material_slots[index].link='OBJECT';obj.material_slots[index].material=mat
bpy.ops.wm.save_as_mainfile(filepath=target)
# Export the same local cover meshes, shifted roots and corresponding masks.
for item in shelf['objects']:item['origin'][0]-=.01
for mask in shelf['occluders'][3:5]:
    for i in range(0,len(mask['positions']),3):mask['positions'][i]-=.01
media=os.path.join(project,'public/room/v156');os.makedirs(media,exist_ok=True)
with open(os.path.join(media,'shelf-geometry.json'),'w') as f:json.dump(shelf,f,separators=(',',':'))
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
cam=bpy.data.objects.new('CAM_V156_OriginalWebPath',bpy.data.cameras.new('CAM_V156_OriginalWebPath'));s.collection.objects.link(cam)
cam.rotation_mode='QUATERNION';cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36;cam.data.shift_x=cam.data.shift_y=0;s.camera=cam
s.render.resolution_percentage=100;s.render.resolution_x=1920;s.render.resolution_y=1080
s.eevee.taa_render_samples=32;s.eevee.volumetric_samples=16
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
start=shelf['cubbies'][1];end=player['camera']
def quat(v):return Quaternion((v[3],v[0],v[1],v[2]))
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def camera_at(weight):
    cam.location=Vector(start['camera']).lerp(Vector(end['position']),weight)
    cam.rotation_quaternion=quat(start['quaternion']).slerp(quat(end['quaternion']),weight)
    vfov=start['verticalFov']+(end['fov']-start['verticalFov'])*weight
    cam.data.lens=36/(2*math.tan(math.radians(vfov)/2)*(16/9))
def paint(path,weight):
    camera_at(weight);s.render.filepath=path;bpy.ops.render.render(write_still=True)
camera_at(0)
paint(os.path.join(out,'vinyl-still.png'),0)
for slot in range(2,7):
    obj=bpy.data.objects[f'INTERACT_Vinyl_{slot}'];obj.hide_render=True
    for child in obj.children_recursive:child.hide_render=True
for part in parts:
    obj=bpy.data.objects.get(part['name'])
    if obj:obj.hide_render=True
cache={}
audit=[]
for sequence,count in [('playback',138),('return',28)]:
    folder=os.path.join(out,sequence);os.makedirs(folder,exist_ok=True)
    for i in range(count):
        weight=ease(((i+1)-42)/46) if sequence=='playback' else ease(1-(i/24-.18)/.75)
        path=os.path.join(folder,f'{i:04d}.png');key=round(weight,10)
        if key in cache:shutil.copyfile(cache[key],path)
        else:paint(path,weight);cache[key]=path
        camera_at(weight)
        audit.append({'sequence':sequence,'frame':i,'weight':weight,'position':list(cam.location),'quaternion':[cam.rotation_quaternion[k] for k in (1,2,3,0)],'lens':cam.data.lens})
        print('V156_FRAME',sequence,i,flush=True)
shutil.copyfile(os.path.join(out,'playback/0000.png'),os.path.join(out,'vinyl-background.png'))
with open(os.path.join(out,'camera-audit.json'),'w') as f:json.dump(audit,f)
print('V156_COMPLETE',flush=True)
