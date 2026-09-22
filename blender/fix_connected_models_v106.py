# -*- coding: utf-8 -*-
"""Targeted v106 cleanup for the bedside cubby, desk chair, and floor plant.

This pass intentionally leaves every other model and all window/rain work alone.
It starts from the approved v104 stage, aligns the cubby with the bed's wall
plane, seats the chair wheel outlines on the floor, and replaces overlapping
component outlines on the cubby and floor plant with genuinely connected
geometry.
"""

from pathlib import Path
import argparse
import json
import math
import sys

import bpy
import bmesh
from mathutils import Vector


HERE = Path(__file__).resolve().parent


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v104-viewport-visible-stage.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v106-connected-cubby-plant.blend"),
    )
    parser.add_argument(
        "--render-dir",
        default=str(HERE / "outputs" / "blender"),
    )
    return parser.parse_args(argv)


def mesh_world_points(ob, evaluated=False):
    if evaluated:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated_ob = ob.evaluated_get(depsgraph)
        mesh = evaluated_ob.to_mesh()
        try:
            return [evaluated_ob.matrix_world @ vertex.co for vertex in mesh.vertices]
        finally:
            evaluated_ob.to_mesh_clear()
    return [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]


def world_bounds(ob, evaluated=False):
    points = mesh_world_points(ob, evaluated=evaluated)
    return (
        min(point.x for point in points), max(point.x for point in points),
        min(point.y for point in points), max(point.y for point in points),
        min(point.z for point in points), max(point.z for point in points),
    )


def connected_component_bounds(ob):
    vertices = ob.data.vertices
    adjacency = [set() for _ in vertices]
    for edge in ob.data.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)

    seen = set()
    bounds = []
    for start in range(len(vertices)):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = []
        while stack:
            index = stack.pop()
            component.append(index)
            for neighbor in adjacency[index]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        points = [ob.matrix_world @ vertices[index].co for index in component]
        bounds.append((
            min(point.x for point in points), max(point.x for point in points),
            min(point.y for point in points), max(point.y for point in points),
            min(point.z for point in points), max(point.z for point in points),
        ))
    return bounds


