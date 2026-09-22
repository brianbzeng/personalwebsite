"""Restore the greeting transform from the unchanged approved monitor start."""
import bpy,json,os
s=bpy.context.scene
assert bpy.data.filepath.endswith('v149-approved-project-covers.blend')
s.frame_set(1);bpy.context.view_layer.update()
home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
monitor=bpy.data.objects['CAM_MonitorRounded_v133']
home.animation_data_clear();home.matrix_world=monitor.matrix_world.copy()
home.data=home.data.copy();home.data.animation_data_clear()
for key in ('lens','shift_x','shift_y','sensor_width','sensor_height','sensor_fit'):
    setattr(home.data,key,getattr(monitor.data,key))
s.camera=home;s.frame_set(1);bpy.context.view_layer.update()
assert (home.matrix_world.translation-monitor.matrix_world.translation).length<1e-7
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('V149_APPROVED_GREETING_RESTORED',list(home.location),flush=True)
