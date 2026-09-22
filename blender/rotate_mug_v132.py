"""Rotate the complete mug assembly toward the seat; preserve all other objects."""
import bpy, os, math, json
from mathutils import Vector, Matrix
s=bpy.context.scene;s.frame_set(1)
root=os.path.dirname(os.path.abspath(__file__))
out=os.path.join(root,'outputs/web-room-v132');os.makedirs(out,exist_ok=True)
target=os.path.join(root,'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v132-mug-facing-seat.blend')
assert 'v131-traveling-pulses' in bpy.data.filepath
assert not os.path.exists(target), 'Preserve existing versions'
objects=[o for o in s.objects if o.type in {'MESH','CURVE'} and 'mug' in o.name.lower()]
assert len(objects)==10
before={o.name:o.matrix_world.copy() for o in s.objects}
pivot=bpy.data.objects['DESK_Mug'].matrix_world.translation.copy()
seat=bpy.data.objects['CHAIR_Seat'].matrix_world.translation.copy()
handle=bpy.data.objects['DESK_MugHandleOuter'].matrix_world.translation.copy()
a=handle-pivot;b=seat-pivot;a.z=0;b.z=0
angle=math.atan2(b.y,b.x)-math.atan2(a.y,a.x)
rotation=Matrix.Rotation(angle,4,'Z')
transform=Matrix.Translation(pivot)@rotation@Matrix.Translation(-pivot)
for o in objects:
    assert o.parent is None and not o.animation_data
    o.matrix_world=transform@before[o.name]
bpy.context.view_layer.update()
direction=bpy.data.objects['DESK_MugHandleOuter'].matrix_world.translation-pivot;direction.z=0
assert direction.normalized().dot(b.normalized())>.99999
for o in s.objects:
    if o not in objects:assert o.matrix_world==before[o.name],o.name
# Move the existing world-space sweep coordinate system with the assembly.
m=bpy.data.materials['CATHODE_V131_Travel_mug'];n=m.node_tree.nodes
oldaxis=Vector(m['world_axis']);newaxis=rotation.to_3x3()@oldaxis
low=float(m['bounds_min'])+(pivot-rotation.to_3x3()@pivot).dot(newaxis)
n['Vector Math'].inputs[1].default_value=newaxis
n['Math'].inputs[1].default_value=low
m['world_axis']=list(newaxis);m['bounds_min']=low
s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
bpy.ops.wm.save_as_mainfile(filepath=target)
with open(os.path.join(out,'mug-audit.json'),'w') as f:json.dump({'degrees':math.degrees(angle),'objects':[o.name for o in objects],'seatAlignment':direction.normalized().dot(b.normalized()),'otherTransformsUnchanged':True},f,indent=2)
# Dedicated close-up before publishing any media.
s.camera=bpy.data.objects['CAM_QA_MugOutline_v122'];s.render.resolution_percentage=75
s.render.filepath=os.path.join(out,'mug-closeup.png');bpy.ops.render.render(write_still=True)
print('V132_MUG_READY',math.degrees(angle),flush=True)
