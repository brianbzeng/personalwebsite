"""Replace seam-producing automatic outlines with continuous boundary strokes.

The v108 model geometry and all transforms are preserved. Picture frames keep
their single-piece rings, while their visible cathode strokes are rebuilt from
only the outer and inner perimeters. The large bookshelf gets one outer stroke
plus one stroke around each true cubby opening. No construction/join edges are
included, so there is nothing left for the renderer to draw at member joints.
"""

from pathlib import Path
import argparse
import json
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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v108-frame-bed-shelf-cleanup.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v109-seamless-frame-shelf-outlines.blend"),
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


def ensure_restyle_collection():
    collection = bpy.data.collections.get("CATHODE_RESTYLE")
    if collection is None:
        collection = bpy.data.collections.new("CATHODE_RESTYLE")
        bpy.context.scene.collection.children.link(collection)
    return collection


def remove_objects(names):
    removed = []
    for name in names:
        ob = bpy.data.objects.get(name)
        if ob is not None:
            removed.append(name)
            bpy.data.objects.remove(ob, do_unlink=True)
    return removed


def loop_stroke_boxes_x(rect, front_x, stroke=0.01, depth=0.003):
    """Four overlapping cuboids forming a square-cornered Y/Z loop."""
    y0, y1, z0, z1 = rect
    half = stroke * 0.5
    x0 = front_x - depth
    x1 = front_x
    return [
        (x0, x1, y0 - half, y1 + half, z0 - half, z0 + half),
        (x0, x1, y0 - half, y1 + half, z1 - half, z1 + half),
        (x0, x1, y0 - half, y0 + half, z0 - half, z1 + half),
        (x0, x1, y1 - half, y1 + half, z0 - half, z1 + half),
    ]


def create_continuous_stroke_object(name, boxes):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    mesh = V106.build_axis_union_mesh(name + "_Mesh", boxes)
    mesh.materials.append(V106.flowing_ink_material())
    ob = bpy.data.objects.new(name, mesh)
    ensure_restyle_collection().objects.link(ob)
    for polygon in mesh.polygons:
        polygon.material_index = 0
    ob["cathode_purpose_built_continuous_stroke_v109"] = True
    ob["cathode_automatic_wireframe"] = False
    return ob


def frame_perimeters(anchor):
    points = world_points(anchor)
    ys = sorted({round(point.y, 6) for point in points})
    zs = sorted({round(point.z, 6) for point in points})
    if len(ys) != 4 or len(zs) != 4:
        raise RuntimeError("Unexpected rectangular-ring topology on %s: y=%s z=%s" % (anchor.name, ys, zs))
    outer = (ys[0], ys[3], zs[0], zs[3])
    inner = (ys[1], ys[2], zs[1], zs[2])
    front_x = min(point.x for point in points) - 0.002
    return outer, inner, front_x


def replace_frame_strokes(label, anchor_name):
    anchor = bpy.data.objects.get(anchor_name)
    if anchor is None:
        return {"assembly": label, "status": "missing"}
    outer, inner, front_x = frame_perimeters(anchor)
    boxes = loop_stroke_boxes_x(outer, front_x) + loop_stroke_boxes_x(inner, front_x)
    removed = remove_objects((
        "CATHODE_WIREFRAME_" + anchor_name,
        "CATHODE_ASSEMBLY_OUTLINE_" + label,
        "CATHODE_CLEAN_OUTLINE_" + label + "_v109",
    ))
    outline = create_continuous_stroke_object("CATHODE_CLEAN_OUTLINE_" + label + "_v109", boxes)
    anchor["cathode_no_join_lines_v109"] = True
    return {
        "assembly": label,
        "status": "outer_and_inner_perimeters_only",
        "model": anchor.name,
        "outline": outline.name,
        "removed_automatic_outlines": removed,
        "outer": outer,
        "inner": inner,
        "stroke_boxes_before_union": len(boxes),
        "stroke_faces_after_union": len(outline.data.polygons),
    }


