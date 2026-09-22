"""User-directed pivot cleanup and continuous sleeve fade; preserve all poses."""
import bpy, os, json

assert bpy.data.filepath.endswith('v142-detailed-pivot-rest.blend')
target = os.path.join(os.path.dirname(bpy.data.filepath), 'lofi-room-cathode-glm53f-city-v143-simplified-pivot-sleeve-fade.blend')
assert not os.path.exists(target), target
scene = bpy.context.scene
removed = ['V138_Pivot_LiftShoe'] + [f'V138_Pivot_{part}{side}' for part in ('BearingCap', 'BearingScrew', 'ScrewSlot') for side in ('Left', 'Right')]
for name in removed:
    ob = bpy.data.objects[name]
    ob.hide_render = True
    ob.hide_set(True)
    ob['v143_hidden_reason'] = 'User-requested simplification; retained for recovery'

sleeve = bpy.data.objects['V138_Playback_Sleeve_Rig']
poses = []
for frame in range(1, 145):
    scene.frame_set(frame)
    poses.append((sleeve.location.copy(), sleeve.rotation_quaternion.copy(), sleeve.scale.copy(), sleeve.matrix_world.copy()))
sleeve.animation_data_clear()
for frame, (location, rotation, scale, _) in enumerate(poses, 1):
    scene.frame_set(frame)
    sleeve.location, sleeve.rotation_quaternion, sleeve.scale = location, rotation, scale
    t = max(0.0, min(1.0, (frame - 12) / 32))
    sleeve['opacity'] = 1 - t * t * (3 - 2 * t)
    for path in ('location', 'rotation_quaternion', 'scale', '["opacity"]'):
        sleeve.keyframe_insert(path, frame=frame)

max_error = 0.0
opacity = []
for frame, pose in enumerate(poses, 1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    max_error = max(max_error, max(abs(sleeve.matrix_world[r][c] - pose[3][r][c]) for r in range(4) for c in range(4)))
    opacity.append(float(sleeve['opacity']))
assert max_error < 1e-6, max_error
assert opacity[11] == 1 and opacity[12] < 1 and opacity[43] == 0
assert all(a >= b for a, b in zip(opacity, opacity[1:]))
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=target)
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blender/outputs/review-v143')
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'cleanup-audit.json'), 'w') as f:
    json.dump({'hiddenObjects': removed, 'maxSleevePoseError': max_error, 'fadeStartFrame': 12, 'fadeEndFrame': 44, 'opacity': opacity}, f, indent=2)
print('V143_CLEANUP_COMPLETE', target)
