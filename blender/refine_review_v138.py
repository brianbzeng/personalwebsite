"""Refine owned approval file after visual checks; earlier source is preserved."""
import bpy, math
from mathutils import Vector
assert bpy.data.filepath.endswith('v138-player-book-review.blend')
for m in bpy.data.materials:
    if m.name.startswith('V138_') and m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:
            p.inputs['Emission Color'].default_value=p.inputs['Base Color'].default_value
            p.inputs['Emission Strength'].default_value=.8
bs=bpy.data.scenes['V138_Book_Prototypes']
for name,x in [('Hardback',0),('Paperback',.26)]:
    root=bpy.data.objects['V138_'+name+'_Root'];root.animation_data_clear()
    for f,dx in ((1,0),(12,0),(30,-.035),(240,-.035)):
        root.location=(x+dx,0,0);root.keyframe_insert('location',frame=f)
c=bs.camera;c.location=(.42,-.64,.35);c.rotation_euler=(Vector((.12,0,0))-c.location).to_track_quat('-Z','Y').to_euler()
arm=bpy.data.objects['V138_Tonearm_Rig']
for f in (122,144):
    bpy.context.scene.frame_set(f);arm.location.z=1.4935;arm.keyframe_insert('location',frame=f)
c=bpy.data.objects['CAM_V138_BookStack_Review'];c.location=(1.52,1.06,2.28);c.rotation_euler=(Vector((2.4,1.06,1.95))-c.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.frame_set(1);bs.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