def build_axis_union_mesh(name, boxes):
    """Build the exact exterior boundary of a union of axis-aligned boxes."""
    xs = sorted(set(round(value, 7) for box in boxes for value in box[0:2]))
    ys = sorted(set(round(value, 7) for box in boxes for value in box[2:4]))
    zs = sorted(set(round(value, 7) for box in boxes for value in box[4:6]))

    occupied = set()
    for ix in range(len(xs) - 1):
        cx = (xs[ix] + xs[ix + 1]) * 0.5
        for iy in range(len(ys) - 1):
            cy = (ys[iy] + ys[iy + 1]) * 0.5
            for iz in range(len(zs) - 1):
                cz = (zs[iz] + zs[iz + 1]) * 0.5
                if any(
                    box[0] - 1e-6 <= cx <= box[1] + 1e-6
                    and box[2] - 1e-6 <= cy <= box[3] + 1e-6
                    and box[4] - 1e-6 <= cz <= box[5] + 1e-6
                    for box in boxes
                ):
                    occupied.add((ix, iy, iz))

    vertices = []
    vertex_map = {}
    faces = []

    def vertex_index(coordinate):
        key = tuple(round(value, 7) for value in coordinate)
        if key not in vertex_map:
            vertex_map[key] = len(vertices)
            vertices.append(key)
        return vertex_map[key]

    def add_face(coordinates):
        faces.append(tuple(vertex_index(coordinate) for coordinate in coordinates))

    for ix, iy, iz in occupied:
        x0, x1 = xs[ix], xs[ix + 1]
        y0, y1 = ys[iy], ys[iy + 1]
        z0, z1 = zs[iz], zs[iz + 1]
        if (ix - 1, iy, iz) not in occupied:
            add_face(((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)))
        if (ix + 1, iy, iz) not in occupied:
            add_face(((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)))
        if (ix, iy - 1, iz) not in occupied:
            add_face(((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)))
        if (ix, iy + 1, iz) not in occupied:
            add_face(((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)))
        if (ix, iy, iz - 1) not in occupied:
            add_face(((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)))
        if (ix, iy, iz + 1) not in occupied:
            add_face(((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Remove only coplanar cell boundaries. The silhouette, cubby openings,
    # shelf fronts, and every actual right-angle corner remain intact.
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    for _ in range(4):
        coplanar = [
            edge for edge in bm.edges
            if len(edge.link_faces) == 2
            and edge.link_faces[0].normal.dot(edge.link_faces[1].normal) > 0.999999
        ]
        if not coplanar:
            break
        bmesh.ops.dissolve_edges(bm, edges=coplanar, use_verts=True, use_face_split=False)
        bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def assign_cathode_face_materials(ob):
    """Match the source room convention: dark upward planes, gray elsewhere."""
    for polygon in ob.data.polygons:
        normal = (ob.matrix_world.to_3x3() @ polygon.normal).normalized()
        polygon.material_index = 1 if normal.z > 0.6 and len(ob.data.materials) > 1 else 0


def flowing_ink_material():
    material = bpy.data.materials.get("CATHODE_FLOWING_WHITE_INK")
    if material is None:
        raise RuntimeError("Missing CATHODE_FLOWING_WHITE_INK material")
    return material


def replace_outline(source, old_names=(), remove_end_caps=False, thickness=0.01):
    for name in set(old_names) | {"CATHODE_WIREFRAME_" + source.name}:
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)

    outline = bpy.data.objects.new("CATHODE_WIREFRAME_" + source.name, source.data.copy())
    collection = bpy.data.collections.get("CATHODE_RESTYLE")
    if collection is None:
        collection = bpy.data.collections.new("CATHODE_RESTYLE")
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(outline)
    outline.matrix_world = source.matrix_world.copy()
    if remove_end_caps and outline.data.polygons:
        bm = bmesh.new()
        bm.from_mesh(outline.data)
        bm.faces.ensure_lookup_table()
        centers = [outline.matrix_world @ face.calc_center_median() for face in bm.faces]
        bottom_face = min(range(len(centers)), key=lambda index: centers[index].z)
        top_face = max(range(len(centers)), key=lambda index: centers[index].z)
        bmesh.ops.delete(
            bm,
            geom=[bm.faces[bottom_face], bm.faces[top_face]],
            context="FACES_ONLY",
        )
        bm.to_mesh(outline.data)
        bm.free()
        outline.data.update()
    outline.data.materials.clear()
    outline.data.materials.append(flowing_ink_material())
    wire = outline.modifiers.new("Roomwide connected outline", "WIREFRAME")
    wire.thickness = thickness
    wire.offset = 1.0
    wire.use_even_offset = True
    wire.use_replace = True
    # Open-ended stem outlines deliberately omit boundary rings, so the stem
    # flows into the soil and leaf instead of advertising two rectangular caps.
    wire.use_boundary = not remove_end_caps
    depth = outline.modifiers.new("Roomwide outline depth", "SOLIDIFY")
    depth.thickness = 0.002
    depth.offset = 0.0
    outline["cathode_connected_outline_v106"] = True
    return outline


def rebuild_and_align_cubby():
    cubby = bpy.data.objects.get("CUBBY_Carcass_Cohesive")
    bed = bpy.data.objects.get("BED_Frame_Carcass_Cohesive")
    if cubby is None or bed is None:
        raise RuntimeError("Missing cubby or bed frame")

    old_bounds = world_bounds(cubby)
    bed_bounds = world_bounds(bed)
    delta_y = bed_bounds[2] - old_bounds[2]
    boxes = []
    for box in connected_component_bounds(cubby):
        boxes.append((box[0], box[1], box[2] + delta_y, box[3] + delta_y, box[4], box[5]))

    old_mesh = cubby.data
    cubby.data = build_axis_union_mesh("CUBBY_Carcass_Connected_v106_Mesh", boxes)
    cubby.matrix_world.identity()
    for material in old_mesh.materials:
        cubby.data.materials.append(material)
    assign_cathode_face_materials(cubby)
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    outline = replace_outline(
        cubby,
        old_names=("CATHODE_WIREFRAME_CUBBY_Carcass_Cohesive",),
    )
    cubby["cathode_connected_carcass_v106"] = True
    cubby["cathode_aligned_to_bed_wall_plane_v106"] = True
    cubby["cathode_alignment_delta_y_v106"] = delta_y
    return {
        "object": cubby.name,
        "outline": outline.name,
        "delta_y": round(delta_y, 6),
        "old_bounds": [round(value, 6) for value in old_bounds],
        "new_bounds": [round(value, 6) for value in world_bounds(cubby)],
        "bed_wall_plane_y": round(bed_bounds[2], 6),
        "components_replaced": len(boxes),
    }


def seat_chair_wheels():
    floor = bpy.data.objects.get("ARCH_Floor")
    wheel_outlines = [
        ob for ob in bpy.data.objects
        if ob.name.startswith("CATHODE_WIREFRAME_CHAIR_Wheel_") and ob.type == "MESH"
    ]
    if floor is None or not wheel_outlines:
        raise RuntimeError("Missing floor or chair wheel outlines")

    floor_top = world_bounds(floor)[5]
    old_min = min(world_bounds(ob, evaluated=True)[4] for ob in wheel_outlines)
    target_min = floor_top + 0.001
    delta_z = target_min - old_min
    moved = []
    for ob in bpy.data.objects:
        if ob.name.startswith(("CHAIR_", "CATHODE_WIREFRAME_CHAIR_")):
            ob.matrix_world.translation.z += delta_z
            moved.append(ob.name)

    bpy.context.view_layer.update()
    new_min = min(world_bounds(ob, evaluated=True)[4] for ob in wheel_outlines)
    bpy.context.scene["cathode_chair_wheel_seating_v106"] = True
    return {
        "moved_objects": moved,
        "delta_z": round(delta_z, 6),
        "floor_top": round(floor_top, 6),
        "old_outline_min_z": round(old_min, 6),
        "new_outline_min_z": round(new_min, 6),
        "clearance": round(new_min - floor_top, 6),
    }


def extend_stem_bottom(ob, target_z=0.432, entry_radius=0.052):
    """Sink and separate stem entries so they emerge naturally from the soil."""
    if not ob.data.polygons:
        return 0.0
    world_matrix = ob.matrix_world
    centers = [world_matrix @ polygon.center for polygon in ob.data.polygons]
    bottom_index = min(range(len(centers)), key=lambda index: centers[index].z)
    top_index = max(range(len(centers)), key=lambda index: centers[index].z)
    bottom_center = centers[bottom_index]
    top_center = centers[top_index]
    radial = Vector((top_center.x + 2.27, top_center.y + 2.27, 0.0))
    if radial.length < 1e-8:
        radial = Vector((1.0, 0.0, 0.0))
    else:
        radial.normalize()
    target = Vector((-2.27, -2.27, target_z)) + radial * entry_radius
    target.z = target_z
    if bottom_center.z <= target_z and (bottom_center - target).length < 1e-6:
        return 0.0
    delta_world = target - bottom_center
    delta_local = world_matrix.inverted().to_3x3() @ delta_world
    for vertex_index in ob.data.polygons[bottom_index].vertices:
        ob.data.vertices[vertex_index].co += delta_local
    ob.data.update()
    return delta_world.length


def build_connected_plant_pot(body, rim, soil):
    """Create one continuous low-poly pot, lip, inner wall, and soil surface."""
    body_bounds = world_bounds(body)
    rim_bounds = world_bounds(rim)
    soil_bounds = world_bounds(soil)
    center_x = (body_bounds[0] + body_bounds[1]) * 0.5
    center_y = (body_bounds[2] + body_bounds[3]) * 0.5
    bottom_half = (body_bounds[1] - body_bounds[0]) * 0.5 - 0.05
    body_top_half = (body_bounds[1] - body_bounds[0]) * 0.5
    rim_outer_half = (rim_bounds[1] - rim_bounds[0]) * 0.5
    rim_inner_half = (soil_bounds[1] - soil_bounds[0]) * 0.5 + 0.008
    bottom_z = body_bounds[4]
    shoulder_z = rim_bounds[4]
    rim_top_z = rim_bounds[5]
    soil_z = max(soil_bounds[5], shoulder_z + 0.006)

    vertices = []
    faces = []

    def add_ring(half, z):
        start = len(vertices)
        vertices.extend((
            (center_x - half, center_y - half, z),
            (center_x + half, center_y - half, z),
            (center_x + half, center_y + half, z),
            (center_x - half, center_y + half, z),
        ))
        return [start + index for index in range(4)]

    def bridge(lower, upper, reverse=False):
        for index in range(4):
            nxt = (index + 1) % 4
            if reverse:
                faces.append((lower[index], upper[index], upper[nxt], lower[nxt]))
            else:
                faces.append((lower[index], lower[nxt], upper[nxt], upper[index]))

    bottom = add_ring(bottom_half, bottom_z)
    body_top = add_ring(body_top_half, shoulder_z)
    rim_outer_bottom = add_ring(rim_outer_half, shoulder_z)
    rim_outer_top = add_ring(rim_outer_half, rim_top_z)
    rim_inner_top = add_ring(rim_inner_half, rim_top_z)
    soil_ring = add_ring(rim_inner_half, soil_z)

    faces.append(tuple(reversed(bottom)))
    bridge(bottom, body_top)
    # Horizontal shoulder from the tapered body to the slightly wider lip.
    for index in range(4):
        nxt = (index + 1) % 4
        faces.append((body_top[index], rim_outer_bottom[index],
                      rim_outer_bottom[nxt], body_top[nxt]))
    bridge(rim_outer_bottom, rim_outer_top)
    # Continuous top lip.
    for index in range(4):
        nxt = (index + 1) % 4
        faces.append((rim_outer_top[index], rim_outer_top[nxt],
                      rim_inner_top[nxt], rim_inner_top[index]))
    # Inner wall drops cleanly to the soil surface; the soil is the final cap.
    bridge(rim_inner_top, soil_ring, reverse=True)
    faces.append(tuple(soil_ring))

    mesh = bpy.data.meshes.new("FLOOR_PlantPot_Connected_v106_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    pot = bpy.data.objects.new("FLOOR_PlantPot_Connected_v106", mesh)
    bpy.context.scene.collection.objects.link(pot)
    for material in body.data.materials:
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.material_index = 1 if polygon.normal.z > 0.6 and len(mesh.materials) > 1 else 0
    pot["cathode_connected_pot_rim_soil_v106"] = True
    return pot


def join_floor_plant():
    body = bpy.data.objects.get("FLOOR_PlantPot_Body")
    rim = bpy.data.objects.get("FLOOR_PlantPot_Rim")
    soil = bpy.data.objects.get("FLOOR_PlantPot_Soil")
    if body is None or rim is None or soil is None:
        raise RuntimeError("Missing floor plant pot components")

    old_outline_names = [
        ob.name for ob in list(bpy.data.objects)
        if ob.name.startswith("CATHODE_WIREFRAME_FLOOR_Plant")
    ]
    for name in old_outline_names:
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)

    pot = build_connected_plant_pot(body, rim, soil)
    for old in (body, rim, soil):
        bpy.data.objects.remove(old, do_unlink=True)
    pot_outline = replace_outline(pot)

    extended = {}
    stem_outlines = []
    leaf_outlines = []
    for source in sorted(
        (ob for ob in bpy.data.objects if ob.type == "MESH" and ob.name.startswith("FLOOR_Plant_")),
        key=lambda ob: ob.name,
    ):
        if source.name.startswith("FLOOR_Plant_Stem_"):
            extended[source.name] = round(extend_stem_bottom(source), 6)
            stem_outlines.append(
                replace_outline(source, remove_end_caps=True, thickness=0.006).name
            )
            source["cathode_stem_caps_hidden_v106"] = True
        elif source.name.startswith("FLOOR_Plant_Leaf_"):
            leaf_outlines.append(replace_outline(source).name)

    return {
        "pot_object": pot.name,
        "pot_outline": pot_outline.name,
        "source_outline_objects_removed": old_outline_names,
        "stem_extensions": extended,
        "stem_outlines_without_end_caps": stem_outlines,
        "leaf_outlines_preserved": leaf_outlines,
        "pot_bounds": [round(value, 6) for value in world_bounds(pot)],
        "visual_connection_strategy": "continuous pot/rim/soil + stems sunk below soil + no stem cap outlines",
    }


def aim_camera(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def ensure_camera(name, location, target, lens=55.0):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.cameras.new(name + "_Data")
    camera = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    camera.data.lens = lens
    camera.data.sensor_width = 36.0
    aim_camera(camera, target)
    return camera


def render_camera(scene, camera, path, resolution=(900, 700)):
    scene.camera = camera
    # Blender 5.2 exposes Eevee under the BLENDER_EEVEE identifier.
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    scene.render.film_transparent = False
    scene.frame_set(48)
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    render_dir = Path(args.render_dir).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    bpy.ops.wm.open_mainfile(filepath=str(input_path))
    scene = bpy.context.scene
    original_camera = scene.camera
    cubby_report = rebuild_and_align_cubby()
    chair_report = seat_chair_wheels()
    plant_report = join_floor_plant()
    scene["cathode_targeted_connected_models_v106"] = True
    scene["cathode_source_file_v106"] = str(input_path)
    scene["cathode_restyle_version"] = "v106"
    bpy.context.view_layer.update()

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cubby_camera = ensure_camera(
        "CAM_QA_CubbyConnected_v106",
        (-0.15, -1.20, 1.65),
        (0.72, -2.50, 0.58),
        lens=62.0,
    )
    plant_camera = ensure_camera(
        "CAM_QA_PlantConnected_v106",
        (-1.05, -1.00, 1.60),
        (-2.27, -2.27, 0.58),
        lens=68.0,
    )
    chair_camera = ensure_camera(
        "CAM_QA_ChairSeated_v106",
        (-0.10, -0.15, 0.72),
        (0.0, 1.34, 0.22),
        lens=62.0,
    )
    render_camera(scene, cubby_camera, render_dir / "lofi-room-cathode-v106-cubby-closeup.png")
    render_camera(scene, plant_camera, render_dir / "lofi-room-cathode-v106-plant-closeup.png")
    render_camera(scene, chair_camera, render_dir / "lofi-room-cathode-v106-chair-closeup.png")
    if original_camera is not None:
        render_camera(
            scene,
            original_camera,
            render_dir / "lofi-room-cathode-v106-overview.png",
            resolution=(1280, 720),
        )
        scene.camera = original_camera

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    report = {
        "source": str(input_path),
        "output": str(output_path),
        "scope": "cubby alignment + chair seating + cubby/plant connected geometry only",
        "cubby": cubby_report,
        "chair": chair_report,
        "plant": plant_report,
        "roomwide_application_deferred": True,
        "renders": {
            "cubby": str(render_dir / "lofi-room-cathode-v106-cubby-closeup.png"),
            "plant": str(render_dir / "lofi-room-cathode-v106-plant-closeup.png"),
            "chair": str(render_dir / "lofi-room-cathode-v106-chair-closeup.png"),
            "overview": str(render_dir / "lofi-room-cathode-v106-overview.png"),
        },
    }
    report_path = output_path.with_name(output_path.stem + "-report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
