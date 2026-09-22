import bpy,json,os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;cam=bpy.data.objects['CAM_MonitorDive_v127'];home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
start=home.location.copy();end=Vector((0,.9710854888,1.4028000832));waypoint=Vector((1.35,-1.6,2.85));direction=(end-waypoint).normalized()
s.frame_set(1);start_error=(cam.location-start).length
s.frame_set(121);end_error=(cam.location-end).length
straight=[]
for f in range(66,122):
    s.frame_set(f);straight.append((cam.location-waypoint).cross(direction).length)
s.frame_set(241);return_error=(cam.location-start).length
flash={}
for f in [1,127,128,129,130,131,132,133,240]:
    s.frame_set(f);flash[f]=float(bpy.data.objects['CTRL_LightningSync']['lightning_strength'])
s.frame_set(121)
corners=[list(world_to_camera_view(s,cam,Vector((x,2.4723,z)))) for x in [-.5749333,.5749333] for z in [1.0794,1.7262]]
report={'startError':start_error,'endError':end_error,'returnError':return_error,'straightLineError':max(straight),'lightning':flash,'screenProjection':corners,'resolution':[s.render.resolution_x,s.render.resolution_y]}
assert max(start_error,end_error,return_error,max(straight))<.00001,report
assert flash[128]==1 and flash[1]==flash[240]==0,report
with open(os.path.join(os.path.dirname(__file__),'outputs/web-room-v127/audit.json'),'w') as f:json.dump(report,f,indent=2)
print('CAMERA_LIGHTNING_AUDIT',json.dumps(report),flush=True)
