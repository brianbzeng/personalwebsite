"""Publish the unified, expanded window beams with no supplemental strips."""

from pathlib import Path
import bpy, json, sys

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import outside_short_interactive_rays_v121 as V121

src=HERE/'outputs'/'blender'/'lofi-room-cathode-v123-window-clipped-rays.blend'
out=HERE/'outputs'/'blender'/'lofi-room-cathode-v125-unified-expanded-window-rays.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene
original=scene.camera
for ob in list(bpy.data.objects):
    if ob.name.startswith(('CATHODE_WindowRightEdgeFill_','LIGHT_WindowRightEdgeFill_')):
        bpy.data.objects.remove(ob,do_unlink=True)
scene['cathode_restyle_version']='v125'
scene['cathode_unified_expanded_window_rays_v125']=True
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))
cam=V121.qa_camera('CAM_QA_UnifiedExpandedRays_v125',(-2.70,0.20,2.35),(0.0,2.55,1.78),48.0)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v125-unified-expanded-window-rays.png'
V121.render(scene,cam,img,(1100,760))
if original: scene.camera=original
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'source':str(src),'output':str(out),'render':str(img),'supplemental_rays_removed':True,'main_rays_expanded':True}
out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('V125_REPORT='+json.dumps(report))
