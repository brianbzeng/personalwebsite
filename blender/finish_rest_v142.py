"""Refine the owned v142 socket/post ratio after close-up inspection."""
import bpy
assert bpy.data.filepath.endswith('v142-detailed-pivot-rest.blend')
bpy.context.scene.frame_set(1)
base=bpy.data.objects['V138_ArmRest_Base'];base.dimensions.z=.0185;base.location.z=1.415+.00925
bpy.data.objects['V138_ArmRest_SocketLip'].location.z=1.415+.0186
top=bpy.data.objects['V138_Tonearm_Rig'].location.z-.0051
post=bpy.data.objects['V138_ArmRest_Post'];post.dimensions.z=top-1.415-.0185;post.location.z=(top+1.415+.0185)/2
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
