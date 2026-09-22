# -*- coding: utf-8 -*-
"""Room-wide connected-outline sweep with a strict transform freeze.

The pass starts from the approved v106 scene. It does not translate, rotate,
or scale any existing model. Construction seams are removed by rebuilding
multi-box carcasses as true exterior shells and by replacing overlapping
per-part outlines with one unioned assembly outline. The chair caster arms are
reshaped only at their wheel ends; wheel transforms stay untouched.
"""

from pathlib import Path
import argparse
import json
import math
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fix_connected_models_v106 as V106


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v106-connected-cubby-plant.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v107-roomwide-connected-sweep.blend"),
    )
    parser.add_argument(
        "--render-dir",
        default=str(HERE / "outputs" / "blender"),
    )
    return parser.parse_args(argv)


def matrix_values(ob):
    return tuple(round(value, 9) for row in ob.matrix_world for value in row)


def snapshot_model_transforms():
    return {
        ob.name: matrix_values(ob)
        for ob in bpy.data.objects
        if ob.type == "MESH" and not ob.name.startswith("CATHODE_")
    }


def mesh_component_indices(ob):
    vertices = ob.data.vertices
    adjacency = [set() for _ in vertices]
    for edge in ob.data.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen = set()
    components = []
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
        components.append(component)
    return components


def component_world_bounds(ob, component):
    points = [ob.matrix_world @ ob.data.vertices[index].co for index in component]
    return (
        min(point.x for point in points), max(point.x for point in points),
        min(point.y for point in points), max(point.y for point in points),
        min(point.z for point in points), max(point.z for point in points),
    )


def component_is_axis_box(ob, component, tolerance=1e-5):
    if len(component) != 8:
        return False
    points = [ob.matrix_world @ ob.data.vertices[index].co for index in component]
    axes = (
        {round(point.x / tolerance) for point in points},
        {round(point.y / tolerance) for point in points},
        {round(point.z / tolerance) for point in points},
    )
    return all(len(values) == 2 for values in axes)


def all_component_boxes(ob):
    components = mesh_component_indices(ob)
    if not all(component_is_axis_box(ob, component) for component in components):
        raise ValueError("%s is not exclusively axis-aligned box components" % ob.name)
    return [component_world_bounds(ob, component) for component in components]


