"""Rounded two-straight monitor approach. Only a new camera is added to v132."""
import bpy, os, math, json, bisect
from mathutils import Vector

s = bpy.context.scene
root = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(root, 'outputs/web-room-v133')
os.makedirs(out, exist_ok=True)
target = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v133-rounded-monitor-pan.blend')
assert 'v132-mug-facing-seat' in bpy.data.filepath
assert not os.path.exists(target), 'Preserve earlier versions.'
s.frame_set(1)
original = {o.name: list(sum((list(row) for row in o.matrix_world), [])) for o in s.objects}
home = bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
start = home.location.copy()
startq = home.matrix_world.to_quaternion()
end = Vector((0, 2.15, 1.40280008))
screen = Vector((0, 2.4759, 1.40280008))
# The virtual corner is on the screen centerline, never beyond its right side.
corner = Vector((0, -4.2))
origin = Vector((start.x, start.y))
finish = Vector((end.x, end.y))
incoming = (corner - origin).normalized()
entry = corner - incoming * 2.0
leave = corner + Vector((0, 2.0))
def bend(u):
    return (1-u)**2 * entry + 2*(1-u)*u * corner + u*u * leave
curve = [bend(i/2000) for i in range(2001)]
distances = [0.0]
for a, b in zip(curve, curve[1:]):
    distances.append(distances[-1] + (b-a).length)
first = (entry-origin).length
last = (finish-leave).length
length = first + distances[-1] + last
def ease(t):
    return t*t*(3-2*t)
def point(progress):
    distance = progress * length
    if distance <= first:
        xy = origin.lerp(entry, distance/first)
    elif distance < first + distances[-1]:
        d = distance-first
        j = bisect.bisect_right(distances, d)
        f = (d-distances[j-1])/(distances[j]-distances[j-1])
        xy = curve[j-1].lerp(curve[j], f)
    else:
        xy = leave.lerp(finish, (distance-first-distances[-1])/last)
    # One continuous downhill grade, with no waypoint-specific vertical lurch.
    return Vector((xy.x, xy.y, start.z+(end.z-start.z)*progress))
def pose(t):
    progress = ease(t)
    p = point(progress)
    look = (screen-p).to_track_quat('-Z', 'Y')
    q = startq.slerp(look, ease(min(1, progress/.65)))
    return p, q

cam = home.copy()
cam.data = home.data.copy()
cam.name = 'CAM_MonitorRounded_v133'
s.collection.objects.link(cam)
cam.animation_data_clear()
cam.data.animation_data_clear()
cam.rotation_mode = 'QUATERNION'
cam.data.lens = 50
for frame in range(1, 242):
    t = (frame-1)/120 if frame <= 121 else (241-frame)/120
    cam.location, cam.rotation_quaternion = pose(t)
    cam.data.shift_y = -.0175*(1-ease(t))
    cam.keyframe_insert('location', frame=frame)
    cam.keyframe_insert('rotation_quaternion', frame=frame)
    cam.data.keyframe_insert('shift_y', frame=frame)
for owner in (cam, cam.data):
    for layer in owner.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:
                        key.interpolation = 'LINEAR'
cam['path_description'] = 'Straight inward descent, rounded corner without right overshoot, straight final run on the monitor centerline.'
samples = [list(point(i/1000)) for i in range(1001)]
assert all(p[0] <= 1e-6 for p in samples)
assert all(a[2] >= b[2] for a,b in zip(samples,samples[1:]))
assert (point(0)-start).length < 1e-5 and (point(1)-end).length < 1e-5
s.camera = home
s.frame_set(1)
assert all(original[o.name] == list(sum((list(row) for row in o.matrix_world), [])) for o in s.objects if o.name in original)
report = dict(source=bpy.data.filepath, start=list(start), end=list(end), corner=list(corner), entry=list(entry), leave=list(leave), firstLength=first, bendLength=distances[-1], lastLength=last, samples=samples, originalTransformsUnchanged=True)
with open(os.path.join(out, 'camera-audit.json'), 'w') as f:
    json.dump(report, f, indent=2)
bpy.ops.wm.save_as_mainfile(filepath=target)
s.camera = cam
s.render.resolution_x = 1920
s.render.resolution_y = 1080
s.render.resolution_percentage = 50
s.render.image_settings.file_format = 'PNG'
s.eevee.taa_render_samples = 8
for frame in (1, 25, 49, 61, 73, 85, 97, 109, 121):
    s.frame_set(frame)
    s.render.filepath = os.path.join(out, f'probe-{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
print('V133_PREPARED', flush=True)
