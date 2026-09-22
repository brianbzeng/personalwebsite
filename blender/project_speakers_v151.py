import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
s=bpy.context.scene;s.frame_set(1)
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
c=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
for name in ('DESK_SpeakerWoofer_Left','DESK_SpeakerWoofer_Right'):
    o=bpy.data.objects.get(name)
    if o:
        # Cylinder origin is halfway through its .022m depth. Emit from the
        # visible front cap, not the origin inside the speaker housing.
        p=world_to_camera_view(s,c,o.matrix_world @ Vector((0,0,.011)))
        print('SPEAKER_ANCHOR',name,round(p.x*1920,2),round((1-p.y)*1080,2),flush=True)
