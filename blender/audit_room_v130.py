import bpy,json,os
from mathutils import Vector
s=bpy.context.scene;cam=bpy.data.objects['CAM_MonitorCubby_v130'];home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
way=Vector(cam['waypoint']);end=Vector(cam['end']);direction=(end-way).normalized()
errors=[];chair_clearance=[]
for frame in range(1,242):
    s.frame_set(frame)
    if 70<=frame<=121:errors.append((cam.location-way).cross(direction).length)
    if -.32<=cam.location.x<=.32 and .67<=cam.location.y<=.81:chair_clearance.append(cam.location.z-1.549525)
s.frame_set(1);start_error=(cam.location-home.location).length
s.frame_set(121);end_error=(cam.location-end).length
s.frame_set(241);return_error=(cam.location-home.location).length
shade=bpy.data.objects['FLOOR_LAMP_V129_DESK_LampShade'];top=max((shade.matrix_world@v.co).z for v in shade.data.vertices)
flash={}
for f in [1,128,130,132,240]:s.frame_set(f);flash[f]=bpy.data.objects['CTRL_LightningSync']['lightning_strength']
report={'startError':start_error,'endError':end_error,'returnError':return_error,'straightLineError':max(errors),'chairClearance':min(chair_clearance,default=None),'lampHeight':top-.06,'lampHeightRatio':(top-.06)/2.082,'lightning':flash}
assert max(start_error,end_error,return_error,max(errors))<1e-5,report
assert not chair_clearance or min(chair_clearance)>.07,report
assert abs(report['lampHeightRatio']-2/3)<.001,report
assert flash[128]==1 and flash[1]==flash[240]==0,report
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs/web-room-v130/audit.json'),'w') as f:json.dump(report,f,indent=2)
print('V130_AUDIT_PASS',json.dumps(report),flush=True)
