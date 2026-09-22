"""Targeted v108 cleanup for picture-frame corners, bed textiles, and bookshelf joins.

The approved v107 scene is the source. Existing object transforms are frozen.
Picture-frame rails are rebuilt in-place as continuous rectangular rings, the
large bookshelf outline is regenerated from its already-unioned carcass with a
centered stroke, and only the blanket's skirt vertices are eased outward enough
to clear the mattress and both cathode outlines.
"""

from pathlib import Path
import argparse
import json
import sys

import bpy
import bmesh
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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v107-roomwide-connected-sweep.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v108-frame-bed-shelf-cleanup.blend"),
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


def world_bounds(ob):
    points = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
    return (
        min(point.x for point in points), max(point.x for point in points),
        min(point.y for point in points), max(point.y for point in points),
        min(point.z for point in points), max(point.z for point in points),
    )


def set_outline_centered(outline):
    for modifier in outline.modifiers:
        if modifier.type == "WIREFRAME":
            modifier.offset = 0.0
            modifier.use_even_offset = True
    outline["cathode_centered_joint_stroke_v108"] = True


def rebuild_frame_ring(label, rail_names):
    rails = [bpy.data.objects.get(name) for name in rail_names]
    if any(rail is None for rail in rails):
        return {"assembly": label, "status": "missing"}

    anchor = rails[-1]
    frozen_matrix = anchor.matrix_world.copy()
    boxes = [world_bounds(rail) for rail in rails]
    old_mesh = anchor.data
    materials = list(old_mesh.materials)

    # The exact union of the four rail solids is a rectangular ring with no
    # overlapping corner volumes or per-piece surface seams.
    world_mesh = V106.build_axis_union_mesh(label + "_FrameRing_v108_WorldMesh", boxes)
    world_mesh.transform(frozen_matrix.inverted())
    world_mesh.name = label + "_FrameRing_v108_Mesh"
    anchor.data = world_mesh
    for material in materials:
        world_mesh.materials.append(material)
    V106.assign_cathode_face_materials(anchor)
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

    removed_models = []
    for rail in rails[:-1]:
        removed_models.append(rail.name)
        bpy.data.objects.remove(rail, do_unlink=True)

    old_outline_names = ["CATHODE_WIREFRAME_" + name for name in rail_names]
    old_outline_names.append("CATHODE_ASSEMBLY_OUTLINE_" + label)
    outline = V106.replace_outline(anchor, old_names=tuple(old_outline_names), thickness=0.01)
    set_outline_centered(outline)
    anchor["cathode_continuous_frame_ring_v108"] = True
    return {
        "assembly": label,
        "status": "continuous_ring",
        "anchor": anchor.name,
        "removed_overlapping_rails": removed_models,
        "outline": outline.name,
        "anchor_transform_unchanged": matrix_values(anchor) == tuple(
            round(value, 9) for row in frozen_matrix for value in row
        ),
        "faces": len(anchor.data.polygons),
    }


def clean_bookshelf_outline():
    shelf = bpy.data.objects.get("SHELF_Carcass_Cohesive")
    if shelf is None:
        return {"status": "missing"}
    frozen_matrix = shelf.matrix_world.copy()

    # One more limited dissolve catches any coplanar remnants imported through
    # prior mesh copies while preserving every true cubby edge and silhouette.
    bm = bmesh.new()
    bm.from_mesh(shelf.data)
    bm.normal_update()
    bmesh.ops.dissolve_limit(
        bm,
        angle_limit=0.0001,
        verts=list(bm.verts),
        edges=list(bm.edges),
        delimit={"NORMAL"},
        use_dissolve_boundaries=False,
    )
    bm.to_mesh(shelf.data)
    bm.free()
    shelf.data.update()

    outline = V106.replace_outline(
        shelf,
        old_names=("CATHODE_WIREFRAME_SHELF_Carcass_Cohesive",),
        thickness=0.01,
    )
    set_outline_centered(outline)
    shelf["cathode_joint_cleanup_v108"] = True
    return {
        "status": "cleaned_connected_carcass",
        "object": shelf.name,
        "outline": outline.name,
        "transform_unchanged": matrix_values(shelf) == tuple(
            round(value, 9) for row in frozen_matrix for value in row
        ),
        "faces": len(shelf.data.polygons),
    }


