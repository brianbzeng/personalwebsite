"""Align every ray to its real aperture and stop it shortly inside the room."""

from pathlib import Path
import argparse, json, sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--input', default=str(HERE/'outputs'/'blender'/'lofi-room-cathode-v122-full-window-model-cleanup.blend'))
    p.add_argument('--output', default=str(HERE/'outputs'/'blender'/'lofi-room-cathode-v123-window-clipped-rays.blend'))
    p.add_argument('--render-dir', default=str(HERE/'outputs'/'blender'))
    return p.parse_args(argv)


def remove_lighting():
    prefixes = ('CATHODE_WindowRayVolume_', 'LIGHT_WindowGapBand_', 'LIGHT_WindowLowerPane_', 'LIGHT_WindowFull_')
    removed=[]
    for ob in list(bpy.data.objects):
        if ob.name.startswith(prefixes):
            removed.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    return removed


def rebuild():
    removed = remove_lighting()
    ctrl = bpy.data.objects.get('CTRL_LightningSync') or V121.lightning_controller()
    direction = Vector((0.65, -1.0, -0.48)).normalized()
    exterior_y = 3.00
    glass_y = 2.65
    length = 0.68
    travel_to_glass = (exterior_y-glass_y) / abs(direction.y)
    x_shift = direction.x * travel_to_glass
    z_shift = direction.z * travel_to_glass

    blind_mat = V121.faded_volume_material(
        'CATHODE_BlindRay_ApertureClipped_v123', direction, length,
        density=0.0053, emission_strength=0.155, controller=ctrl)
    lower_mat = V121.faded_volume_material(
        'CATHODE_LowerRay_ApertureClipped_v123', direction, length,
        density=0.0036, emission_strength=0.082, controller=ctrl)
    # Fade starts at the glass plane. Only the final 0.33 m exists in the room.
    for mat in (blind_mat, lower_mat):
        node = mat.node_tree.nodes.get('CATHODE_FadeImmediatelyInside')
        node.inputs['From Min'].default_value = travel_to_glass / length
        node.inputs['From Max'].default_value = 1.0

    # Exact visible gaps, including the three highest gaps that were previously
    # missed because the source Z had not accounted for the ray's downward angle.
    target_gaps = [1.9325] + [1.9875 + 0.055*i for i in range(11)]
    created=[]
    for window, aperture_x in ((1,-1.40),(2,1.40)):
        # Pull the beam two centimeters toward the aperture interior and trim
        # its width so it no longer grazes the left jamb.
        source_x = aperture_x + 0.040 - x_shift
        for i, target_z in enumerate(target_gaps):
            source_z = target_z - z_shift
            ray,_ = V121.create_tapered_volume(
                f'CATHODE_WindowRayVolume_W{window}_Blind_{i:02d}_v123',
                (source_x, exterior_y, source_z), direction, length,
                1.22, 1.22, 0.026, 0.032, blind_mat,
                'cathode_aperture_clipped_ray_v123')
            created.append(ray.name)
            V121.create_driven_area_light(
                f'LIGHT_WindowGapBand_W{window}_{i:02d}_v123',
                (source_x, exterior_y+0.02, source_z), direction,
                1.20, 0.022, 13.0, 0.72, ctrl)

        lower_target_z = 1.525
        lower_source_z = lower_target_z - z_shift
        lower,_ = V121.create_tapered_volume(
            f'CATHODE_WindowRayVolume_W{window}_LowerPane_v123',
            (source_x, exterior_y, lower_source_z), direction, length,
            1.22, 1.22, 0.70, 0.72, lower_mat,
            'cathode_aperture_clipped_ray_v123')
        created.append(lower.name)
        V121.create_driven_area_light(
            f'LIGHT_WindowLowerPane_W{window}_v123',
            (source_x, exterior_y+0.02, lower_source_z), direction,
            1.20, 0.68, 14.0, 0.72, ctrl)

    return {'removed':removed,'created':created,'length':length,'glass_y':glass_y,
            'inside_reach':round(length-travel_to_glass,4),
            'top_gap_targets':target_gaps[-3:]}


def main():
    a=parse_args()
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.input).resolve()))
    scene=bpy.context.scene
    original=scene.camera
    report=rebuild()
    scene['cathode_restyle_version']='v123'
    scene['cathode_window_aperture_clipped_rays_v123']=True
    out=Path(a.output).resolve()
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    cam=V121.qa_camera('CAM_QA_WindowClippedRays_v123',(-2.70,0.20,2.35),(0.0,2.55,1.78),48.0)
    qa=Path(a.render_dir).resolve()/'lofi-room-cathode-v123-window-clipped-rays.png'
    V121.render(scene,cam,qa,(1100,760))
    report['render']=str(qa)
    if original: scene.camera=original
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('V123_REPORT='+json.dumps(report))


if __name__=='__main__': main()
