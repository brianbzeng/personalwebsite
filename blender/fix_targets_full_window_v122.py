"""Full-window rays plus camera, bed, mug-outline, and mouse cleanup."""

from pathlib import Path
import argparse, json, sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import outside_short_interactive_rays_v121 as V121
import fix_connected_models_v106 as V106


def args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--input', default=str(HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v121-outside-short-interactive-rays.blend'))
    p.add_argument('--output', default=str(HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v122-full-window-model-cleanup.blend'))
    p.add_argument('--render-dir', default=str(HERE / 'outputs' / 'blender'))
    return p.parse_args(argv)


def remove_prefix(prefix):
    for ob in list(bpy.data.objects):
        if ob.name.startswith(prefix):
            bpy.data.objects.remove(ob, do_unlink=True)


def rebuild_full_window_rays(controller):
    for prefix in ('CATHODE_WindowRayVolume_', 'LIGHT_WindowGapBand_', 'LIGHT_WindowLowerPane_', 'LIGHT_WindowFull_'):
        remove_prefix(prefix)

    direction = Vector((0.65, -1.0, -0.48)).normalized()
    length = 1.00
    exterior_y = 3.00
    blind_mat = V121.faded_volume_material(
        'CATHODE_BlindRay_FullCoverage_v122', direction, length,
        density=0.0052, emission_strength=0.15, controller=controller)
    lower_mat = V121.faded_volume_material(
        'CATHODE_LowerRay_FullCoverage_v122', direction, length,
        density=0.0037, emission_strength=0.082, controller=controller)

    # The first and last slots deliberately overlap the frame opening slightly,
    # so the visible light begins outside and no dark seam remains at any edge.
    gap_z = [1.89 + 0.055 * i for i in range(13)]
    made = []
    for window, x in ((1, -1.40), (2, 1.40)):
        for index, z in enumerate(gap_z):
            ob, _ = V121.create_tapered_volume(
                f'CATHODE_WindowRayVolume_W{window}_Blind_{index:02d}_v122',
                (x, exterior_y, z), direction, length,
                2.20, 2.26, 0.061, 0.070, blind_mat,
                'cathode_full_window_short_fade_v122')
            made.append(ob.name)
            V121.create_driven_area_light(
                f'LIGHT_WindowGapBand_W{window}_{index:02d}_v122',
                (x, 3.02, z), direction, 1.34, 0.050, 14.0, 1.08, controller)
        lower, _ = V121.create_tapered_volume(
            f'CATHODE_WindowRayVolume_W{window}_LowerPane_v122',
            (x, exterior_y, 1.42), direction, length,
            2.20, 2.26, 1.08, 1.14, lower_mat,
            'cathode_full_window_short_fade_v122')
        made.append(lower.name)
        V121.create_driven_area_light(
            f'LIGHT_WindowFull_W{window}_v122', (x, 3.02, 1.84), direction,
            1.34, 1.50, 25.0, 1.12, controller)
    return made


def simple_box_mesh(name, dims):
    x, y, z = (d * 0.5 for d in dims)
    verts = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def clean_camera_body():
    body = bpy.data.objects.get('SHELF_Camera_Body')
    if body is None:
        return 'missing'
    dims = body.dimensions.copy()
    old = body.data
    mats = list(old.materials)
    body.data = simple_box_mesh('SHELF_Camera_Body_Clean', dims)
    for mat in mats:
        body.data.materials.append(mat)
    # A plain six-face body removes only the two unwanted diagonal front seams.
    outline = V106.replace_outline(body, thickness=0.006)
    for mod in outline.modifiers:
        if mod.type == 'WIREFRAME':
            mod.offset = 0.0
    if old.users == 0:
        bpy.data.meshes.remove(old)
    body['cathode_diagonal_seams_removed_v122'] = True
    return body.name


def clean_blanket_and_outline():
    blanket = bpy.data.objects.get('BED_Blanket_FacetedContinuous')
    mattress = bpy.data.objects.get('BED_Mattress')
    if not blanket or not mattress:
        return {'status': 'missing'}
    bcoords = [blanket.matrix_world @ v.co for v in blanket.data.vertices]
    y_min, y_max = min(v.y for v in bcoords), max(v.y for v in bcoords)
    mattress_top = max((mattress.matrix_world @ v.co).z for v in mattress.data.vertices)
    inv = blanket.matrix_world.inverted()
    changed = []
    for v in blanket.data.vertices:
        w = blanket.matrix_world @ v.co
        # Lift both short-end top rims just above the mattress. Low drape
        # vertices remain untouched, preserving the blanket's hanging shape.
        if (abs(w.y - y_min) < 0.045 or abs(w.y - y_max) < 0.045) and w.z > mattress_top - 0.10:
            target = mattress_top + 0.014
            if w.z < target:
                w.z = target
                v.co = inv @ w
                changed.append(v.index)
    blanket.data.update()
    outline = V106.replace_outline(
        blanket,
        old_names=('CATHODE_WIREFRAME_BED_Blanket_FacetedContinuous',),
        thickness=0.010)
    for mod in outline.modifiers:
        if mod.type == 'WIREFRAME':
            mod.offset = 0.0
    blanket['cathode_short_end_clearance_v122'] = 0.014
    return {'changed': changed, 'outline': outline.name}


def clean_mug_outline():
    old = bpy.data.objects.get('CATHODE_ASSEMBLY_OUTLINE_DeskMug')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    created = []
    for name in ('DESK_Mug', 'DESK_MugHandleLower', 'DESK_MugHandleOuter', 'DESK_MugHandleUpper'):
        ob = bpy.data.objects.get(name)
        if ob:
            outline = V106.replace_outline(ob, thickness=0.007)
            for mod in outline.modifiers:
                if mod.type == 'WIREFRAME':
                    mod.offset = 0.0
            created.append(outline.name)
    return created


def gray_material():
    mouse = bpy.data.objects.get('DESK_Mouse')
    if mouse and mouse.data.materials:
        return mouse.data.materials[0]
    for name in ('CATHODE_MID', 'CATHODE_MAT_MID', 'Room_Mid', 'MAT_Mid'):
        mat = bpy.data.materials.get(name)
        if mat:
            return mat
    mat = bpy.data.materials.new('CATHODE_MouseSolidGray_v122')
    mat.diffuse_color = (0.32, 0.32, 0.32, 1.0)
    return mat


def box_object(name, center, dims, material):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    ob = bpy.data.objects.new(name, simple_box_mesh(name, dims))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = center
    ob.data.materials.append(material)
    return ob


def solid_mouse_top():
    mat = gray_material()
    for name in ('DESK_Mouse_Wheel', 'DESK_Mouse_ButtonSplit'):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
    for name in ('CATHODE_WIREFRAME_DESK_Mouse_Wheel', 'CATHODE_WIREFRAME_DESK_Mouse_ButtonSplit'):
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)

    # The center button is now a filled rectangular cap running to the end of
    # the shell; the separator terminates at its rear edge instead of crossing it.
    middle = box_object('DESK_Mouse_MiddleButton', (0.57, 2.095, 0.906), (0.034, 0.075, 0.008), mat)
    split = box_object('DESK_Mouse_ButtonSplit', (0.57, 2.151, 0.904), (0.008, 0.037, 0.007), mat)
    created = []
    for ob in (middle, split):
        outline = V106.replace_outline(ob, thickness=0.0045)
        for mod in outline.modifiers:
            if mod.type == 'WIREFRAME':
                mod.offset = 0.0
        created.extend((ob.name, outline.name))
    return created


def render(scene, name, location, target, lens, path):
    cam = V121.qa_camera(name, location, target, lens)
    V121.render(scene, cam, path, (1000, 720))
    return str(path)


def main():
    a = args()
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.input).resolve()))
    scene = bpy.context.scene
    original_camera = scene.camera
    controller = bpy.data.objects.get('CTRL_LightningSync') or V121.lightning_controller()
    report = {
        'rays': rebuild_full_window_rays(controller),
        'camera': clean_camera_body(),
        'blanket': clean_blanket_and_outline(),
        'mug_outlines': clean_mug_outline(),
        'mouse': solid_mouse_top(),
    }
    scene['cathode_restyle_version'] = 'v122'
    scene['cathode_full_window_model_cleanup_v122'] = True
    bpy.context.view_layer.update()
    out = Path(a.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))

    rd = Path(a.render_dir).resolve()
    report['renders'] = {
        'window': render(scene, 'CAM_QA_FullWindow_v122', (-2.70, 0.20, 2.35), (0.0, 2.55, 1.78), 48.0, rd / 'lofi-room-cathode-v122-full-window.png'),
        'models': render(scene, 'CAM_QA_CameraBedMouse_v122', (-2.55, -0.65, 2.28), (1.10, 1.05, 1.05), 52.0, rd / 'lofi-room-cathode-v122-model-cleanup.png'),
        'bed': render(scene, 'CAM_QA_BedShortEnds_v122', (0.82, -0.15, 1.62), (2.02, -1.58, 0.72), 60.0, rd / 'lofi-room-cathode-v122-bed-short-ends.png'),
        'mouse': render(scene, 'CAM_QA_MouseSolidTop_v122', (-0.42, 1.05, 1.58), (0.57, 2.06, 0.89), 70.0, rd / 'lofi-room-cathode-v122-mouse-solid-top.png'),
        'mug': render(scene, 'CAM_QA_MugOutline_v122', (0.20, 1.38, 1.55), (1.10, 2.48, 0.94), 70.0, rd / 'lofi-room-cathode-v122-mug-outline.png'),
    }
    if original_camera:
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('V122_REPORT=' + json.dumps(report))


if __name__ == '__main__':
    main()