def separate_blanket_from_mattress():
    blanket = bpy.data.objects.get("BED_Blanket_FacetedContinuous")
    mattress = bpy.data.objects.get("BED_Mattress")
    if blanket is None or mattress is None:
        return {"status": "missing"}

    frozen_blanket = blanket.matrix_world.copy()
    frozen_mattress = mattress.matrix_world.copy()
    mattress_bounds = world_bounds(mattress)
    center_x = (mattress_bounds[0] + mattress_bounds[1]) * 0.5
    mattress_top = mattress_bounds[5]
    target_left = mattress_bounds[0] - 0.022
    target_right = mattress_bounds[1] + 0.022
    changed_vertices = []

    inverse = blanket.matrix_world.inverted()
    for vertex in blanket.data.vertices:
        world = blanket.matrix_world @ vertex.co
        # The entire left/right blanket boundary must sit beyond the mattress,
        # including its upper rim. Widening only the low skirt would leave the
        # sloped drape crossing through the mattress corner. Interior fold-grid
        # vertices stay untouched. Twenty-two millimeters clears both 10 mm
        # strokes while preserving physical contact across the blanket top.
        old_x = world.x
        if world.x < center_x - 0.45:
            world.x = min(world.x, target_left)
        elif world.x > center_x + 0.45:
            world.x = max(world.x, target_right)
        if abs(world.x - old_x) > 1e-7:
            vertex.co = inverse @ world
            changed_vertices.append(vertex.index)
    blanket.data.update()

    blanket_outline = V106.replace_outline(
        blanket,
        old_names=("CATHODE_WIREFRAME_BED_Blanket_FacetedContinuous",),
        thickness=0.01,
    )
    mattress_outline = bpy.data.objects.get("CATHODE_WIREFRAME_BED_Mattress")
    if mattress_outline is None:
        mattress_outline = V106.replace_outline(mattress, thickness=0.01)
    set_outline_centered(blanket_outline)
    set_outline_centered(mattress_outline)

    blanket["cathode_mattress_clearance_v108"] = 0.022
    return {
        "status": "separated_without_transform_change",
        "blanket": blanket.name,
        "mattress": mattress.name,
        "changed_skirt_vertices": changed_vertices,
        "blanket_outline": blanket_outline.name,
        "mattress_outline": mattress_outline.name,
        "blanket_transform_unchanged": matrix_values(blanket) == tuple(
            round(value, 9) for row in frozen_blanket for value in row
        ),
        "mattress_transform_unchanged": matrix_values(mattress) == tuple(
            round(value, 9) for row in frozen_mattress for value in row
        ),
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

    frames = [
        rebuild_frame_ring("PulsarFrame", (
            "ART_PulsarMap_North", "ART_PulsarMap_South",
            "ART_PulsarMap_Bottom", "ART_PulsarMap_Top",
        )),
        rebuild_frame_ring("GoldenRecordFrame", (
            "INTERACT_GoldenRecord_North", "INTERACT_GoldenRecord_South",
            "INTERACT_GoldenRecord_Bottom", "INTERACT_GoldenRecord_Top",
        )),
        rebuild_frame_ring("DiplomaFrame", (
            "INTERACT_Diploma_North", "INTERACT_Diploma_South",
            "INTERACT_Diploma_Bottom", "INTERACT_Diploma_Top",
        )),
    ]
    shelf = clean_bookshelf_outline()
    bed = separate_blanket_from_mattress()

    allowed_deleted = {
        "ART_PulsarMap_North", "ART_PulsarMap_South", "ART_PulsarMap_Bottom",
        "INTERACT_GoldenRecord_North", "INTERACT_GoldenRecord_South", "INTERACT_GoldenRecord_Bottom",
        "INTERACT_Diploma_North", "INTERACT_Diploma_South", "INTERACT_Diploma_Bottom",
    }
    changed = {}
    unexpected_deleted = []
    unchanged = 0
    for name, old_matrix in before.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            if name not in allowed_deleted:
                unexpected_deleted.append(name)
            continue
        if matrix_values(ob) != old_matrix:
            changed[name] = {"before": old_matrix, "after": matrix_values(ob)}
        else:
            unchanged += 1
    if changed or unexpected_deleted:
        raise RuntimeError("Transform/identity freeze violated: %s %s" % (changed, unexpected_deleted))

    scene["cathode_frame_bed_shelf_cleanup_v108"] = True
    scene["cathode_existing_model_transforms_changed_v108"] = 0
    scene["cathode_restyle_version"] = "v108"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "frames": qa_camera("CAM_QA_FramesClean_v108", (0.80, -1.45, 2.38),
                            (2.64, -1.57, 2.10), 68.0),
        "bed": qa_camera("CAM_QA_BedTextilesClean_v108", (0.82, -0.15, 1.62),
                         (2.04, -1.57, 0.70), 56.0),
        "shelf": qa_camera("CAM_QA_ShelfClean_v108", (0.46, -0.22, 2.20),
                           (2.44, 1.37, 1.28), 60.0),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / ("lofi-room-cathode-v108-%s-closeup.png" % label)
        render(scene, camera, path)
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v108-overview.png"
        render(scene, original_camera, overview, size=(1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "frames": frames,
        "bookshelf": shelf,
        "bed_textiles": bed,
        "transform_audit": {
            "changed": changed,
            "unexpected_deleted": unexpected_deleted,
            "unchanged_count": unchanged,
            "intentional_replaced_frame_rails": sorted(allowed_deleted),
        },
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
