"""Seam-free bedside cubby front and collision-free blinds for both windows."""

from pathlib import Path
import argparse
import json
import math
import sys

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fix_connected_models_v106 as V106


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v109-seamless-frame-shelf-outlines.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v110-cubby-thin-blinds.blend"),
    )
    parser.add_argument("--render-dir", default=str(HERE / "outputs" / "blender"))
    return parser.parse_args(argv)


def matrix_values(ob):
    return tuple(round(value, 9) for row in ob.matrix_world for value in row)


def snapshot_model_transforms():
    return {
        ob.name: matrix_values(ob)
        for ob in bpy.data.objects
        if ob.type == "MESH" and not ob.name.startswith("CATHODE_")
    }


def world_points(ob):
    return [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]


def restyle_collection():
    collection = bpy.data.collections.get("CATHODE_RESTYLE")
    if collection is None:
        collection = bpy.data.collections.new("CATHODE_RESTYLE")
        bpy.context.scene.collection.children.link(collection)
    return collection


def loop_stroke_boxes_y(rect, front_y, stroke=0.01, depth=0.003):
    """Four overlapping cuboids forming a square-cornered X/Z loop."""
    x0, x1, z0, z1 = rect
    half = stroke * 0.5
    y0, y1 = front_y, front_y + depth
    return [
        (x0 - half, x1 + half, y0, y1, z0 - half, z0 + half),
        (x0 - half, x1 + half, y0, y1, z1 - half, z1 + half),
        (x0 - half, x0 + half, y0, y1, z0 - half, z1 + half),
        (x1 - half, x1 + half, y0, y1, z0 - half, z1 + half),
    ]


