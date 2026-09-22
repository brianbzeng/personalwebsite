"""Shorter floor lamp and cubby-first monitor approach; source v129 untouched."""
import bpy, math, os, json, sys
from mathutils import Vector
s=bpy.context.scene
root=os.path.dirname(os.path.abspath(__file__))
out=os.path.join(root,'outputs/web-room-v130');os.makedirs(out,exist_ok=True)
target=os.path.join(root,'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v130-cubby-monitor-pan.blend')
assert 'v129-lamp-lighting-preview' in bpy.data.filepath
assert not os.path.exists(target) or '--refine-own-version' in sys.argv
old_bottom=.06;old_top=2.142;new_top=old_bottom+(old_top-old_bottom)*2/3
drop=old_top-new_top
def lower(z):
    if z<=.126:return z
    if z>=1.78425:return z-drop
    return .126+(z-.126)*(1.78425-drop-.126)/(1.78425-.126)
lamp=[]
for o in s.objects:
    if o.name.startswith('FLOOR_LAMP_V129_') and o.type=='MESH':
        o.data=o.data.copy()
        for v in o.data.vertices: v.co.z=lower(v.co.z)
        lamp.append(o.name)
    elif o.name.startswith('LAMP_V129_Floor_'):
        o.location.z-=drop
        if o.name.endswith('Down'):o.data.energy*=.55

home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
cam=home.copy();cam.data=home.data.copy();cam.name='CAM_MonitorCubby_v130';s.collection.objects.link(cam)
cam.animation_data_clear();cam.data.animation_data_clear();cam.rotation_mode='QUATERNION';cam.data.lens=50
start=home.location.copy();startq=home.rotation_euler.to_quaternion()
way=Vector((1.0,-2.8,2.35));end=Vector((0,2.15,1.40280008));screen=Vector((0,2.4759,1.40280008))
direction=(end-way).normalized();wayq=(screen-way).to_track_quat('-Z','Y')
c1=start+(way-start)*.62+Vector((1.8,-1,-1.4));c2=way-direction*2.4
split=.57
def ease(t):return t*t*(3-2*t)
def pose(t):
    if t<=split:
        a=t/split;u=a*a*(2-a);v=1-u
        p=v**3*start+3*v*v*u*c1+3*v*u*u*c2+u**3*way
        q=startq.slerp(wayq,ease(u))
    else:
        u=(t-split)/(1-split)
        speed=3*2.4*(1-split)/(split*(end-way).length)
        distance=speed*u+(3-2*speed)*u*u+(speed-2)*u*u*u
        p=way.lerp(end,distance);q=(screen-p).to_track_quat('-Z','Y')
    return p,q
for frame in range(1,242):
    t=(frame-1)/120 if frame<=121 else (241-frame)/120
    cam.location,cam.rotation_quaternion=pose(t)
    cam.data.shift_y=-.0175*(1-ease(t))
    cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_quaternion',frame=frame);cam.data.keyframe_insert('shift_y',frame=frame)
cam['path_description']='Dip toward the front-right cubby, then a straight descending approach over the chair and into the blank screen.'
cam['waypoint']=list(way);cam['end']=list(end)
# Dense baked samples should not introduce interpolation wobble.
for owner in [cam,cam.data]:
    for layer in owner.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
s.camera=home;s.frame_set(1)
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.eevee.taa_render_samples=16;s.eevee.volumetric_samples=16
report={'lampHeightBefore':old_top-old_bottom,'lampHeightAfter':new_top-old_bottom,'lampDrop':drop,'lampObjects':lamp,'waypoint':list(way),'endpoint':list(end),'home':list(start),'source':bpy.data.filepath}
with open(os.path.join(out,'changes.json'),'w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=target)
# Small framing probes before committing to full footage.
s.render.resolution_percentage=50;s.eevee.taa_render_samples=8
for frame in [1,37,61,70,91,105,121]:
    s.camera=cam;s.frame_set(frame);s.render.filepath=os.path.join(out,f'probe-{frame:03d}.png');bpy.ops.render.render(write_still=True)
print('V130_PREPARED',flush=True)
