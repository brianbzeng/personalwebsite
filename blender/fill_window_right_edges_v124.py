"""Fill the right-edge falloff while staying inside each window aperture."""

from pathlib import Path
import argparse, json, sys

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import outside_short_interactive_rays_v121 as V121


def parse_args():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument('--input',default=str(HERE/'outputs'/'blender'/'lofi-room-cathode-v123-window-clipped-rays.blend'))
    p.add_argument('--output',default=str(HERE/'outputs'/'blender'/'lofi-room-cathode-v124-window-right-edge-fill.blend'))
    p.add_argument('--render-dir',default=str(HERE/'outputs'/'blender'))
    return p.parse_args(argv)


def rebuild_edge_fill():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(('CATHODE_WindowRightEdgeFill_','LIGHT_WindowRightEdgeFill_')):
            bpy.data.objects.remove(ob,do_unlink=True)
    ctrl=bpy.data.objects.get('CTRL_LightningSync') or V121.lightning_controller()
    direction=Vector((0.65,-1.0,-0.48)).normalized()
    exterior_y=3.00
    glass_y=2.65
    length=0.78
    travel=(exterior_y-glass_y)/abs(direction.y)
    x_shift=direction.x*travel
    z_shift=direction.z*travel
    blind_mat=V121.faded_volume_material('CATHODE_RightEdgeBlindFill_v124',direction,length,0.0048,0.14,ctrl)
    lower_mat=V121.faded_volume_material('CATHODE_RightEdgeLowerFill_v124',direction,length,0.0034,0.078,ctrl)
    for mat in (blind_mat,lower_mat):
        fade=mat.node_tree.nodes.get('CATHODE_FadeImmediatelyInside')
        fade.inputs['From Min'].default_value=travel/length
        fade.inputs['From Max'].default_value=1.0
    gaps=[1.9325]+[1.9875+0.055*i for i in range(11)]
    made=[]
    for window,center in ((1,-1.40),(2,1.40)):
        # Center a narrow support beam just inside the right jamb. At the glass
        # it spans only the final 18 cm of the 1.30 m opening.
        target_x=center+0.545
        source_x=target_x-x_shift
        for i,target_z in enumerate(gaps):
            source_z=target_z-z_shift
            ob,_=V121.create_tapered_volume(
                f'CATHODE_WindowRightEdgeFill_W{window}_Blind_{i:02d}_v124',
                (source_x,exterior_y,source_z),direction,length,
                0.18,0.20,0.024,0.030,blind_mat,'cathode_right_edge_fill_v124')
            made.append(ob.name)
        lower_z=1.525
        source_z=lower_z-z_shift
        ob,_=V121.create_tapered_volume(
            f'CATHODE_WindowRightEdgeFill_W{window}_Lower_v124',
            (source_x,exterior_y,source_z),direction,length,
            0.18,0.20,0.70,0.72,lower_mat,'cathode_right_edge_fill_v124')
        made.append(ob.name)
        V121.create_driven_area_light(
            f'LIGHT_WindowRightEdgeFill_W{window}_v124',
            (source_x,exterior_y+0.02,source_z),direction,
            0.17,0.68,7.0,0.82,ctrl)
    return {'created':made,'target_strip_width':0.18,'inside_reach':round(length-travel,4)}


def main():
    a=parse_args()
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.input).resolve()))
    scene=bpy.context.scene
    original=scene.camera
    report=rebuild_edge_fill()
    scene['cathode_restyle_version']='v124'
    scene['cathode_window_right_edge_fill_v124']=True
    out=Path(a.output).resolve()
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    cam=V121.qa_camera('CAM_QA_WindowRightEdges_v124',(-2.70,0.20,2.35),(0.0,2.55,1.78),48.0)
    img=Path(a.render_dir).resolve()/'lofi-room-cathode-v124-window-right-edge-fill.png'
    V121.render(scene,cam,img,(1100,760))
    report['render']=str(img)
    if original: scene.camera=original
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('V124_REPORT='+json.dumps(report))


if __name__=='__main__': main()
