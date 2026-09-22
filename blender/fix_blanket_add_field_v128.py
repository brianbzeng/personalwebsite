"""Eliminate blanket outline runaways, clear the mattress seam, and restore the 3D field."""

from pathlib import Path
import bpy, json, sys

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import outside_short_interactive_rays_v121 as V121
import stylize_lofi_room_cathode as STYLE

src=HERE/'outputs'/'blender'/'lofi-room-cathode-v127-wide-asymmetric-rays.blend'
out=HERE/'outputs'/'blender'/'lofi-room-cathode-v128-blanket-field.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene
original=scene.camera


def replace_blanket_outline_with_curves():
    blanket=bpy.data.objects.get('BED_Blanket_FacetedContinuous')
    mattress=bpy.data.objects.get('BED_Mattress')
    if not blanket or not mattress: return {'status':'missing'}
    old=bpy.data.objects.get('CATHODE_WIREFRAME_BED_Blanket_FacetedContinuous')
    if old: bpy.data.objects.remove(old,do_unlink=True)

    mattress_top=max((mattress.matrix_world@v.co).z for v in mattress.data.vertices)
    pts=[blanket.matrix_world@v.co for v in blanket.data.vertices]
    seam_y=min(p.y for p in pts)
    inv=blanket.matrix_world.inverted()
    lifted=[]
    for v in blanket.data.vertices:
        w=blanket.matrix_world@v.co
        # The short seam and nearby faceted top now have positive clearance.
        if w.z>mattress_top-0.065 and (w.y<seam_y+0.16 or w.z>mattress_top-0.015):
            target=mattress_top+0.022
            if w.z<target:
                w.z=target
                v.co=inv@w
                lifted.append(v.index)
    blanket.data.update()

    curve=bpy.data.curves.new('CATHODE_BlanketCleanOutline_Curve','CURVE')
    curve.dimensions='3D'
    curve.resolution_u=1
    curve.bevel_depth=0.005
    curve.bevel_resolution=0
    curve.resolution_u=1
    # Each source edge becomes a direct two-point stroke. Unlike Wireframe,
    # this cannot generate evaluated spikes beyond the actual blanket bounds.
    for edge in blanket.data.edges:
        a=blanket.matrix_world@blanket.data.vertices[edge.vertices[0]].co
        b=blanket.matrix_world@blanket.data.vertices[edge.vertices[1]].co
        if (b-a).length>0.40:  # omit only anomalously long topology connections
            continue
        spline=curve.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co=(*a,1.0)
        spline.points[1].co=(*b,1.0)
    ink=bpy.data.materials.get('CATHODE_FLOWING_WHITE_INK')
    if ink: curve.materials.append(ink)
    outline=bpy.data.objects.new('CATHODE_WIREFRAME_BED_Blanket_FacetedContinuous',curve)
    coll=bpy.data.collections.get('CATHODE_RESTYLE') or scene.collection
    coll.objects.link(outline)
    outline['cathode_spike_free_curve_outline_v128']=True
    blanket['cathode_mattress_short_seam_clearance_v128']=0.022
    return {'lifted_vertices':lifted,'outline':outline.name,'splines':len(curve.splines)}


def rebuild_field():
    coll=bpy.data.collections.get('CATHODE_EXTERIOR_SOURCE_FIELD')
    if coll:
        for ob in list(coll.objects): bpy.data.objects.remove(ob,do_unlink=True)
        bpy.data.collections.remove(coll)
    if 'cathode_full_exterior_field_source_v105' in scene:
        del scene['cathode_full_exterior_field_source_v105']
    return STYLE.build_full_exterior_field_source_v105()


report={'blanket':replace_blanket_outline_with_curves(),'field':rebuild_field()}
scene['cathode_restyle_version']='v128'
scene['cathode_blanket_field_v128']=True
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

renders={}
cam=V121.qa_camera('CAM_QA_FieldThroughWindows_v128',(-2.70,0.20,2.35),(0.0,2.60,1.55),48.0)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v128-field-through-windows.png'
V121.render(scene,cam,img,(1100,760)); renders['field']=str(img)
cam=V121.qa_camera('CAM_QA_BlanketClean_v128',(0.82,-0.15,1.62),(2.02,-1.58,0.72),60.0)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v128-blanket-clean.png'
V121.render(scene,cam,img,(1100,760)); renders['blanket']=str(img)
report['renders']=renders
if original: scene.camera=original
bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('V128_REPORT='+json.dumps(report))
