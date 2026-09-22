import bpy, os
from mathutils import Vector

s = bpy.context.scene
camera = bpy.data.objects['CAM_Website_Pans_v119']
home = bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
target = bpy.data.objects['INTERACT_Monitor_Screen'].matrix_world.translation.copy()
home_target = home.location + (home.rotation_euler.to_quaternion() @ Vector((0, 0, -1))) * (target-home.location).length
# Preserve all positions and easing, but aim at an interpolated target instead
# of interpolating independent rotations that let the monitor leave the frame.
poses = []
for frame in range(1, 193):
    s.frame_set(frame)
    f = frame-1
    t = 0 if f < 12 else (f-12)/72 if f <= 84 else 1 if f <= 108 else 1-(f-108)/72 if f <= 180 else 0
    t = t*t*(3-2*t)
    direction = home_target.lerp(target, t) - camera.location
    poses.append((frame, direction.to_track_quat('-Z', 'Y')))
for frame, rotation in poses:
    camera.rotation_quaternion = rotation
    camera.keyframe_insert('rotation_quaternion', frame=frame)
s.camera = camera
s.render.resolution_x = 1280
s.render.resolution_y = 720
s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGB'
s.eevee.taa_render_samples = 8
s.eevee.volumetric_samples = 8
root = os.path.join(os.path.dirname(__file__), 'outputs', 'web-room-v122')
for name, frames in [('monitor-in', range(13, 86)), ('monitor-out', range(109, 182))]:
    folder = os.path.join(root, name)
    os.makedirs(folder, exist_ok=True)
    for index, frame in enumerate(frames):
        s.frame_set(frame)
        s.render.filepath = os.path.join(folder, f'{index:04d}.png')
        bpy.ops.render.render(write_still=True)
        print('WEB_FRAME', name, index, flush=True)