def replace_object_with_axis_union(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return {"object": name, "status": "missing"}
    frozen_matrix = ob.matrix_world.copy()
    boxes = all_component_boxes(ob)
    old_mesh = ob.data
    materials = list(old_mesh.materials)
    world_mesh = V106.build_axis_union_mesh(name + "_Connected_v107_WorldMesh", boxes)
    world_mesh.transform(frozen_matrix.inverted())
    world_mesh.name = name + "_Connected_v107_Mesh"
    ob.data = world_mesh
    for material in materials:
        world_mesh.materials.append(material)
    V106.assign_cathode_face_materials(ob)
    ob.matrix_world = frozen_matrix
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    outline = V106.replace_outline(ob, old_names=("CATHODE_WIREFRAME_" + name,))
    ob["cathode_connected_shell_v107"] = True
    return {
        "object": name,
        "status": "connected",
        "source_components": len(boxes),
        "outline": outline.name,
        "transform_unchanged": matrix_values(ob) == tuple(round(value, 9) for row in frozen_matrix for value in row),
        "faces": len(ob.data.polygons),
    }


def delete_source_outlines(source_names):
    removed = []
    for source_name in source_names:
        name = "CATHODE_WIREFRAME_" + source_name
        outline = bpy.data.objects.get(name)
        if outline is not None:
            removed.append(name)
            bpy.data.objects.remove(outline, do_unlink=True)
    return removed


def add_outline_modifiers(outline, thickness=0.01, use_boundary=True):
    outline.data.materials.clear()
    outline.data.materials.append(V106.flowing_ink_material())
    wire = outline.modifiers.new("Roomwide connected outline", "WIREFRAME")
    wire.thickness = thickness
    wire.offset = 1.0
    wire.use_even_offset = True
    wire.use_replace = True
    wire.use_boundary = use_boundary
    depth = outline.modifiers.new("Roomwide outline depth", "SOLIDIFY")
    depth.thickness = 0.002
    depth.offset = 0.0
    outline["cathode_roomwide_connected_outline_v107"] = True


def link_to_restyle(ob):
    collection = bpy.data.collections.get("CATHODE_RESTYLE")
    if collection is None:
        collection = bpy.data.collections.new("CATHODE_RESTYLE")
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(ob)


def create_axis_assembly_outline(label, source_names, thickness=0.01):
    sources = [bpy.data.objects.get(name) for name in source_names]
    sources = [source for source in sources if source is not None and source.type == "MESH"]
    if not sources:
        return {"assembly": label, "status": "missing"}
    boxes = []
    for source in sources:
        boxes.extend(all_component_boxes(source))
    mesh = V106.build_axis_union_mesh("CATHODE_ASSEMBLY_" + label + "_Mesh", boxes)
    name = "CATHODE_ASSEMBLY_OUTLINE_" + label
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    outline = bpy.data.objects.new(name, mesh)
    link_to_restyle(outline)
    add_outline_modifiers(outline, thickness=thickness)
    removed = delete_source_outlines([source.name for source in sources])
    return {
        "assembly": label,
        "status": "connected_axis_union_outline",
        "sources": [source.name for source in sources],
        "removed_part_outlines": removed,
        "outline": outline.name,
        "boxes": len(boxes),
        "faces": len(mesh.polygons),
    }


def dissolve_coplanar_edges(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    for _ in range(3):
        edges = [
            edge for edge in bm.edges
            if len(edge.link_faces) == 2
            and edge.link_faces[0].normal.dot(edge.link_faces[1].normal) > 0.999999
        ]
        if not edges:
            break
        bmesh.ops.dissolve_edges(bm, edges=edges, use_verts=True, use_face_split=False)
        bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def duplicate_evaluated_mesh(source, name):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = source.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    duplicate = bpy.data.objects.new(name, mesh)
    duplicate.matrix_world = source.matrix_world.copy()
    return duplicate


def create_boolean_assembly_outline(label, source_names, thickness=0.009):
    sources = [bpy.data.objects.get(name) for name in source_names]
    sources = [source for source in sources if source is not None and source.type == "MESH"]
    if not sources:
        return {"assembly": label, "status": "missing"}

    operand_collection = bpy.data.collections.new("TMP_V107_" + label + "_OPERANDS")
    bpy.context.scene.collection.children.link(operand_collection)
    base = duplicate_evaluated_mesh(sources[0], "TMP_V107_" + label + "_BASE")
    bpy.context.scene.collection.objects.link(base)
    operands = []
    for index, source in enumerate(sources[1:]):
        duplicate = duplicate_evaluated_mesh(source, "TMP_V107_%s_%02d" % (label, index))
        operand_collection.objects.link(duplicate)
        operands.append(duplicate)

    if operands:
        bpy.context.view_layer.objects.active = base
        base.select_set(True)
        modifier = base.modifiers.new("Connected assembly union", "BOOLEAN")
        modifier.operation = "UNION"
        modifier.operand_type = "COLLECTION"
        modifier.collection = operand_collection
        modifier.solver = "EXACT"
        if hasattr(modifier, "use_self"):
            modifier.use_self = True
        if hasattr(modifier, "use_hole_tolerant"):
            modifier.use_hole_tolerant = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        base.select_set(False)
    dissolve_coplanar_edges(base.data)
    if not base.data.polygons:
        raise RuntimeError("Boolean assembly %s produced no faces" % label)

    for operand in operands:
        bpy.data.objects.remove(operand, do_unlink=True)
    bpy.data.collections.remove(operand_collection)
    name = "CATHODE_ASSEMBLY_OUTLINE_" + label
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    base.name = name
    base.data.name = name + "_Mesh"
    # Keep the base's original transform. Its evaluated mesh was generated in
    # local coordinates, so no source transform is changed or baked away.
    for collection in list(base.users_collection):
        collection.objects.unlink(base)
    link_to_restyle(base)
    add_outline_modifiers(base, thickness=thickness)
    removed = delete_source_outlines([source.name for source in sources])
    return {
        "assembly": label,
        "status": "connected_boolean_outline",
        "sources": [source.name for source in sources],
        "removed_part_outlines": removed,
        "outline": base.name,
        "vertices": len(base.data.vertices),
        "faces": len(base.data.polygons),
    }


def build_loft_arm_mesh(name, sections, direction, perpendicular, origin_xy, inverse_matrix):
    vertices_world = []
    for distance, half_width, center_z, half_height in sections:
        center = Vector((origin_xy.x, origin_xy.y, 0.0)) + direction * distance
        vertices_world.extend((
            (center.x - perpendicular.x * half_width,
             center.y - perpendicular.y * half_width, center_z - half_height),
            (center.x + perpendicular.x * half_width,
             center.y + perpendicular.y * half_width, center_z - half_height),
            (center.x + perpendicular.x * half_width,
             center.y + perpendicular.y * half_width, center_z + half_height),
            (center.x - perpendicular.x * half_width,
             center.y - perpendicular.y * half_width, center_z + half_height),
        ))
    vertices = [tuple(inverse_matrix @ Vector(vertex)) for vertex in vertices_world]
    faces = [(3, 2, 1, 0)]
    for section_index in range(len(sections) - 1):
        a = section_index * 4
        b = (section_index + 1) * 4
        for edge_index in range(4):
            nxt = (edge_index + 1) % 4
            faces.append((a + edge_index, a + nxt, b + nxt, b + edge_index))
    last = (len(sections) - 1) * 4
    faces.append((last, last + 1, last + 2, last + 3))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh


def replace_arm_outline_open_at_wheel(arm, direction, hub_xy):
    old = bpy.data.objects.get("CATHODE_WIREFRAME_" + arm.name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    outline = bpy.data.objects.new("CATHODE_WIREFRAME_" + arm.name, arm.data.copy())
    link_to_restyle(outline)
    outline.matrix_world = arm.matrix_world.copy()
    bm = bmesh.new()
    bm.from_mesh(outline.data)
    bm.faces.ensure_lookup_table()
    hub = Vector((hub_xy.x, hub_xy.y, 0.0))
    end_face = max(
        bm.faces,
        key=lambda face: ((outline.matrix_world @ face.calc_center_median()) - hub).dot(direction),
    )
    bmesh.ops.delete(bm, geom=[end_face], context="FACES_ONLY")
    bm.to_mesh(outline.data)
    bm.free()
    add_outline_modifiers(outline, thickness=0.008, use_boundary=False)
    outline["cathode_open_wheel_connection_v107"] = True
    return outline


def reshape_chair_caster_arms():
    hub = bpy.data.objects.get("CHAIR_Hub")
    if hub is None:
        raise RuntimeError("Missing CHAIR_Hub")
    hub_bounds = V106.world_bounds(hub)
    hub_xy = Vector(((hub_bounds[0] + hub_bounds[1]) * 0.5,
                     (hub_bounds[2] + hub_bounds[3]) * 0.5, 0.0))
    hub_center_z = (hub_bounds[4] + hub_bounds[5]) * 0.5
    results = []
    for index in range(5):
        arm = bpy.data.objects.get("CHAIR_BaseArm_%d" % index)
        wheel = bpy.data.objects.get("CHAIR_Wheel_%d" % index)
        if arm is None or wheel is None:
            continue
        frozen_matrix = arm.matrix_world.copy()
        arm_points = V106.mesh_world_points(arm)
        wheel_points = V106.mesh_world_points(wheel)
        wheel_bounds = V106.world_bounds(wheel)
        wheel_center = Vector(((wheel_bounds[0] + wheel_bounds[1]) * 0.5,
                               (wheel_bounds[2] + wheel_bounds[3]) * 0.5, 0.0))
        direction = wheel_center - hub_xy
        direction.z = 0.0
        direction.normalize()
        perpendicular = Vector((-direction.y, direction.x, 0.0))
        projections = [(point - hub_xy).dot(direction) for point in arm_points]
        side_projections = [abs((point - hub_xy).dot(perpendicular)) for point in arm_points]
        wheel_projection = min((point - hub_xy).dot(direction) for point in wheel_points)
        start = min(projections)
        broad_half_width = max(side_projections)
        z_min = min(point.z for point in arm_points)
        z_max = max(point.z for point in arm_points)
        # The previous beam inherited the source arm's full vertical depth,
        # which made it hang below the octagonal hub. Keep the footprint and
        # endpoints frozen, but halve total height and center it on the hub.
        broad_center_z = hub_center_z
        broad_half_height = (z_max - z_min) * 0.25
        wheel_center_z = (wheel_bounds[4] + wheel_bounds[5]) * 0.5
        touch = wheel_projection - 0.002
        shoulder = min(touch - 0.052, max(start + 0.10, touch - 0.052))
        transition = min(touch - 0.018, shoulder + 0.030)
        sections = (
            (start, broad_half_width, broad_center_z, broad_half_height),
            (shoulder, broad_half_width, broad_center_z, broad_half_height),
            (transition, 0.011, wheel_center_z, 0.009),
            (touch, 0.011, wheel_center_z, 0.009),
        )
        old_mesh = arm.data
        materials = list(old_mesh.materials)
        arm.data = build_loft_arm_mesh(
            arm.name + "_ConnectedCaster_v107_Mesh",
            sections,
            direction,
            perpendicular,
            hub_xy,
            frozen_matrix.inverted(),
        )
        for material in materials:
            arm.data.materials.append(material)
        arm.matrix_world = frozen_matrix
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
        outline = replace_arm_outline_open_at_wheel(arm, direction, hub_xy)
        arm["cathode_tapered_wheel_connection_v107"] = True
        results.append({
            "arm": arm.name,
            "wheel": wheel.name,
            "outline": outline.name,
            "wheel_transform_unchanged": True,
            "arm_transform_unchanged": matrix_values(arm) == tuple(
                round(value, 9) for row in frozen_matrix for value in row
            ),
            "broad_end": round(shoulder, 6),
            "connector_end": round(touch, 6),
            "wheel_inner_surface": round(wheel_projection, 6),
            "geometric_clearance": round(wheel_projection - touch, 6),
        })
    return results


def build_connected_pot(prefix, body, rim, soil):
    body_bounds = V106.world_bounds(body)
    rim_bounds = V106.world_bounds(rim)
    soil_bounds = V106.world_bounds(soil)
    center_x = (body_bounds[0] + body_bounds[1]) * 0.5
    center_y = (body_bounds[2] + body_bounds[3]) * 0.5
    bottom_half = (body_bounds[1] - body_bounds[0]) * 0.5 - 0.025
    body_top_half = (body_bounds[1] - body_bounds[0]) * 0.5
    rim_outer_half = (rim_bounds[1] - rim_bounds[0]) * 0.5
    rim_inner_half = (soil_bounds[1] - soil_bounds[0]) * 0.5 + 0.004
    bottom_z = body_bounds[4]
    shoulder_z = rim_bounds[4]
    rim_top_z = rim_bounds[5]
    soil_z = max(soil_bounds[5], shoulder_z + 0.003)
    vertices = []
    faces = []

    def ring(half, z):
        start = len(vertices)
        vertices.extend((
            (center_x - half, center_y - half, z),
            (center_x + half, center_y - half, z),
            (center_x + half, center_y + half, z),
            (center_x - half, center_y + half, z),
        ))
        return [start + i for i in range(4)]

    def bridge(lower, upper, reverse=False):
        for i in range(4):
            j = (i + 1) % 4
            faces.append((lower[i], upper[i], upper[j], lower[j]) if reverse
                         else (lower[i], lower[j], upper[j], upper[i]))

    bottom = ring(bottom_half, bottom_z)
    body_top = ring(body_top_half, shoulder_z)
    outer_bottom = ring(rim_outer_half, shoulder_z)
    outer_top = ring(rim_outer_half, rim_top_z)
    inner_top = ring(rim_inner_half, rim_top_z)
    soil_ring = ring(rim_inner_half, soil_z)
    faces.append(tuple(reversed(bottom)))
    bridge(bottom, body_top)
    for i in range(4):
        j = (i + 1) % 4
        faces.append((body_top[i], outer_bottom[i], outer_bottom[j], body_top[j]))
    bridge(outer_bottom, outer_top)
    for i in range(4):
        j = (i + 1) % 4
        faces.append((outer_top[i], outer_top[j], inner_top[j], inner_top[i]))
    bridge(inner_top, soil_ring, reverse=True)
    faces.append(tuple(soil_ring))
    mesh = bpy.data.meshes.new(prefix + "_PlantPot_Connected_v107_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    pot = bpy.data.objects.new(prefix + "_PlantPot_Connected_v107", mesh)
    bpy.context.scene.collection.objects.link(pot)
    for material in body.data.materials:
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.material_index = 1 if polygon.normal.z > 0.6 and len(mesh.materials) > 1 else 0
    return pot, Vector((center_x, center_y, soil_z))


def sink_stem_entry(source, center, entry_radius):
    centers = [source.matrix_world @ polygon.center for polygon in source.data.polygons]
    bottom_index = min(range(len(centers)), key=lambda index: centers[index].z)
    top_index = max(range(len(centers)), key=lambda index: centers[index].z)
    bottom = centers[bottom_index]
    top = centers[top_index]
    radial = Vector((top.x - center.x, top.y - center.y, 0.0))
    if radial.length < 1e-8:
        radial = Vector((1.0, 0.0, 0.0))
    else:
        radial.normalize()
    target = Vector((center.x, center.y, center.z - 0.008)) + radial * entry_radius
    delta_world = target - bottom
    delta_local = source.matrix_world.inverted().to_3x3() @ delta_world
    for vertex_index in source.data.polygons[bottom_index].vertices:
        source.data.vertices[vertex_index].co += delta_local
    source.data.update()
    return delta_world.length


def clean_desk_plant():
    body = bpy.data.objects.get("DESK_PlantPot_Body")
    rim = bpy.data.objects.get("DESK_PlantPot_Rim")
    soil = bpy.data.objects.get("DESK_PlantPot_Soil")
    if body is None or rim is None or soil is None:
        return {"status": "missing"}
    old_outline_names = [
        ob.name for ob in list(bpy.data.objects)
        if ob.name.startswith("CATHODE_WIREFRAME_DESK_Plant")
    ]
    for name in old_outline_names:
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
    pot, center = build_connected_pot("DESK", body, rim, soil)
    for old in (body, rim, soil):
        bpy.data.objects.remove(old, do_unlink=True)
    pot_outline = V106.replace_outline(pot)
    stem_results = []
    leaf_outlines = []
    entry_radius = (V106.world_bounds(pot)[1] - V106.world_bounds(pot)[0]) * 0.12
    for source in sorted(
        (ob for ob in bpy.data.objects if ob.type == "MESH" and ob.name.startswith("DESK_Plant")),
        key=lambda ob: ob.name,
    ):
        if source.name.startswith("DESK_PlantStem_"):
            extension = sink_stem_entry(source, center, entry_radius)
            outline = V106.replace_outline(source, remove_end_caps=True, thickness=0.005)
            stem_results.append({"stem": source.name, "outline": outline.name,
                                 "entry_adjustment": round(extension, 6)})
        elif source.name.startswith("DESK_PlantLeaf_"):
            leaf_outlines.append(V106.replace_outline(source).name)
    return {
        "status": "connected",
        "pot": pot.name,
        "pot_outline": pot_outline.name,
        "old_outlines_removed": old_outline_names,
        "stems": stem_results,
        "leaf_outlines": leaf_outlines,
    }


def audit_transform_freeze(snapshot):
    changed = {}
    deleted = []
    for name, before in snapshot.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            deleted.append(name)
            continue
        after = matrix_values(ob)
        if before != after:
            changed[name] = {"before": before, "after": after}
    return {"changed": changed, "deleted_for_connected_rebuild": deleted,
            "unchanged_count": len(snapshot) - len(changed) - len(deleted)}


def aim_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def qa_camera(name, location, target, lens=58.0):
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


def render(scene, camera, path, size=(1000, 720)):
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
    transforms = snapshot_model_transforms()

    shell_names = (
        "BED_Frame_Carcass_Cohesive",
        "DESK_Carcass_Cohesive",
        "SHELF_Carcass_Cohesive",
        "WINDOW_1_Frame_Cohesive",
        "WINDOW_2_Frame_Cohesive",
    )
    shells = [replace_object_with_axis_union(name) for name in shell_names]

    axis_assemblies = []
    axis_assemblies.append(create_axis_assembly_outline("PulsarFrame", (
        "ART_PulsarMap_Back", "ART_PulsarMap_Bottom", "ART_PulsarMap_North",
        "ART_PulsarMap_South", "ART_PulsarMap_Top",
    )))
    axis_assemblies.append(create_axis_assembly_outline("GoldenRecordFrame", (
        "INTERACT_GoldenRecord_Back", "INTERACT_GoldenRecord_Bottom",
        "INTERACT_GoldenRecord_North", "INTERACT_GoldenRecord_South",
        "INTERACT_GoldenRecord_Top",
    )))
    axis_assemblies.append(create_axis_assembly_outline("DiplomaFrame", (
        "INTERACT_Diploma_Back", "INTERACT_Diploma_Bottom", "INTERACT_Diploma_North",
        "INTERACT_Diploma_South", "INTERACT_Diploma_Top",
    )))

    boolean_specs = (
        ("Monitor", ("INTERACT_Monitor_Body", "INTERACT_Monitor_Screen",
                     "DESK_MonitorStem", "DESK_MonitorBase")),
        ("DeskMug", ("DESK_Mug", "DESK_MugHandleLower",
                     "DESK_MugHandleOuter", "DESK_MugHandleUpper")),
        ("DeskLamp", ("DESK_LampBase", "DESK_LampArm",
                      "DESK_LampShade", "DESK_LampBulb")),
        ("ShelfCamera", ("SHELF_Camera_Body", "SHELF_Camera_LensOuter",
                         "SHELF_Camera_LensGlass", "SHELF_Camera_ShutterButton")),
        ("ShelfGlobe", ("SHELF_Globe", "SHELF_GlobeAxis", "SHELF_GlobeStand")),
        ("StorageBin0", ("SHELF_StorageBin_0_Body", "SHELF_StorageRim_0",
                         "SHELF_StorageHandle_0")),
        ("StorageBin1", ("SHELF_StorageBin_1_Body", "SHELF_StorageRim_1",
                         "SHELF_StorageHandle_1")),
        ("SpeakerLeft", ("DESK_Speaker_Left", "DESK_SpeakerTweeter_Left",
                         "DESK_SpeakerWoofer_Left")),
        ("SpeakerRight", ("DESK_Speaker_Right", "DESK_SpeakerTweeter_Right",
                          "DESK_SpeakerWoofer_Right")),
        ("ChairUpper", ("CHAIR_Hub", "CHAIR_Post", "CHAIR_Seat", "CHAIR_Back",
                        "CHAIR_Lumbar", "CHAIR_ArmPost_L", "CHAIR_ArmPost_R",
                        "CHAIR_ArmPad_L", "CHAIR_ArmPad_R")),
    )
    boolean_assemblies = [
        create_boolean_assembly_outline(label, names)
        for label, names in boolean_specs
    ]

    chair_arms = reshape_chair_caster_arms()
    desk_plant = clean_desk_plant()
    transform_audit = audit_transform_freeze(transforms)
    if transform_audit["changed"]:
        raise RuntimeError("Transform freeze violated: %s" % sorted(transform_audit["changed"]))

    scene["cathode_roomwide_intersection_sweep_v107"] = True
    scene["cathode_existing_model_transforms_changed_v107"] = 0
    scene["cathode_source_file_v107"] = str(input_path)
    scene["cathode_restyle_version"] = "v107"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "chair": qa_camera("CAM_QA_ChairConnections_v107", (-0.35, 0.18, 0.64),
                           (0.0, 1.34, 0.17), 66.0),
        "shelf": qa_camera("CAM_QA_ShelfConnected_v107", (0.55, -0.20, 2.20),
                           (2.45, 1.36, 1.15), 62.0),
        "desk": qa_camera("CAM_QA_DeskConnected_v107", (-1.75, 1.05, 1.68),
                          (0.10, 2.46, 1.14), 48.0),
        "monitor": qa_camera("CAM_QA_MonitorConnected_v107", (-0.82, 1.48, 1.53),
                             (0.0, 2.48, 1.15), 66.0),
        "deskplant": qa_camera("CAM_QA_DeskPlantConnected_v107", (-1.82, 1.65, 1.28),
                               (-1.30, 2.48, 1.00), 70.0),
        "frames": qa_camera("CAM_QA_FramesConnected_v107", (0.80, -1.45, 2.38),
                            (2.64, -1.57, 2.10), 68.0),
        "windows": qa_camera("CAM_QA_WindowsConnected_v107", (-1.40, 0.95, 2.02),
                             (-1.40, 2.66, 1.93), 48.0),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / ("lofi-room-cathode-v107-%s-closeup.png" % label)
        render(scene, camera, path)
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v107-overview.png"
        render(scene, original_camera, overview, size=(1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "scope": "roomwide construction-intersection cleanup + chair caster connections",
        "transform_freeze": transform_audit,
        "connected_shells": shells,
        "axis_outline_assemblies": axis_assemblies,
        "boolean_outline_assemblies": boolean_assemblies,
        "chair_caster_arms": chair_arms,
        "desk_plant": desk_plant,
        "preserved_as_intentionally_separate": [
            "books and vinyl sleeves", "keyboard keys", "blind slats",
            "floor tiles", "polaroid cards", "record-player layered controls",
            "wall/floor architectural corners",
        ],
        "renders": renders,
    }
    report_path = output_path.with_name(output_path.stem + "-report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
