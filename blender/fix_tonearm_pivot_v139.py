"""Anchor the approval tonearm at its bearing; preserve v138 and all other rigs."""
import bpy
import json
import math
import os
from mathutils import Quaternion, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert bpy.data.filepath.endswith('v138-player-book-review.blend')
target = os.path.join(os.path.dirname(bpy.data.filepath),
                      'lofi-room-cathode-glm53f-city-v139-anchored-tonearm.blend')
assert not os.path.exists(target), 'Preserve existing versions; do not overwrite.'
scene = bpy.context.scene
arm = bpy.data.objects['V138_Tonearm_Rig']
needle = bpy.data.objects['V138_Stylus']
scene.frame_set(1)
bpy.context.view_layer.update()
pivot = arm.matrix_world.translation.copy()
assert (pivot - Vector((2.565, .972, 1.493))).length < 1e-6
ev = needle.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = ev.to_mesh()
local = [arm.matrix_world.inverted() @ ev.matrix_world @ v.co for v in mesh.vertices]
ev.to_mesh_clear()

# Arm runs along local -X, so a positive Y pitch lifts only its needle end.
def orientation(yaw, pitch):
    return Quaternion((0, 0, 1), yaw) @ Quaternion((0, 1, 0), pitch)

def tip(yaw, pitch):
    q = orientation(yaw, pitch)
    return min((pivot + q @ p for p in local), key=lambda p: p.z)

record_top = 1.4785
lo, hi = 0.0, math.radians(1)
for _ in range(40):
    mid = (lo + hi) / 2
    if tip(-.55, mid).z < record_top + .00005:
        lo = mid
    else:
        hi = mid
landing_pitch = (lo + hi) / 2
lift_pitch = math.radians(1)
keys = [(1, 0, 0), (90, 0, 0), (98, 0, lift_pitch),
        (112, -.55, lift_pitch), (122, -.55, landing_pitch),
        (144, -.55, landing_pitch)]
arm.animation_data_clear()
arm.rotation_mode = 'QUATERNION'
arm.location = pivot
samples = []
for frame in range(1, 145):
    a, b = next((a, b) for a, b in zip(keys, keys[1:]) if a[0] <= frame <= b[0])
    t = (frame - a[0]) / (b[0] - a[0])
    t = t * t * (3 - 2 * t)
    yaw = a[1] + (b[1] - a[1]) * t
    pitch = a[2] + (b[2] - a[2]) * t
    arm.rotation_quaternion = orientation(yaw, pitch)
    arm.keyframe_insert('rotation_quaternion', frame=frame)
    samples.append({'frame': frame, 'yaw': yaw, 'pitch': pitch,
                    'needleBottom': list(tip(yaw, pitch))})

# Verify evaluated animation, not just the requested keyframe values.
for frame in range(1, 145):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    assert (arm.matrix_world.translation - pivot).length < 1e-7
    actual = min((needle.matrix_world @ v.co).z for v in needle.data.vertices)
    assert abs(actual - samples[frame - 1]['needleBottom'][2]) < 1e-6
lift = samples[97]['needleBottom'][2] - samples[89]['needleBottom'][2]
assert .003 < lift < .004
land = Vector(samples[121]['needleBottom'])
radius = math.hypot(land.x - 2.465, land.y - 1.173)
assert .109 < radius < .118, radius
assert abs(land.z - record_top - .00005) < 1e-6
arm['v139_fixed_bearing'] = True
arm['v139_max_tip_lift_mm'] = lift * 1000
out = os.path.join(ROOT, 'blender/outputs/review-v139')
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'arm-audit.json'), 'w') as f:
    json.dump({'fixedPivot': list(pivot), 'maxTipLiftMm': lift * 1000,
               'landingRadiusMeters': radius, 'recordTop': record_top,
               'samples': samples}, f, indent=2)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=target)
print('V139_ANCHORED_ARM', target, 'tip lift mm', lift * 1000, 'landing radius', radius, flush=True)
