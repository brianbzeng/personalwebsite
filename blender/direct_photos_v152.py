"""Dedicated direct photo camera and clean interactive plate; preserve v150."""
import bpy,os,json
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;root=os.path.dirname(os.path.abspath(__file__))
assert bpy.data.filepath.endswith('v150-direct-book-camera.blend')
target=bpy.data.filepath.replace('v150-direct-book-camera','v152-direct-polaroid-camera')
assert not os.path.exists(target),'Do not overwrite an existing source'
old=bpy.data.objects['CAM_Website_Pans_v119'];home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119'];end=bpy.data.objects['CAM_Shelf_photos_v137']
def pose(c):return c.matrix_world.translation.copy(),c.matrix_world.to_quaternion(),c.data.lens,c.data.shift_y
def ease(t):return t*t*(3-2*t)
c=bpy.data.objects.new('CAM_PhotosApproach_v152',old.data.copy());s.collection.objects.link(c);c.data.animation_data_clear();c.rotation_mode='QUATERNION'
s.frame_set(277);oldend=pose(old);newend=pose(end);poses={}
for reverse in (False,True):
 for i in range(49):
  t=i/48;s.frame_set(round((301 if reverse else 205)+72*t));p=pose(old);weight=1-ease(t) if reverse else ease(t)
  value=(p[0]+(newend[0]-oldend[0])*weight,p[1].slerp(newend[1],weight),p[2],p[3]*(1-weight));frame=(73 if reverse else 1)+i;poses[frame]=value
  c.location,c.rotation_quaternion,c.data.lens,c.data.shift_y=value;c.keyframe_insert('location',frame=frame);c.keyframe_insert('rotation_quaternion',frame=frame);c.data.keyframe_insert('lens',frame=frame);c.data.keyframe_insert('shift_y',frame=frame)
s.frame_set(1);s.camera=home;bpy.context.view_layer.update()
points=[world_to_camera_view(s,home,bpy.data.objects[f'SHELF_Polaroid_{letter}_Card'].matrix_world.translation) for letter in 'DCBA']
out=os.path.join(root,'outputs/web-room-v152');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'photos-camera.json'),'w')as f:json.dump({'hotspot':{'x':sum(v.x for v in points)/4,'y':1-sum(v.y for v in points)/4},'frames':49,'fps':24},f)
c['clip_ranges']='1-49 room to photographs; 73-121 photographs directly to room'
bpy.ops.wm.save_as_mainfile(filepath=target)
for name in ('INTERACT_Vinyl_6','PROJECT_VINYL_V126_Outline_6','PROJECT_VINYL_V126_Record_6'):bpy.data.objects[name].hide_render=False
for name in ('V138_Playback_Record_Rig','V138_Playback_Sleeve_Rig'):
 for o in bpy.data.objects[name].children_recursive:o.hide_render=True
for name in ('V138_Tonearm_Rig','V138_Pivot_YawRig'):
 o=bpy.data.objects[name];basis=o.matrix_basis.copy();o.animation_data_clear();o.matrix_basis=basis
c.animation_data_clear();c.data.animation_data_clear()
targets={slot.material.name for o in s.objects if 'Vinyl' in o.name for slot in o.material_slots if slot.material}
def selected(amount):
 for m in bpy.data.materials:
  if m.use_nodes:
   fade=m.node_tree.nodes.get('Selected target fades to black')
   if fade:fade.inputs[0].default_value=amount if m.name in targets else 0
s.render.resolution_percentage=100;s.render.resolution_x=1920;s.render.resolution_y=1080;s.eevee.taa_render_samples=16;s.eevee.volumetric_samples=16
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
photos=[o for o in s.objects if any(o.name==prefix+f'SHELF_Polaroid_{letter}_{part}' for prefix in ('','CATHODE_WIREFRAME_') for letter in 'ABCD' for part in ('Card','Photo'))]
s.frame_set(73);s.camera=end;selected(1)
for o in photos:o.hide_render=True
s.render.filepath=os.path.join(out,'photos-background.png');bpy.ops.render.render(write_still=True)
for o in photos:o.hide_render=False
s.render.resolution_x=1280;s.render.resolution_y=720
for reverse in (False,True):
 name='photos-out' if reverse else 'photos-in';folder=os.path.join(out,name);os.makedirs(folder,exist_ok=True)
 for i in range(49):
  s.frame_set(round((73 if reverse else 1)+72*i/48));c.location,c.rotation_quaternion,c.data.lens,c.data.shift_y=poses[(73 if reverse else 1)+i];s.camera=c;selected(min(1,2*ease(1-i/48 if reverse else i/48)))
  s.render.filepath=os.path.join(folder,f'{i:04d}.png');bpy.ops.render.render(write_still=True);print('V152_FRAME',name,i,flush=True)
print('V152_COMPLETE',flush=True)
