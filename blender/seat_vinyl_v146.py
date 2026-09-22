"""Seat viewer-right decorative sleeve against its neighbor without outline overlap."""
import bpy, os, json
from mathutils import Vector
assert bpy.data.filepath.endswith('v145-lit-player-wireframe.blend')
target=os.path.join(os.path.dirname(bpy.data.filepath),'lofi-room-cathode-glm53f-city-v146-seated-blank-vinyl.blend')
assert not os.path.exists(target)
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['INTERACT_Vinyl_0'];neighbor=bpy.data.objects['INTERACT_Vinyl_1']
wire=bpy.data.objects['PROJECT_VINYL_V126_Outline_0'];neighbor_wire=bpy.data.objects['PROJECT_VINYL_V126_Outline_1']
def bounds(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    p=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
    return [[min(v[i] for v in p),max(v[i] for v in p)] for i in range(3)]
before={o.name:list(v for row in o.matrix_world for v in row) for o in s.objects}
angle=tuple(body.rotation_euler)
old_gap=bounds(neighbor_wire)[1][0]-bounds(wire)[1][1]
dz=bounds(neighbor)[2][0]-bounds(body)[2][0]
dy=old_gap-.00015
delta=Vector((0,dy,dz))
# Children include all outline/art/record details, so one source transform moves
# the assembly coherently without touching its hover controller or neighbor.
body.location+=body.parent.matrix_world.inverted().to_3x3()@delta
bpy.context.view_layer.update()
changed={body.name,*[o.name for o in body.children_recursive]}
assert all(before[o.name]==list(v for row in o.matrix_world for v in row) for o in s.objects if o.name not in changed)
assert tuple(body.rotation_euler)==angle
samples=[]
for frame in (1,42,88,122,144,240,277):
    s.frame_set(frame);bpy.context.view_layer.update()
    gap=bounds(neighbor_wire)[1][0]-bounds(wire)[1][1]
    foot=bounds(body)[2][0]-bounds(neighbor)[2][0]
    assert .00010<gap<.00020,(frame,gap)
    assert abs(foot)<1e-6,(frame,foot)
    samples.append({'frame':frame,'outlineGap':gap,'footHeightDifference':foot})
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=target)
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'blender/outputs/review-v146');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'contact-audit.json'),'w') as f:json.dump({'source':body.name,'neighbor':neighbor.name,'previousGapMeters':old_gap,'translationMeters':list(delta),'leanPreserved':True,'onlyAssemblyChanged':True,'samples':samples},f,indent=2)
print('V146_VINYL_SEATED',dy,dz)
