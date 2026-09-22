"""Ephemeral release pose and current shelf geometry; never overwrite source."""
import bpy,os,json
from mathutils import Vector
s=bpy.context.scene
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert bpy.data.filepath.endswith('v149-approved-project-covers.blend')
s.frame_set(1);bpy.context.view_layer.update()
home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
monitor=bpy.data.objects['CAM_MonitorRounded_v133']
assert (home.matrix_world.translation-monitor.matrix_world.translation).length<1e-6, 'Restore approved greeting before rendering'
for name in ('INTERACT_Vinyl_6','PROJECT_VINYL_V126_Outline_6','PROJECT_VINYL_V126_Record_6'):
    bpy.data.objects[name].hide_render=False
for name in ('V138_Playback_Record_Rig','V138_Playback_Sleeve_Rig'):
    for o in bpy.data.objects[name].children_recursive:o.hide_render=True
for name in ('V138_Tonearm_Rig','V138_Pivot_YawRig'):
    o=bpy.data.objects[name];pose=o.matrix_basis.copy();o.animation_data_clear();o.matrix_basis=pose
s.frame_set(277);bpy.context.view_layer.update()
def worldmesh(o,center=None,rotation=None):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();positions=[]
    for v in me.vertices:
        p=o.matrix_world@v.co
        if center is not None:p=rotation.inverted()@(p-center)
        positions.extend(p)
    result={'positions':positions,'indices':[i for t in me.loop_triangles for i in t.vertices]};ev.to_mesh_clear();return result
with open(os.path.join(ROOT,'public/room/v137/shelf-geometry.json')) as f:model=json.load(f)
for d in model['objects']:
    o=bpy.data.objects[d['name']];q=o.matrix_world.to_quaternion();center=Vector((-.028+.2585/2,0,-.1175+.2585/2))
    d['origin']=list(o.matrix_world@center);d['quaternion']=[q.x,q.y,q.z,q.w]
model['occluders']=[worldmesh(bpy.data.objects[n]) for n in ['SHELF_VinylRack_Left','SHELF_VinylRack_Right','SHELF_Carcass_Cohesive','INTERACT_Vinyl_0','INTERACT_Vinyl_1']]
for d in model['decorations']:
    o=bpy.data.objects[d['name']];q=o.matrix_world.to_quaternion();d['origin']=list(o.matrix_world@Vector((-.028+.2585/2,0,-.1175+.2585/2)));d['quaternion']=[q.x,q.y,q.z,q.w]
book=bpy.data.objects['BOOK_Mid_9'];wire=bpy.data.objects['CATHODE_WIREFRAME_BOOK_Mid_9'];q=book.matrix_world.to_quaternion();center=book.matrix_world.translation.copy()
model['book'].update(origin=list(center),quaternion=[q.x,q.y,q.z,q.w],body=worldmesh(book,center,q),outline=worldmesh(wire,center,q))
model['version']=149
out=os.path.join(ROOT,'blender/outputs/web-room-v149');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'shelf-geometry.json'),'w') as f:json.dump(model,f)
s.frame_set(1)
print('V149_STATIC_ROOM_PREPARED',flush=True)