def remove_object(name):
    ob = bpy.data.objects.get(name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
        return True
    return False


def clean_cubby_front():
    cubby = bpy.data.objects.get("CUBBY_Carcass_Cohesive")
    if cubby is None:
        return {"status": "missing"}
    frozen = cubby.matrix_world.copy()
    points = world_points(cubby)
    xs = sorted({round(point.x, 6) for point in points})
    zs = sorted({round(point.z, 6) for point in points})
    if len(xs) != 6 or len(zs) != 6:
        raise RuntimeError("Unexpected cubby front topology: x=%s z=%s" % (xs, zs))

    outer = (xs[0], xs[-1], zs[0], zs[-1])
    openings = [
        (x_pair[0], x_pair[1], z_pair[0], z_pair[1])
        for x_pair in ((xs[1], xs[2]), (xs[3], xs[4]))
        for z_pair in ((zs[1], zs[2]), (zs[3], zs[4]))
    ]
    front_y = max(point.y for point in points) + 0.002
    boxes = loop_stroke_boxes_y(outer, front_y)
    for opening in openings:
        boxes.extend(loop_stroke_boxes_y(opening, front_y))

    removed = []
    for name in (
        "CATHODE_WIREFRAME_CUBBY_Carcass_Cohesive",
        "CATHODE_CLEAN_OUTLINE_CUBBY_Carcass_Cohesive_v110",
    ):
        if remove_object(name):
            removed.append(name)
    mesh = V106.build_axis_union_mesh("CATHODE_CLEAN_OUTLINE_CUBBY_Carcass_Cohesive_v110_Mesh", boxes)
    mesh.materials.append(V106.flowing_ink_material())
    outline = bpy.data.objects.new("CATHODE_CLEAN_OUTLINE_CUBBY_Carcass_Cohesive_v110", mesh)
    restyle_collection().objects.link(outline)
    for polygon in mesh.polygons:
        polygon.material_index = 0
    outline["cathode_purpose_built_continuous_stroke_v110"] = True
    cubby["cathode_no_join_lines_v110"] = True
    return {
        "status": "outer_and_four_opening_boundaries_only",
        "object": cubby.name,
        "outer": outer,
        "openings": openings,
        "outline": outline.name,
        "removed_automatic_outlines": removed,
        "transform_unchanged": matrix_values(cubby) == tuple(
            round(value, 9) for row in frozen for value in row
        ),
    }


def copy_materials(materials, target):
    for material in materials:
        target.data.materials.append(material)
    V106.assign_cathode_face_materials(target)


def create_box(name, location, dimensions, rotation_x, materials):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = dimensions
    ob.rotation_euler.x = rotation_x
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    copy_materials(materials, ob)
    return ob


def rebuild_window_blinds(index):
    prefix = "WINDOW_%d_" % index
    old_slats = [
        bpy.data.objects.get(prefix + "Blind_%02d" % slat_index)
        for slat_index in range(7)
    ]
    old_slats = [slat for slat in old_slats if slat is not None]
    if not old_slats:
        return {"window": index, "status": "missing_slats"}
    source = old_slats[0]
    center_x = source.location.x
    center_y = source.location.y
    rotation_x = source.rotation_euler.x
    materials = list(source.data.materials)

    removed_slats = []
    for slat in old_slats:
        removed_slats.append(slat.name)
        remove_object("CATHODE_WIREFRAME_" + slat.name)
        bpy.data.objects.remove(slat, do_unlink=True)

    # The window mullion ends at Z=1.9125. Eleven 22 mm slats occupy only the
    # clear upper opening, from Z=1.96 through Z=2.51, leaving visible air on
    # both sides of every blade and a definite gap above the mullion.
    centers = [1.96 + 0.055 * step for step in range(11)]
    new_slats = []
    new_outlines = []
    for slat_index, center_z in enumerate(centers):
        name = prefix + "BlindThin_%02d" % slat_index
        remove_object(name)
        remove_object("CATHODE_WIREFRAME_" + name)
        slat = create_box(
            name,
            (center_x, center_y, center_z),
            (1.26, 0.050, 0.022),
            rotation_x,
            materials,
        )
        slat["cathode_thin_blind_v110"] = True
        outline = V106.replace_outline(slat, thickness=0.005)
        new_slats.append(slat.name)
        new_outlines.append(outline.name)

    # Park the wand on the room-facing surface of the right frame stile. It is
    # outside the 1.26 m slat span but still reads as attached to the window.
    wand_x = center_x + 0.70
    moved_controls = []
    for suffix in ("BlindCord", "BlindPull"):
        control = bpy.data.objects.get(prefix + suffix)
        if control is None:
            continue
        before = tuple(control.location)
        control.location.x = wand_x
        bpy.context.view_layer.update()
        outline = V106.replace_outline(control, thickness=0.005)
        # Explicitly sync after the location edit; matrix_world can otherwise
        # remain stale until the next depsgraph evaluation in background mode.
        outline.matrix_world = control.matrix_world.copy()
        moved_controls.append({
            "object": control.name,
            "from": before,
            "to": tuple(control.location),
            "outline": outline.name,
        })

    return {
        "window": index,
        "status": "eleven_thin_slats_above_mullion",
        "removed_slats": removed_slats,
        "new_slats": new_slats,
        "new_outlines": new_outlines,
        "slat_dimensions": (1.26, 0.050, 0.022),
        "slat_centers_z": centers,
        "mullion_top_z": 1.9125,
        "lowest_slat_bottom_z": centers[0] - 0.011,
        "mullion_clearance": centers[0] - 0.011 - 1.9125,
        "moved_controls": moved_controls,
        "wand_x": wand_x,
        "slat_x_range": (center_x - 0.63, center_x + 0.63),
    }


def aim_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def qa_camera(name, location, target, lens=60.0):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.cameras.new(name + "_Data")
    camera = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    camera.data.lens = lens
    aim_camera(camera, target)
    return camera


def render(scene, camera, path, size=(1100, 760)):
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    scene.frame_set(48)
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    render_dir = Path(args.render_dir).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(input_path))
    scene = bpy.context.scene
    original_camera = scene.camera
    before = snapshot_model_transforms()

    cubby = clean_cubby_front()
    windows = [rebuild_window_blinds(1), rebuild_window_blinds(2)]

    intentional_removed = {
        "WINDOW_%d_Blind_%02d" % (window, slat)
        for window in (1, 2) for slat in range(7)
    }
    intentional_moved = {
        "WINDOW_%d_%s" % (window, suffix)
        for window in (1, 2) for suffix in ("BlindCord", "BlindPull")
    }
    changed = {}
    unexpected_deleted = []
    unchanged = 0
    for name, old_matrix in before.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            if name not in intentional_removed:
                unexpected_deleted.append(name)
            continue
        if matrix_values(ob) != old_matrix:
            if name not in intentional_moved:
                changed[name] = {"before": old_matrix, "after": matrix_values(ob)}
        else:
            unchanged += 1
    if changed or unexpected_deleted:
        raise RuntimeError("Unexpected scene change: changed=%s deleted=%s" % (changed, unexpected_deleted))

    scene["cathode_cubby_thin_blinds_v110"] = True
    scene["cathode_restyle_version"] = "v110"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "cubby": qa_camera("CAM_QA_SeamlessCubby_v110", (0.72, 0.00, 1.18),
                           (0.72, -2.33, 0.60), 46.0),
        "window1": qa_camera("CAM_QA_ThinBlindsWindow1_v110", (-1.40, 0.20, 2.00),
                            (-1.40, 2.62, 1.95), 32.0),
        "window2": qa_camera("CAM_QA_ThinBlindsWindow2_v110", (1.40, 0.20, 2.00),
                            (1.40, 2.62, 1.95), 32.0),
        "window1_side": qa_camera("CAM_QA_ThinBlindsWindow1Side_v110", (0.05, 0.55, 2.05),
                                 (-0.73, 2.60, 2.05), 45.0),
        "window2_side": qa_camera("CAM_QA_ThinBlindsWindow2Side_v110", (2.85, 0.55, 2.05),
                                 (2.07, 2.60, 2.05), 45.0),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / ("lofi-room-cathode-v110-%s-closeup.png" % label)
        render(scene, camera, path)
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v110-overview.png"
        render(scene, original_camera, overview, size=(1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "cubby": cubby,
        "windows": windows,
        "audit": {
            "unexpected_transform_changes": changed,
            "unexpected_deleted": unexpected_deleted,
            "unchanged_existing_models": unchanged,
            "intentional_removed_old_slats": sorted(intentional_removed),
            "intentional_moved_controls": sorted(intentional_moved),
        },
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
