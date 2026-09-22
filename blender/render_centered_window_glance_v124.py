import bpy, os, math
from mathutils import Vector
s=bpy.context.scene
camera=bpy.data.objects['CAM_Website_Pans_v119']
home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
home.data=home.data.copy()
home.data.shift_y=-0.0175
camera.data=camera.data.copy()
poses=[]
for start,target in [(1,Vector((0,2.47590017,1.40280008))),(385,Vector((2.615,-2.28,2.1)))]:
    home_target=home.location+(home.rotation_euler.to_quaternion()@Vector((0,0,-1)))*(target-home.location).length
    for frame in range(start,start+192):
        s.frame_set(frame)
        f=frame-start
        t=0 if f<12 else (f-12)/72 if f<=84 else 1 if f<=108 else 1-(f-108)/72 if f<=180 else 0
        t=t*t*(3-2*t)
        aim=home_target.lerp(target,t)
        if start==1:
            # A deliberate outside glance in the middle of the monitor approach.
            peek=.64*math.sin(math.pi*t)**6
            aim=aim.lerp(Vector((0,7,2.2)),peek)
        poses.append((frame,(aim-camera.location).to_track_quat('-Z','Y'),-.0175*(1-t)))
for frame,rotation,shift in poses:
    camera.rotation_quaternion=rotation
    camera.keyframe_insert('rotation_quaternion',frame=frame)
    camera.data.shift_y=shift
    camera.data.keyframe_insert('shift_y',frame=frame)
s.render.resolution_x=1280
s.render.resolution_y=720
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGB'
s.eevee.taa_render_samples=8
s.eevee.volumetric_samples=8
root=os.path.join(os.path.dirname(__file__),'outputs','web-room-v124')
for name,frames in [('monitor-in',range(13,86)),('monitor-out',range(109,182)),('diploma-in',range(397,470)),('diploma-out',range(493,566))]:
    s.camera=camera
    folder=os.path.join(root,name)
    os.makedirs(folder,exist_ok=True)
    for index,frame in enumerate(frames):
        s.frame_set(frame)
        s.render.filepath=os.path.join(folder,f'{index:04d}.png')
        bpy.ops.render.render(write_still=True)
