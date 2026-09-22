"""Skew each unified beam so its right edge reaches farther into the room."""

from pathlib import Path
import bpy, json, sys
from mathutils import Vector

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import outside_short_interactive_rays_v121 as V121

src=HERE/'outputs'/'blender'/'lofi-room-cathode-v125-unified-expanded-window-rays.blend'
out=HERE/'outputs'/'blender'/'lofi-room-cathode-v126-asymmetric-right-long-rays.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene
original=scene.camera

direction=Vector((0.65,-1.0,-0.48)).normalized()
left_length=0.68
right_length=1.18
exterior_y=3.00
glass_y=2.65
travel=(exterior_y-glass_y)/abs(direction.y)
changed=[]

for ob in bpy.data.objects:
    if not ob.name.startswith('CATHODE_WindowRayVolume_') or not ob.name.endswith('_v123'):
        continue
    if ob.type!='MESH' or len(ob.data.vertices)<8:
        continue
    # create_tapered_volume stores the positive-side end corners at 5 and 6.
    # Advancing only those corners produces one continuous skewed prism—no
    # extra ray strips and no visible seams.
    delta=direction*(right_length-left_length)
    for index in (5,6):
        ob.data.vertices[index].co += delta
    ob.data.update()
    ob['cathode_left_length_v126']=left_length
    ob['cathode_right_length_v126']=right_length
    changed.append(ob.name)

for mat_name in ('CATHODE_BlindRay_ApertureClipped_v123','CATHODE_LowerRay_ApertureClipped_v123'):
    mat=bpy.data.materials.get(mat_name)
    if not mat or not mat.use_nodes: continue
    divide=next((n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeMath' and n.operation=='DIVIDE'),None)
    fade=mat.node_tree.nodes.get('CATHODE_FadeImmediatelyInside')
    if divide: divide.inputs[1].default_value=right_length
    if fade:
        fade.inputs['From Min'].default_value=travel/right_length
        fade.inputs['From Max'].default_value=1.0

# Let the driven surface lights reach the same endpoint; shadows remain enabled,
# so the monitor and desk still block illumination where they intersect it.
for ob in bpy.data.objects:
    if ob.name.startswith(('LIGHT_WindowGapBand_','LIGHT_WindowLowerPane_')) and ob.name.endswith('_v123'):
        data=ob.data
        if hasattr(data,'cutoff_distance'):
            data.cutoff_distance=1.22

scene['cathode_restyle_version']='v126'
scene['cathode_asymmetric_right_long_rays_v126']=True
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

renders={}
cam=V121.qa_camera('CAM_QA_AsymmetricWindowFront_v126',(-2.70,0.20,2.35),(0.0,2.55,1.78),48.0)
front=HERE/'outputs'/'blender'/'lofi-room-cathode-v126-asymmetric-window-front.png'
V121.render(scene,cam,front,(1100,760)); renders['front']=str(front)
cam=V121.qa_camera('CAM_QA_AsymmetricWindowDepth_v126',(-2.70,0.85,2.17),(0.30,2.28,1.58),54.0)
depth=HERE/'outputs'/'blender'/'lofi-room-cathode-v126-asymmetric-window-depth.png'
V121.render(scene,cam,depth,(1100,760)); renders['depth']=str(depth)
if original: scene.camera=original
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'source':str(src),'output':str(out),'changed':changed,'left_length':left_length,'right_length':right_length,'renders':renders}
out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('V126_REPORT='+json.dumps(report))
