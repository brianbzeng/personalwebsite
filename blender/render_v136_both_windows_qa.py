"""Render the v136 exterior through both room windows for final visual QA."""

from pathlib import Path
import bpy, sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121

blend = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v136-deep-bay-parallel-bridge.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend))
scene = bpy.context.scene
original = scene.camera

camera = V121.qa_camera('CAM_QA_BothWindows_v136', (0.0, -.85, 1.82), (0.0, 3.65, 1.90), 58)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v136-both-windows.png'
V121.render(scene, camera, image, (1500, 900))
if original:
    scene.camera = original
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
print('BOTH_WINDOWS_QA=' + str(image))