def shelf_opening_rectangles(shelf):
    points = world_points(shelf)
    front_x = min(point.x for point in points)

    # The front carcass has four Y boundaries (outer/inner/inner/outer) and
    # alternating Z boundaries for its horizontal rails and five openings.
    front_faces = []
    for polygon in shelf.data.polygons:
        normal = (shelf.matrix_world.to_3x3() @ polygon.normal).normalized()
        face_points = [shelf.matrix_world @ shelf.data.vertices[index].co for index in polygon.vertices]
        if normal.x < -0.9 and all(abs(point.x - front_x) < 1e-5 for point in face_points):
            front_faces.extend(face_points)
    ys = sorted({round(point.y, 6) for point in front_faces})
    zs = sorted({round(point.z, 6) for point in front_faces})
    if len(ys) != 4 or len(zs) < 4 or len(zs) % 2:
        raise RuntimeError("Unexpected bookshelf front topology: y=%s z=%s" % (ys, zs))
    outer = (ys[0], ys[-1], zs[0], zs[-1])
    # Large consecutive Z gaps are the actual open cubbies; the narrow gaps
    # are the board thicknesses and must not receive their own rectangles.
    openings = [
        (ys[1], ys[2], zs[index], zs[index + 1])
        for index in range(len(zs) - 1)
        if zs[index + 1] - zs[index] > 0.20
    ]
    if len(openings) != 5:
        raise RuntimeError("Expected five bookshelf openings, found %s from z=%s" % (openings, zs))
    return outer, openings, front_x - 0.002


def replace_shelf_strokes():
    shelf = bpy.data.objects.get("SHELF_Carcass_Cohesive")
    if shelf is None:
        return {"status": "missing"}
    outer, openings, front_x = shelf_opening_rectangles(shelf)
    boxes = loop_stroke_boxes_x(outer, front_x)
    for opening in openings:
        boxes.extend(loop_stroke_boxes_x(opening, front_x))
    removed = remove_objects((
        "CATHODE_WIREFRAME_SHELF_Carcass_Cohesive",
        "CATHODE_CLEAN_OUTLINE_SHELF_Carcass_Cohesive_v109",
    ))
    outline = create_continuous_stroke_object(
        "CATHODE_CLEAN_OUTLINE_SHELF_Carcass_Cohesive_v109", boxes
    )
    shelf["cathode_no_join_lines_v109"] = True
    return {
        "status": "outer_and_cubby_boundaries_only",
        "model": shelf.name,
        "outline": outline.name,
        "removed_automatic_outlines": removed,
        "outer": outer,
        "openings": openings,
        "stroke_boxes_before_union": len(boxes),
        "stroke_faces_after_union": len(outline.data.polygons),
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


def render(scene, camera, path, size=(1200, 760)):
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

    frames = [
        replace_frame_strokes("PulsarFrame", "ART_PulsarMap_Top"),
        replace_frame_strokes("GoldenRecordFrame", "INTERACT_GoldenRecord_Top"),
        replace_frame_strokes("DiplomaFrame", "INTERACT_Diploma_Top"),
    ]
    shelf = replace_shelf_strokes()

    changed = {}
    deleted = []
    for name, old_matrix in before.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            deleted.append(name)
        elif matrix_values(ob) != old_matrix:
            changed[name] = {"before": old_matrix, "after": matrix_values(ob)}
    if changed or deleted:
        raise RuntimeError("Model freeze violated: changed=%s deleted=%s" % (changed, deleted))

    scene["cathode_seamless_frame_shelf_outlines_v109"] = True
    scene["cathode_existing_model_transforms_changed_v109"] = 0
    scene["cathode_restyle_version"] = "v109"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "frames": qa_camera("CAM_QA_SeamlessFrames_v109", (0.28, -1.47, 2.40),
                            (2.64, -1.58, 2.10), 55.0),
        "frame_left": qa_camera("CAM_QA_SeamlessFrameLeft_v109", (1.52, -0.60, 2.48),
                                (2.64, -0.88, 2.10), 76.0),
        "frame_right": qa_camera("CAM_QA_SeamlessFrameRight_v109", (1.50, -2.20, 2.47),
                                 (2.64, -2.28, 2.10), 76.0),
        "shelf": qa_camera("CAM_QA_SeamlessShelf_v109", (0.28, 0.06, 2.22),
                           (2.42, 1.36, 1.20), 55.0),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / ("lofi-room-cathode-v109-%s-closeup.png" % label)
        render(scene, camera, path)
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v109-overview.png"
        render(scene, original_camera, overview, size=(1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "frames": frames,
        "bookshelf": shelf,
        "transform_audit": {"changed": changed, "deleted": deleted, "unchanged_count": len(before)},
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
