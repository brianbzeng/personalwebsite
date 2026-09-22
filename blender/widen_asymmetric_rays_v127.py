"""Widen both sides of the asymmetric rays so their soft edges hide behind the jambs."""

from pathlib import Path
import bpy, json, sys
from mathutils import Vector

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import outside_short_interactive_rays_v121 as V121

src=HERE/'outputs'/'blender'/'lofi-room-cathode-v126-asymmetric-right-long-rays.blend'
out=HERE/'outputs'/'blender'/'lofi-room-cathode-v127-wide-asymmetric-rays.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene
original=scene.camera

direction=Vector((0.65,-1.0,-0.48)).normalized()
_,side,_=V121.beam_frame(direction)
old_width=1.22
new_width=1.44
factor=new_width/old_width
changed=[]
for ob in bpy.data.objects:
    if not ob.name.startswith('CATHODE_WindowRayVolume_') or not ob.name.endswith('_v123'):
        continue
    if ob.type!='MESH': continue
    for vertex in ob.data.vertices:
        along=vertex.co.dot(side)
        vertex.co += side*(along*(factor-1.0))
    ob.data.update()
    ob['cathode_width_v127']=new_width
    changed.append(ob.name)

for ob in bpy.data.objects:
    if ob.name.startswith(('LIGHT_WindowGapBand_','LIGHT_WindowLowerPane_')) and ob.name.endswith('_v123'):
        if hasattr(ob.data,'size'):
            ob.data.size=1.40

scene['cathode_restyle_version']='v127'
scene['cathode_wide_asymmetric_rays_v127']=True
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

cam=V121.qa_camera('CAM_QA_WideAsymmetricRays_v127',(-2.70,0.20,2.35),(0.0,2.55,1.78),48.0)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v127-wide-asymmetric-rays.png'
V121.render(scene,cam,img,(1100,760))
if original: scene.camera=original
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'source':str(src),'output':str(out),'old_width':old_width,'new_width':new_width,'changed':changed,'render':str(img)}
out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('V127_REPORT='+json.dumps(report))
