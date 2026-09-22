# -*- coding: utf-8 -*-
"""Apply the monochrome Cathode value system to the existing room.

This script saves a new file and keeps the input untouched. It intentionally
does not rebuild room layout or interaction objects; it changes material/value
language and adds a small ink collection for existing visible geometry.

Example (run inside Blender):
    blender -b --python stylize_lofi_room_cathode.py -- \
      --input lofi-room-rebuild-v08-rainy-suburb.blend \
      --output outputs/blender/lofi-room-cathode-v01.blend
"""

from pathlib import Path
import argparse
import json
import math
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy
import bmesh
from mathutils import Matrix, Vector

import cathode_lib as CL
import cathode_emit as CE
import cathode_scene as CS


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(HERE / "lofi-room-rebuild-v08-rainy-suburb.blend"))
    p.add_argument("--output", default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v56-shelf-recomposition.blend"))
    p.add_argument("--render", default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v56-shelf-recomposition.png"))
    p.add_argument("--frame", type=int, default=48,
                   help="Preview frame for the animated outline pass")
    return p.parse_args(argv)


def remove_old_exterior():
    """Remove the former modeled neighborhood/second-room assembly."""
    doomed_prefixes = ("SUBURB_", "NEIGHBOR_")
    doomed_names = {
        "CAM_QA_Suburb_v08", "CAM_QA_Neighborhood_v06", "CAM_QA_WindowRoom_v06",
    }
    for ob in list(bpy.data.objects):
        if ob.name.startswith(doomed_prefixes) or ob.name in doomed_names:
            bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        if coll.name in {"RAINY_SUBURB_V07", "NEIGHBORHOOD_RAIN_V06", "RAINY_SUBURB"}:
            bpy.data.collections.remove(coll)


def remove_requested_geometry():
    """Apply the requested cleanup while leaving the archived source untouched."""
    removed_top_plant = []
    plant_prefixes = ("SHELF_TOPLEAF_", "SHELF_TOPSTEM_")
    plant_names = {"SHELF_TOPPOT_BODY", "SHELF_TOPPOT_RIM", "SHELF_TOPPOT_SOIL"}
    for ob in list(bpy.data.objects):
        upper = ob.name.upper()
        if upper.startswith(plant_prefixes) or upper in plant_names:
            removed_top_plant.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)

    removed_platform = []
    for platform_name in ("ARCH_Platform", "ARCH_Stage"):
        platform = bpy.data.objects.get(platform_name)
        if platform is not None:
            removed_platform.append(platform.name)
            bpy.data.objects.remove(platform, do_unlink=True)

    return removed_top_plant, removed_platform


def make_floor_squares():
    """Tile the 5.6-unit floor with seven complete 0.8-unit squares."""
    # The floor spans -2.8..2.8 on both axes. Seams at these six positions
    # leave no half-cell at an edge: 7 * 0.8 = 5.6 exactly.
    seam_positions = (-2.0, -1.2, -0.4, 0.4, 1.2, 2.0)
    planks = []
    for ob in bpy.data.objects:
        if ob.name.startswith("ARCH_FloorPlank_"):
            try:
                index = int(ob.name.rsplit("_", 1)[1])
            except ValueError:
                continue
            planks.append((index, ob))
    planks.sort(key=lambda item: item[0])
    removed = []
    kept = []
    for i, (index, ob) in enumerate(planks):
        if i >= len(seam_positions):
            removed.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
        else:
            kept.append(ob)
    for i, ob in enumerate(kept):
        ob.location.x = seam_positions[i]

    joints = []
    for ob in bpy.data.objects:
        if ob.name.startswith("ARCH_FloorJoint_"):
            try:
                index = int(ob.name.rsplit("_", 1)[1])
            except ValueError:
                continue
            joints.append((index, ob))
    joints.sort(key=lambda item: item[0])
    joint_removed = []
    kept_joints = []
    for i, (_, ob) in enumerate(joints):
        if i >= len(seam_positions):
            joint_removed.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
        else:
            ob.location.y = seam_positions[i]
            kept_joints.append(ob)
    return {
        "removed_planks": removed,
        "remaining_planks": [ob.name for ob in kept],
        "removed_joints": joint_removed,
        "joint_count": len(kept_joints),
        "joint_y_positions": [round(ob.location.y, 3) for ob in kept_joints],
        "square_size": 0.8,
        "floor_bounds": [-2.8, 2.8],
        "edge_aligned": True,
    }


def tuck_right_shelf_flush():
    """Align the shelf carcass to the east wall's inner face, as the bed is."""
    wall = bpy.data.objects.get("ARCH_EastWall")
    carcass = bpy.data.objects.get("SHELF_Carcass_Cohesive")
    if wall is None or carcass is None:
        return {"moved": [], "delta_x": 0.0, "wall_inner_x": None}

    wall_inner_x = min((wall.matrix_world @ vertex.co).x for vertex in wall.data.vertices)
    shelf_right_x = max((carcass.matrix_world @ vertex.co).x for vertex in carcass.data.vertices)
    delta_x = wall_inner_x - shelf_right_x
    moved = []
    for ob in bpy.data.objects:
        if ob.name.startswith("SHELF_"):
            ob.location.x += delta_x
            moved.append(ob.name)
    carcass["cathode_tucked_flush_to_wall"] = True
    carcass["cathode_flush_wall_inner_x"] = wall_inner_x
    carcass["cathode_flush_delta_x"] = delta_x
    return {
        "moved": moved,
        "delta_x": round(delta_x, 6),
        "wall_inner_x": round(wall_inner_x, 6),
    }


def make_procedural_grass_texture():
    """Build a packed, grayscale top-down grass field without using a source image.

    The texture is intentionally made from layered marks rather than noise alone:
    broad value variation reads as a little field at a distance, while hundreds
    of tapered-ish blade strokes and radial clumps survive the small window crop.
    """
    name = "CATHODE_GRASS_FIELD_FLAT_TEXTURE"
    width, height = 1024, 768
    image = bpy.data.images.get(name)
    if image is None or image.size[0] != width or image.size[1] != height:
        if image is not None:
            bpy.data.images.remove(image)
        image = bpy.data.images.new(name, width=width, height=height, alpha=True)

    pixels = [0.0] * (width * height * 4)

    def put(x, y, color, alpha=1.0):
        if 0 <= x < width and 0 <= y < height:
            i = ((height - 1 - y) * width + x) * 4
            pixels[i:i + 4] = [color[0], color[1], color[2], alpha]

    def rect(x0, y0, x1, y1, color):
        x0, x1 = max(0, int(x0)), min(width - 1, int(x1))
        y0, y1 = max(0, int(y0)), min(height - 1, int(y1))
        for y in range(y0, y1 + 1):
            row = ((height - 1 - y) * width + x0) * 4
            for x in range(x0, x1 + 1):
                pixels[row:row + 4] = [color[0], color[1], color[2], 1.0]
                row += 4

    def line(x0, y0, x1, y1, color, thickness=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for n in range(steps + 1):
            x = round(x0 + dx * n / steps)
            y = round(y0 + dy * n / steps)
            for ox in range(-thickness // 2, thickness // 2 + 1):
                for oy in range(-thickness // 2, thickness // 2 + 1):
                    put(x + ox, y + oy, color)

    def gray(v):
        v = max(0.0, min(1.0, v))
        return (v, v, v)

    def rnd(i, salt=0):
        # Deterministic, dependency-free pseudo-random values in [0, 1).
        return (math.sin((i + 1.0) * (12.9898 + salt * 78.233)) * 43758.5453) % 1.0

    # A quiet charcoal-to-silver field base. There is no sky or horizon because
    # this image is mapped to a horizontal plane immediately outside the wall.
    for y in range(height):
        t = y / float(height - 1)
        v = 0.155 + 0.145 * t
        v += 0.018 * math.sin(t * math.pi * 7.0)
        color = gray(v)
        rect(0, y, width - 1, y, color)

    # Broad irregular shadow lanes emulate the soft depth changes in a real
    # close-up field without introducing a second modeled room or a photograph.
    for i in range(24):
        x0 = int(rnd(i, 1) * (width - 180))
        y0 = int(rnd(i, 2) * (height - 90))
        w = 90 + int(rnd(i, 3) * 260)
        h = 18 + int(rnd(i, 4) * 70)
        v = 0.085 + rnd(i, 5) * 0.075
        rect(x0, y0, min(width - 1, x0 + w), min(height - 1, y0 + h), gray(v))

    # Dense layered blades. Varying length, lean, width, and value gives a
    # photographic impression when the small window crop is viewed obliquely.
    for i in range(860):
        x = int(rnd(i, 10) * width)
        y = int(rnd(i, 11) * height)
        h = 8 + int(rnd(i, 12) * 42)
        lean = int(-13 + rnd(i, 13) * 27)
        base = 0.11 + rnd(i, 14) * 0.30
        thickness = 1 if i % 7 else 2
        line(x, y, x + lean, max(0, y - h), gray(base), thickness)
        if i % 3 == 0:
            # A parallel highlight is what keeps individual blades readable
            # instead of collapsing into a flat hatch pattern.
            hi = min(0.86, base + 0.18 + rnd(i, 15) * 0.20)
            line(x + 1, y, x + lean + int(2 + rnd(i, 16) * 5), max(0, y - h + 5), gray(hi), 1)

    # Radial clumps add the characteristic star-like tufts visible from above.
    for i in range(118):
        cx = int(12 + rnd(i, 20) * (width - 24))
        cy = int(12 + rnd(i, 21) * (height - 24))
        arms = 6 + int(rnd(i, 22) * 5)
        for j in range(arms):
            angle = (math.pi * 2.0 * j / arms) + (rnd(i * 17 + j, 23) - 0.5) * 0.5
            length = 8 + int(rnd(i * 17 + j, 24) * 30)
            ex = round(cx + math.cos(angle) * length)
            ey = round(cy + math.sin(angle) * length)
            v = 0.22 + rnd(i * 17 + j, 25) * 0.34
            line(cx, cy, ex, ey, gray(v), 1 if j % 3 else 2)

    # Fine broken dark stems and pale tips create a little more photographic
    # grain while staying strictly within the grey/black/white palette.
    for i in range(280):
        x = int(rnd(i, 30) * width)
        y = int(rnd(i, 31) * height)
        length = 3 + int(rnd(i, 32) * 12)
        v = 0.045 + rnd(i, 33) * 0.16
        line(x, y, x + int(-4 + rnd(i, 34) * 9), max(0, y - length), gray(v), 1)
        if i % 9 == 0:
            put(x, max(0, y - length), gray(0.72 + rnd(i, 35) * 0.22))

    image.pixels.foreach_set(pixels)
    image.update()
    image.use_fake_user = True
    try:
        image.pack()
    except RuntimeError:
        pass
    image["cathode_flat_exterior"] = True
    return image


def make_neighborhood_texture():
    """Return a generated texture; the supplied reference is never loaded."""
    return make_procedural_grass_texture()


def add_flat_exterior(scene, coll):
    image = make_neighborhood_texture()
    mat = bpy.data.materials.get("CATHODE_GRASS_FIELD_FLAT")
    if mat is None:
        mat = bpy.data.materials.new("CATHODE_GRASS_FIELD_FLAT")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.08
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    coord = nodes.new("ShaderNodeTexCoord")
    links.new(coord.outputs["UV"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], em.inputs["Color"])
    links.new(em.outputs["Emission"], out.inputs["Surface"])

    name = "CATHODE_WINDOW_EXTERIOR_FLAT"
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    # Flat, inset planes are kept within the actual apertures. They sit just
    # inside the north wall's window line, so the right wall and center pier
    # mask them completely instead of allowing a ground card to leak outside.
    verts = []
    faces = []
    for cx in (-1.4, 1.4):
        x0, x1 = cx - 0.645, cx + 0.645
        z0, z1 = 1.265, 2.585
        base = len(verts)
        verts.extend([(x0, 2.665, z0), (x1, 2.665, z0),
                      (x1, 2.665, z1), (x0, 2.665, z1)])
        faces.append((base, base + 1, base + 2, base + 3))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    quad_uvs = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for poly in mesh.polygons:
        for loop_index, uv in zip(poly.loop_indices, quad_uvs):
            uv_layer.data[loop_index].uv = uv
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.data.materials.append(mat)
    obj["cathode_flat_exterior"] = True
    obj["cathode_flat_exterior_style"] = "procedural grayscale flat grass planes inset to window openings"
    obj["cathode_replaces_second_room"] = True
    return obj


def open_window_glass_for_exterior():
    """Remove opaque glass faces from the render so the ground patches read as outside."""
    opened = []
    for ob in bpy.data.objects:
        upper = ob.name.upper()
        if ob.type == "MESH" and "WINDOW_" in upper and "GLASS" in upper:
            ob.hide_render = True
            ob["cathode_window_glass_hidden"] = True
            opened.append(ob.name)
    return opened


def flow_material():
    """Animated white edge ink: dim base lines plus a moving bright glint."""
    mat = bpy.data.materials.get("CATHODE_FLOWING_WHITE_INK")
    if mat is None:
        mat = bpy.data.materials.new("CATHODE_FLOWING_WHITE_INK")
    mat.use_nodes = True
    if mat.node_tree.animation_data is not None:
        mat.node_tree.animation_data_clear()
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    links.new(em.outputs["Emission"], out.inputs["Surface"])

    geo = nodes.new("ShaderNodeNewGeometry")
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (0.47, 0.31, 0.84)
    links.new(geo.outputs["Position"], dot.inputs[0])
    spatial = nodes.new("ShaderNodeMath")
    spatial.operation = "MULTIPLY"
    spatial.inputs[1].default_value = 2.15
    links.new(dot.outputs["Value"], spatial.inputs[0])
    clock = nodes.new("ShaderNodeValue")
    clock.name = "FLOW_TIME"
    clock.label = "Animated flow time"
    # Use an exact whole number of shader cycles over the 1..240 frame span.
    # Linear interpolation keeps the glimmer's velocity constant.
    flow_delta = 4.0 * math.pi
    clock.outputs[0].default_value = 0.0
    clock.outputs[0].keyframe_insert(data_path="default_value", frame=1)
    clock.outputs[0].default_value = flow_delta
    clock.outputs[0].keyframe_insert(data_path="default_value", frame=240)
    action = mat.node_tree.animation_data.action if mat.node_tree.animation_data else None
    fcurves = []
    if action is not None:
        if hasattr(action, "fcurves"):
            fcurves.extend(action.fcurves)
        else:
            for layer in action.layers:
                for strip in layer.strips:
                    for channelbag in strip.channelbags:
                        fcurves.extend(channelbag.fcurves)
    for fcurve in fcurves:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = "LINEAR"
        if not any(modifier.type == "CYCLES" for modifier in fcurve.modifiers):
            fcurve.modifiers.new(type="CYCLES")
    mat["cathode_flow_clock_start"] = 0.0
    mat["cathode_flow_clock_end"] = flow_delta
    mat["cathode_flow_clock_interpolation"] = "LINEAR"
    mat["cathode_flow_loop"] = "exact two-cycle phase; cyclic extrapolation"
    summed = nodes.new("ShaderNodeMath")
    summed.operation = "ADD"
    links.new(spatial.outputs[0], summed.inputs[0])
    links.new(clock.outputs[0], summed.inputs[1])
    sine = nodes.new("ShaderNodeMath")
    sine.operation = "SINE"
    links.new(summed.outputs[0], sine.inputs[0])
    normalize = nodes.new("ShaderNodeMath")
    normalize.operation = "MULTIPLY"
    normalize.inputs[1].default_value = 0.5
    links.new(sine.outputs[0], normalize.inputs[0])
    offset = nodes.new("ShaderNodeMath")
    offset.operation = "ADD"
    offset.inputs[1].default_value = 0.5
    links.new(normalize.outputs[0], offset.inputs[0])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    elems = ramp.color_ramp.elements
    elems[0].position, elems[0].color = 0.0, (0, 0, 0, 1)
    elems[1].position, elems[1].color = 1.0, (0, 0, 0, 1)
    for pos in (0.445, 0.5, 0.555):
        e = elems.new(pos)
        e.color = (1, 1, 1, 1) if pos == 0.5 else (0, 0, 0, 1)
    links.new(offset.outputs[0], ramp.inputs[0])
    pulse = nodes.new("ShaderNodeMath")
    pulse.operation = "MULTIPLY"
    pulse.inputs[1].default_value = 4.6
    links.new(ramp.outputs["Color"], pulse.inputs[0])
    strength = nodes.new("ShaderNodeMath")
    strength.operation = "ADD"
    strength.inputs[1].default_value = 0.16
    links.new(pulse.outputs[0], strength.inputs[0])
    links.new(strength.outputs[0], em.inputs["Strength"])
    mat["cathode_flow_shader"] = "world-space scan plus diagonal glint"
    return mat


def add_flowing_outlines(scene, coll):
    cam = scene.camera
    if cam is None:
        return None, 0
    mat = flow_material()
    old = bpy.data.objects.get("CATHODE_FLOWING_OUTLINES")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    curve = bpy.data.curves.new("CATHODE_FLOWING_OUTLINES_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.010
    curve.bevel_resolution = 0
    curve.fill_mode = "FULL"
    curve.materials.append(mat)
    count = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name.startswith("CATHODE_") or ob.hide_render:
            continue
        if ob.get("cathode_suppress_flow_outline"):
            continue
        upper = ob.name.upper()
        if "GLASS" in upper or "RAIN" in upper:
            continue
        # Books and vinyl sleeves use square-section outline bars so their
        # close-up corners form flush right angles rather than rounded seams.
        if upper.startswith("BOOK_") or upper.startswith("INTERACT_VINYL_"):
            continue
        verts = ob.data.vertices
        for edge in ob.data.edges:
            a = ob.matrix_world @ verts[edge.vertices[0]].co
            b = ob.matrix_world @ verts[edge.vertices[1]].co
            if (b - a).length < 0.018:
                continue
            # A tiny camera-facing lift prevents z-fighting on coplanar ink.
            lift = (cam.location - (a + b) * 0.5).normalized() * 0.0035
            a += lift
            b += lift
            spline = curve.splines.new("POLY")
            spline.points.add(1)
            spline.points[0].co = (*a, 1.0)
            spline.points[1].co = (*b, 1.0)
            count += 1
    obj = bpy.data.objects.new("CATHODE_FLOWING_OUTLINES", curve)
    coll.objects.link(obj)
    obj["cathode_outline_edges"] = count
    obj["cathode_outline_animation"] = "moving white scan and glint"
    return obj, count


def add_book_vinyl_outline_corner_joints(scene, coll):
    """Fill close-up seams where separate beveled outline segments meet."""
    old = bpy.data.objects.get("CATHODE_BOOK_VINYL_OUTLINE_JOINTS")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    cam = scene.camera
    if cam is None:
        return None, 0

    bm = bmesh.new()
    count = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        upper = ob.name.upper()
        if not (upper.startswith("BOOK_") or upper.startswith("INTERACT_VINYL_")):
            continue
        used = {index for edge in ob.data.edges for index in edge.vertices}
        for index in used:
            point = ob.matrix_world @ ob.data.vertices[index].co
            # Match the outline's camera-facing offset while using one stable
            # position per shared mesh corner.
            point += (cam.location - point).normalized() * 0.0035
            bmesh.ops.create_icosphere(
                bm,
                subdivisions=2,
                radius=0.0115,
                matrix=Matrix.Translation(point),
            )
            count += 1

    mesh = bpy.data.meshes.new("CATHODE_BOOK_VINYL_OUTLINE_JOINTS_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    joints = bpy.data.objects.new("CATHODE_BOOK_VINYL_OUTLINE_JOINTS", mesh)
    coll.objects.link(joints)
    joints.data.materials.append(flow_material())
    joints["cathode_outline_corner_joints"] = count
    joints["cathode_outline_corner_joint_radius"] = 0.0115
    return joints, count


def add_book_vinyl_rectangular_corner_joints(scene, coll):
    """Close book and vinyl outline corners with flush, hard-edged blocks."""
    for name in (
        "CATHODE_BOOK_VINYL_OUTLINE_JOINTS",
        "CATHODE_BOOK_VINYL_RECTANGULAR_JOINTS",
    ):
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
    cam = scene.camera
    if cam is None:
        return None, 0

    bm = bmesh.new()
    count = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        upper = ob.name.upper()
        if not (upper.startswith("BOOK_") or upper.startswith("INTERACT_VINYL_")):
            continue
        rotation = ob.matrix_world.to_quaternion().to_matrix().to_4x4()
        used = {index for edge in ob.data.edges for index in edge.vertices}
        for index in used:
            point = ob.matrix_world @ ob.data.vertices[index].co
            point += (cam.location - point).normalized() * 0.0035
            transform = Matrix.Translation(point) @ rotation
            bmesh.ops.create_cube(bm, size=0.0205, matrix=transform)
            count += 1

    mesh = bpy.data.meshes.new("CATHODE_BOOK_VINYL_RECTANGULAR_JOINTS_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    joints = bpy.data.objects.new("CATHODE_BOOK_VINYL_RECTANGULAR_JOINTS", mesh)
    coll.objects.link(joints)
    joints.data.materials.append(flow_material())
    joints["cathode_outline_rectangular_corner_joints"] = count
    joints["cathode_outline_corner_block_size"] = 0.0205
    return joints, count


def add_book_vinyl_flush_rectangular_outlines(scene, coll):
    """Build book/vinyl outlines from flush square bars with clean right-angle joins."""
    for name in (
        "CATHODE_BOOK_VINYL_OUTLINE_JOINTS",
        "CATHODE_BOOK_VINYL_RECTANGULAR_JOINTS",
        "CATHODE_BOOK_VINYL_FLUSH_OUTLINES",
    ):
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
    cam = scene.camera
    if cam is None:
        return None, 0

    thickness = 0.020
    bm = bmesh.new()
    count = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        upper = ob.name.upper()
        if not (upper.startswith("BOOK_") or upper.startswith("INTERACT_VINYL_")):
            continue

        # One shared lifted position per source vertex prevents adjacent bars
        # from drifting apart at a corner.
        lifted = {}
        for vertex in ob.data.vertices:
            point = ob.matrix_world @ vertex.co
            point += (cam.location - point).normalized() * 0.0035
            lifted[vertex.index] = point

        for edge in ob.data.edges:
            a = lifted[edge.vertices[0]]
            b = lifted[edge.vertices[1]]
            direction = b - a
            length = direction.length
            if length < 0.018:
                continue
            midpoint = (a + b) * 0.5
            rotation = direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
            # Extend each bar by half a stroke at both ends. Perpendicular bars
            # then overlap into one flush square joint without extra caps.
            scale = Matrix.Diagonal((thickness, thickness, length + thickness, 1.0))
            transform = Matrix.Translation(midpoint) @ rotation @ scale
            bmesh.ops.create_cube(bm, size=1.0, matrix=transform)
            count += 1

    mesh = bpy.data.meshes.new("CATHODE_BOOK_VINYL_FLUSH_OUTLINES_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    outlines = bpy.data.objects.new("CATHODE_BOOK_VINYL_FLUSH_OUTLINES", mesh)
    coll.objects.link(outlines)
    outlines.data.materials.append(flow_material())
    outlines["cathode_flush_rectangular_outline_edges"] = count
    outlines["cathode_flush_rectangular_outline_thickness"] = thickness
    return outlines, count


def add_book_vinyl_continuous_face_outlines(scene, coll):
    """Use continuous cyclic face loops so outline corners join without caps."""
    for name in (
        "CATHODE_BOOK_VINYL_OUTLINE_JOINTS",
        "CATHODE_BOOK_VINYL_RECTANGULAR_JOINTS",
        "CATHODE_BOOK_VINYL_FLUSH_OUTLINES",
        "CATHODE_BOOK_VINYL_CONTINUOUS_OUTLINES",
    ):
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
    cam = scene.camera
    if cam is None:
        return None, 0

    curve = bpy.data.curves.new("CATHODE_BOOK_VINYL_CONTINUOUS_OUTLINES_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.010
    curve.bevel_resolution = 0
    curve.fill_mode = "FULL"
    curve.materials.append(flow_material())
    count = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        upper = ob.name.upper()
        if not (upper.startswith("BOOK_") or upper.startswith("INTERACT_VINYL_")):
            continue
        lifted = {}
        for vertex in ob.data.vertices:
            point = ob.matrix_world @ vertex.co
            point += (cam.location - point).normalized() * 0.0035
            lifted[vertex.index] = point
        for polygon in ob.data.polygons:
            indices = list(polygon.vertices)
            if len(indices) < 3:
                continue
            spline = curve.splines.new("POLY")
            spline.points.add(len(indices) - 1)
            for point, index in zip(spline.points, indices):
                point.co = (*lifted[index], 1.0)
            spline.use_cyclic_u = True
            count += 1

    outlines = bpy.data.objects.new("CATHODE_BOOK_VINYL_CONTINUOUS_OUTLINES", curve)
    coll.objects.link(outlines)
    outlines["cathode_continuous_face_outline_loops"] = count
    outlines["cathode_outline_join_style"] = "continuous cyclic right-angle loops"
    return outlines, count


def add_book_vinyl_connected_wireframe_outlines(scene, coll):
    """Derive natural joined outlines from each source mesh with Wireframe."""
    prefixes = (
        "CATHODE_BOOK_VINYL_OUTLINE_JOINTS",
        "CATHODE_BOOK_VINYL_RECTANGULAR_JOINTS",
        "CATHODE_BOOK_VINYL_FLUSH_OUTLINES",
        "CATHODE_BOOK_VINYL_CONTINUOUS_OUTLINES",
        "CATHODE_WIREFRAME_BOOK_",
        "CATHODE_WIREFRAME_INTERACT_VINYL_",
    )
    for old in list(bpy.data.objects):
        if any(old.name.upper().startswith(prefix.upper()) for prefix in prefixes):
            bpy.data.objects.remove(old, do_unlink=True)

    mat = flow_material()
    count = 0
    for source in list(bpy.data.objects):
        if source.type != "MESH" or source.hide_render:
            continue
        upper = source.name.upper()
        if not (upper.startswith("BOOK_") or upper.startswith("INTERACT_VINYL_")):
            continue
        outline = source.copy()
        outline.data = source.data.copy()
        outline.name = "CATHODE_WIREFRAME_" + source.name
        coll.objects.link(outline)
        outline.data.materials.clear()
        outline.data.materials.append(mat)

        wire = outline.modifiers.new("Connected flush outline", "WIREFRAME")
        wire.thickness = 0.010
        wire.offset = 1.0
        wire.use_replace = True
        wire.use_even_offset = True
        wire.use_relative_offset = False
        wire.use_boundary = True

        solid = outline.modifiers.new("Minimal outline depth", "SOLIDIFY")
        solid.thickness = 0.002
        solid.offset = 0.0
        outline["cathode_connected_wireframe_source"] = source.name
        count += 1
    return count


def configure_compositor(scene):
    scene.use_nodes = True
    tree = scene.compositing_node_group
    if tree is None:
        tree = bpy.data.node_groups.new("CATHODE_COMPOSITOR", "CompositorNodeTree")
        scene.compositing_node_group = tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()
    rl = nodes.new("CompositorNodeRLayers")
    glow = nodes.new("CompositorNodeGlare")
    if hasattr(glow, "glare_type"):
        glow.glare_type = "FOG_GLOW"
        glow.quality = "HIGH"
        glow.threshold = 0.8
        glow.size = 6
    else:
        # Blender 5.2 exposes compositor settings as menu sockets.
        glow.inputs["Type"].default_value = "Fog Glow"
        glow.inputs["Quality"].default_value = "High"
        glow.inputs["Threshold"].default_value = 0.8
        glow.inputs["Size"].default_value = 0.72
    comp = nodes.new("CompositorNodeComposite")
    links.new(rl.outputs["Image"], glow.inputs["Image"])
    links.new(glow.outputs["Image"], comp.inputs["Image"])


def emission(name, rgb, strength=1.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*[c / 255.0 for c in rgb], 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def style_materials():
    return {
        "bright": emission("CATH_ROOM_BRIGHT", (27, 27, 27)),
        "dark": emission("CATH_ROOM_DARK", (10, 10, 10)),
        "mid": emission("CATH_ROOM_MID", (58, 58, 58)),
        "white": emission("CATH_ROOM_WHITE", (220, 220, 220), 0.65),
    }


def is_preserved(name):
    upper = name.upper()
    return any(k in upper for k in (
        "TARGET_", "CAMERA", "DIPLOMA", "VINYL", "MONITOR", "SCREEN",
        "INTERACT", "PIVOT", "LIGHTNING", "RAIN", "EXTERIOR"))


def choose_material(ob, mats):
    name = ob.name.upper()
    if "SCREEN" in name:
        return mats["white"]
    if "MONITOR" in name:
        return mats["mid"]
    if any(k in name for k in ("EMISSION", "GLOW", "LIGHT")):
        return mats["white"]
    if any(k in name for k in ("WALL", "FLOOR", "CEILING", "SHADOW", "RECESS")):
        return mats["dark"]
    if any(k in name for k in ("FRAME", "TRIM", "EDGE", "RAIL", "HOLDER")):
        return mats["mid"]
    return mats["bright"]


def copy_original_materials():
    coll = bpy.data.collections.get("ORIGINAL_MATERIALS")
    if coll is None:
        coll = bpy.data.collections.new("ORIGINAL_MATERIALS")
        bpy.context.scene.collection.children.link(coll)
    # Material datablocks are not collection members, so mark them with a
    # custom property rather than mutating the original datablock names.
    for mat in bpy.data.materials:
        if not mat.name.startswith("CATH_"):
            mat["cathode_original"] = True


def apply_values(mats):
    changed = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name.startswith("CATH_"):
            continue
        mat = choose_material(ob, mats)
        # Keep an explicit original reference on the object for rollback and
        # diagnostics, while replacing only this output file's slots.
        ob["cathode_original_materials"] = [m.name for m in ob.data.materials if m]
        ob.data.materials.clear()
        ob.data.materials.append(mats["bright"])
        ob.data.materials.append(mats["dark"])
        ob.data.materials.append(mat)
        for poly in ob.data.polygons:
            wn = ob.matrix_world.to_3x3() @ poly.normal
            if "MONITOR" in ob.name.upper() and "SCREEN" not in ob.name.upper():
                # The monitor housing is intentionally a quiet mid-gray;
                # otherwise the generic monitor keyword would make it bright.
                poly.material_index = 2
            else:
                poly.material_index = 1 if CL.face_class(wn) else (2 if mat == mats["white"] else 0)
        changed.append(ob.name)
    return changed


def restyle_record_player_arm(mats):
    """Replace the curve's original rainbow metal with a Cathode grey material."""
    arm = bpy.data.objects.get("INTERACT_RecordPlayer_Arm")
    if arm is None or not hasattr(arm.data, "materials"):
        return None
    arm["cathode_original_materials"] = [m.name for m in arm.data.materials if m]
    arm.data.materials.clear()
    arm.data.materials.append(mats["mid"])
    arm["cathode_grayscale_material"] = mats["mid"].name
    return arm.name


def resize_object_axis(ob, axis, center, size):
    """Resize an unrotated shelf part around its world-space center."""
    if ob is None or not hasattr(ob, "data") or not hasattr(ob.data, "vertices"):
        return None
    world_vertices = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
    current_min = min(vertex[axis] for vertex in world_vertices)
    current_max = max(vertex[axis] for vertex in world_vertices)
    current_size = current_max - current_min
    if current_size < 1.0e-6:
        return None
    factor = size / current_size
    if axis == 0:
        ob.scale.x *= factor
    elif axis == 1:
        ob.scale.y *= factor
    else:
        ob.scale.z *= factor
    bpy.context.view_layer.update()
    world_vertices = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
    new_center = sum(vertex[axis] for vertex in world_vertices) / len(world_vertices)
    ob.location[axis] += center - new_center
    bpy.context.view_layer.update()
    return {"center": round(center, 6), "size": round(size, 6)}


def set_world_axis_bounds(ob, axis, lower, upper):
    """Remap an object's evaluated mesh to exact world-space bounds on one axis.

    A few source books have a slight local tilt, so changing ``dimensions``
    alone can leave their axis-aligned world bounds wider than the requested
    cubby run. Remapping the mesh vertices preserves the other world axes and
    makes the visible spine edges land exactly on the planned interval.
    """
    if ob is None or not hasattr(ob, "data") or not hasattr(ob.data, "vertices"):
        return None
    vertices = list(ob.data.vertices)
    if not vertices:
        return None
    world_matrix = ob.matrix_world.copy()
    inverse_matrix = world_matrix.inverted()
    world_vertices = [world_matrix @ vertex.co for vertex in vertices]
    current_min = min(point[axis] for point in world_vertices)
    current_max = max(point[axis] for point in world_vertices)
    current_size = current_max - current_min
    target_size = upper - lower
    if current_size < 1.0e-6 or target_size <= 0.0:
        return None
    factor = target_size / current_size
    for vertex, point in zip(vertices, world_vertices):
        remapped = point.copy()
        remapped[axis] = lower + (point[axis] - current_min) * factor
        vertex.co = inverse_matrix @ remapped
    ob.data.update()
    bpy.context.view_layer.update()
    final_world_vertices = [ob.matrix_world @ vertex.co for vertex in vertices]
    return {
        "min": round(min(point[axis] for point in final_world_vertices), 6),
        "max": round(max(point[axis] for point in final_world_vertices), 6),
        "size": round(target_size, 6),
    }


def rebuild_shelf_contents():
    """Recompose the shelf cubbies and swap the requested contents."""
    shelf = bpy.data.objects.get("SHELF_Carcass_Cohesive")
    if shelf is None:
        return {"storage_boxes": [], "book_run": [], "cubby_swap": None}

    storage = []
    # Two equal boxes fill the bottom cubby from one inner side to the other.
    box_centers = (1.085, 1.635)
    for index, center_y in enumerate(box_centers):
        body = bpy.data.objects.get("SHELF_StorageBin_%d_Body" % index)
        rim = bpy.data.objects.get("SHELF_StorageRim_%d" % index)
        handle = bpy.data.objects.get("SHELF_StorageHandle_%d" % index)
        body_y = resize_object_axis(body, 1, center_y, 0.53)
        body_x = resize_object_axis(body, 0, 2.48, 0.32)
        # Keep the larger box bodies, but inset each lid enough to leave a
        # deliberate clearance from the vertical shelf walls.
        rim_y = resize_object_axis(rim, 1, center_y, 0.50)
        rim_x = resize_object_axis(rim, 0, 2.48, 0.30)
        if handle is not None:
            handle.location.y = center_y
        if body is not None:
            body["cathode_storage_box_equal_pair"] = True
            body["cathode_storage_box_flush_y"] = True
            body["cathode_storage_box_flush_x"] = True
        storage.append({
            "index": index,
            "center_y": center_y,
            "body": {"y": body_y, "x": body_x},
            "rim": {"y": rim_y, "x": rim_x},
        })

    # The second-lowest cubby gets one continuous run of upright books. The
    # old horizontal stacks are removed so there is no interruption in the run.
    removed_stacks = []
    for ob in list(bpy.data.objects):
        if ob.name.startswith("BOOK_Stack_"):
            removed_stacks.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    lower_books = sorted(
        (ob for ob in bpy.data.objects if ob.name.startswith("BOOK_Lower_")),
        key=lambda ob: ob.name,
    )
    # Restore the earlier book scale: the source spines are roughly 0.034 to
    # 0.040 units wide. Use more individual books to fill the full cubby,
    # with a few deliberately thicker/thinner variations for a natural run.
    widths = (0.034, 0.048, 0.038, 0.055, 0.036, 0.046, 0.041, 0.033,
              0.052, 0.039, 0.047, 0.035, 0.054, 0.040, 0.045, 0.037,
              0.050, 0.034, 0.053, 0.038, 0.046, 0.036)
    run_min, run_max = 0.83, 1.89
    gap = (run_max - run_min - sum(widths)) / (len(widths) - 1)
    run = []
    for ob in list(bpy.data.objects):
        if ob.name.startswith("BOOK_LowerRun_"):
            bpy.data.objects.remove(ob, do_unlink=True)
    # Keep the ten original meshes as templates and make additional copies so
    # the earlier, smaller spine scale can still fill the whole cubby.
    templates = list(lower_books)
    if templates:
        book_collection = (templates[0].users_collection[0]
                           if templates[0].users_collection
                           else bpy.context.scene.collection)
        while len(lower_books) < len(widths):
            template = templates[len(lower_books) % len(templates)]
            duplicate = template.copy()
            duplicate.data = template.data.copy()
            duplicate.name = "BOOK_LowerRun_%02d" % len(lower_books)
            book_collection.objects.link(duplicate)
            lower_books.append(duplicate)
    lower_books = lower_books[:len(widths)]
    cursor = run_min
    for index, (ob, width) in enumerate(zip(lower_books, widths)):
        # Pin the last spine to the right inner edge. This keeps the visible
        # run flush even when the source mesh carries a slight tilt/shear.
        book_min = run_max - width if index == len(widths) - 1 else cursor
        book_max = book_min + width
        center_y = (book_min + book_max) / 2.0
        bounds = set_world_axis_bounds(ob, 1, book_min, book_max)
        if bounds is None:
            ob.dimensions.y = width
            ob.location.y = center_y
        ob["cathode_book_run"] = "second-lowest cubby, end-to-end"
        run.append({"name": ob.name, "center_y": round(center_y, 6),
                    "width": width, "world_y_bounds": bounds})
        cursor += width + gap

    scene = bpy.context.scene
    swap = None
    if not scene.get("cathode_shelf_cubby_swap_applied"):
        # Bottom-to-top cubbies: top center ~1.95 and third-from-bottom center
        # ~1.11. Translate both content groups by the same 0.84-unit delta.
        delta_z = 0.84
        top_prefixes = ("SHELF_Camera_", "SHELF_Globe", "SHELF_Polaroid_")
        top_contents = [ob for ob in bpy.data.objects
                        if ob.name.startswith(top_prefixes)]
        middle_contents = [ob for ob in bpy.data.objects
                           if ob.name.startswith(("BOOK_Mid_", "BOOK_MidStack_"))]
        for ob in top_contents:
            ob.location.z -= delta_z
        for ob in middle_contents:
            ob.location.z += delta_z
        scene["cathode_shelf_cubby_swap_applied"] = True
        swap = {
            "swapped": True,
            "top_group": [ob.name for ob in top_contents],
            "third_from_bottom_group": [ob.name for ob in middle_contents],
            "delta_z": delta_z,
        }

    shelf["cathode_shelf_storage_boxes"] = "two equal boxes flush across bottom cubby"
    shelf["cathode_shelf_second_lowest_books"] = "continuous end-to-end upright run"
    shelf["cathode_shelf_highest_third_swap"] = True
    return {
        "storage_boxes": storage,
        "book_run": run,
        "removed_horizontal_stacks": removed_stacks,
        "cubby_swap": swap,
    }


def seat_horizontal_book_stack():
    """Move the three horizontal top-shelf books flush to the inner wall."""
    target_wall_y = 1.89
    seated = []
    for index in range(3):
        book = bpy.data.objects.get("BOOK_MidStack_%d" % index)
        if book is None or not hasattr(book.data, "vertices"):
            continue
        world_vertices = [book.matrix_world @ vertex.co for vertex in book.data.vertices]
        current_max_y = max(point.y for point in world_vertices)
        book.location.y += target_wall_y - current_max_y
        seated.append({
            "object": book.name,
            "world_y_max": round(target_wall_y, 6),
        })
    bpy.context.view_layer.update()
    bpy.context.scene["cathode_horizontal_book_stack_seated"] = True
    return {"applied": True, "target_wall_y": target_wall_y, "objects": seated}


def restore_and_reorder_horizontal_book_stack():
    """Return the horizontal stack to its shelf position and put the wide book on bottom."""
    # These are the original stack coordinates before the mistaken wall tuck.
    # The larger middle book becomes the bottom layer; the two smaller books
    # sit above it with shared edges and no interpenetration.
    targets = {
        "BOOK_MidStack_1": (1.66, 1.814),
        "BOOK_MidStack_0": (1.66, 1.846),
        "BOOK_MidStack_2": (1.66, 1.876),
    }
    changed = []
    for name, (y, z) in targets.items():
        book = bpy.data.objects.get(name)
        if book is None:
            continue
        book.location.y = y
        book.location.z = z
        changed.append({"object": name, "y": y, "z": z})
    bpy.context.view_layer.update()
    bpy.context.scene["cathode_horizontal_book_stack_reordered"] = True
    return {"applied": True, "order_bottom_to_top": [
        "BOOK_MidStack_1", "BOOK_MidStack_0", "BOOK_MidStack_2"
    ], "objects": changed}


def seat_vertical_book_run():
    """Move the upright book run flush to the right side and rear wall."""
    books = [bpy.data.objects.get("BOOK_Mid_%d" % index) for index in range(10)]
    books = [book for book in books if book is not None and hasattr(book.data, "vertices")]
    if not books:
        return {"applied": False, "reason": "vertical book run missing"}
    all_world = [book.matrix_world @ vertex.co for book in books for vertex in book.data.vertices]
    current_max_y = max(point.y for point in all_world)
    target_wall_y = 1.89
    delta_y = target_wall_y - current_max_y
    for book in books:
        world_matrix = book.matrix_world.copy()
        world_matrix.translation.y += delta_y
        world_matrix.translation.x += 2.58 - sum((book.matrix_world @ v.co).x for v in book.data.vertices) / len(book.data.vertices)
        book.matrix_world = world_matrix
    bpy.context.view_layer.update()
    # Verify that the run reaches the right inner side and is pushed into the rear wall.
    final_vertices = [books[0].matrix_world @ vertex.co for vertex in books[0].data.vertices]
    bpy.context.scene["cathode_vertical_book_run_seated"] = True
    return {
        "applied": True,
        "objects": [book.name for book in books],
        "target_wall_y": target_wall_y,
        "target_back_x": 2.58,
        "delta_y": round(delta_y, 6),
        "leftmost_world_y_min": round(min(point.y for point in final_vertices), 6),
    }


def lean_leftmost_vertical_book():
    """Lean the leftmost upright book gently onto its neighbor, without overlap."""
    book = bpy.data.objects.get("BOOK_Mid_0")
    neighbor = bpy.data.objects.get("BOOK_Mid_1")
    if book is None or neighbor is None:
        return {"applied": False, "reason": "upright book pair missing"}
    book.rotation_euler.x = -0.12
    bpy.context.view_layer.update()
    # Restore this spine to the top run; it was the book that had fallen into
    # the vinyl cubby in the previous iteration.
    verts = [book.matrix_world @ v.co for v in book.data.vertices]
    current_center_z = sum(p.z for p in verts) / len(verts)
    world_matrix = book.matrix_world.copy()
    world_matrix.translation.z += 1.898 - current_center_z
    book.matrix_world = world_matrix
    bpy.context.view_layer.update()
    verts = [book.matrix_world @ v.co for v in book.data.vertices]
    nverts = [neighbor.matrix_world @ v.co for v in neighbor.data.vertices]
    max_y = max(p.y for p in verts)
    nmin_y = min(p.y for p in nverts)
    if max_y >= nmin_y:
        world_matrix = book.matrix_world.copy()
        world_matrix.translation.y -= (max_y - nmin_y) + 0.003
        book.matrix_world = world_matrix
    bpy.context.view_layer.update()
    return {"applied": True, "object": book.name, "rotation_x": -0.12,
            "neighbor": neighbor.name, "clearance": 0.003}


def separate_vinyl_holders():
    """Move both triangular holders outward so records sit inside, not through them."""
    moved = []
    for name, delta in (("SHELF_VinylRack_Left", -0.03), ("SHELF_VinylRack_Right", 0.03)):
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        ob.location.x += delta
        moved.append({"object": name, "delta_x": delta})
    bpy.context.view_layer.update()
    return {"applied": bool(moved), "objects": moved, "outward_offset": 0.03}


def expand_vinyl_system():
    """Extend both rack plates through the cubby depth and widen the records to match."""
    scene = bpy.context.scene
    if scene.get("cathode_vinyl_system_expanded"):
        return {"applied": False, "reason": "already present"}
    # The cubby's depth is world-X; its long horizontal run is world-Y.
    # Keep each end holder at its end of the row while deepening it front-to-back.
    target_x_min, target_x_max = 2.30, 2.62
    holder_changes = []
    for name in ("SHELF_VinylRack_Left", "SHELF_VinylRack_Right"):
        ob = bpy.data.objects.get(name)
        if ob is None or not hasattr(ob.data, "vertices"):
            continue
        world = [ob.matrix_world @ v.co for v in ob.data.vertices]
        old_x = (min(p.x for p in world), max(p.x for p in world))
        old_y = (min(p.y for p in world), max(p.y for p in world))
        old_x_mid = (old_x[0] + old_x[1]) * 0.5
        old_y_mid = (old_y[0] + old_y[1]) * 0.5
        old_x_span = max(old_x[1] - old_x[0], 1e-6)
        old_y_span = max(old_y[1] - old_y[0], 1e-6)
        target_y_min, target_y_max = old_y_mid - 0.025, old_y_mid + 0.025
        inverse = ob.matrix_world.inverted()
        for vertex in ob.data.vertices:
            point = ob.matrix_world @ vertex.co
            point.x = target_x_min + (point.x - old_x_mid) / old_x_span * (target_x_max - target_x_min)
            point.y = target_y_min + (point.y - old_y_mid) / old_y_span * (target_y_max - target_y_min)
            vertex.co = inverse @ point
        # Re-anchor after mesh edits so object transforms cannot leave the rack floating.
        bpy.context.view_layer.update()
        placed = [ob.matrix_world @ v.co for v in ob.data.vertices]
        actual_mid_x = (min(p.x for p in placed) + max(p.x for p in placed)) * 0.5
        ob.location.x += (target_x_min + target_x_max) * 0.5 - actual_mid_x
        bpy.context.view_layer.update()
        holder_changes.append({"object": name, "x_bounds": [target_x_min, target_x_max],
                               "y_bounds": [target_y_min, target_y_max]})
    record_changes = []
    # Widen along the shelf's horizontal axis only; keep the record height and seating unchanged.
    center_x, width_scale = 2.46, 1.30
    for index in range(7):
        ob = bpy.data.objects.get("INTERACT_Vinyl_%d" % index)
        if ob is None or not hasattr(ob.data, "vertices"):
            continue
        inverse = ob.matrix_world.inverted()
        for vertex in ob.data.vertices:
            point = ob.matrix_world @ vertex.co
            point.x = center_x + (point.x - center_x) * width_scale
            vertex.co = inverse @ point
        bpy.context.view_layer.update()
        record_world = [ob.matrix_world @ v.co for v in ob.data.vertices]
        record_min_x = min(p.x for p in record_world)
        world_matrix = ob.matrix_world.copy()
        world_matrix.translation.x += 2.31 - record_min_x
        ob.matrix_world = world_matrix
        record_changes.append(ob.name)
    bpy.context.view_layer.update()
    scene["cathode_vinyl_system_expanded"] = True
    return {"applied": True, "holder_changes": holder_changes, "records": record_changes,
            "record_horizontal_scale": width_scale}


def expand_vinyl_system_v61():
    """Enlarge the vinyl rack/records modestly while keeping them inside the cubby."""
    scene = bpy.context.scene
    if scene.get("cathode_vinyl_system_v61"):
        return {"applied": False, "reason": "already present"}
    holder_changes = []
    for name, outward in (("SHELF_VinylRack_Left", -0.015), ("SHELF_VinylRack_Right", 0.015)):
        ob = bpy.data.objects.get(name)
        if ob is None or not hasattr(ob.data, "vertices"):
            continue
        world_matrix = ob.matrix_world.copy()
        inverse = world_matrix.inverted()
        world = [world_matrix @ v.co for v in ob.data.vertices]
        old_x0, old_x1 = min(p.x for p in world), max(p.x for p in world)
        old_mid = (old_x0 + old_x1) * 0.5
        for vertex in ob.data.vertices:
            point = world_matrix @ vertex.co
            point.x = 2.32 + (point.x - old_mid) / max(old_x1 - old_x0, 1e-6) * 0.32
            vertex.co = inverse @ point
        ob.data.update()
        bpy.context.view_layer.update()
        placed = [ob.matrix_world @ v.co for v in ob.data.vertices]
        actual_mid = (min(p.x for p in placed) + max(p.x for p in placed)) * 0.5
        world_matrix = ob.matrix_world.copy()
        world_matrix.translation.x += 2.48 - actual_mid
        world_matrix.translation.y += outward
        ob.matrix_world = world_matrix
        holder_changes.append(name)
    record_changes = []
    for index in range(7):
        ob = bpy.data.objects.get("INTERACT_Vinyl_%d" % index)
        if ob is None or not hasattr(ob.data, "vertices"):
            continue
        world_matrix = ob.matrix_world.copy()
        inverse = world_matrix.inverted()
        world = [world_matrix @ v.co for v in ob.data.vertices]
        x0, x1 = min(p.x for p in world), max(p.x for p in world)
        xmid = (x0 + x1) * 0.5
        z0 = min(p.z for p in world)
        for vertex in ob.data.vertices:
            point = world_matrix @ vertex.co
            point.x = 2.48 + (point.x - xmid) * 1.20
            point.z = z0 + (point.z - z0) * 1.10
            vertex.co = inverse @ point
        ob.data.update()
        record_changes.append(ob.name)
    bpy.context.view_layer.update()
    scene["cathode_vinyl_system_v61"] = True
    return {"applied": True, "holders": holder_changes, "records": record_changes,
            "holder_depth_bounds_x": [2.32, 2.64], "record_scale": {"x": 1.20, "z": 1.10}}


def clear_vinyl_collisions_v63():
    """Clear both end holders and the steeper screen-right record after expansion."""
    scene = bpy.context.scene
    if scene.get("cathode_vinyl_clearance_v63"):
        return {"applied": False, "reason": "already present"}
    holder_changes = []
    for name in ("SHELF_VinylRack_Left", "SHELF_VinylRack_Right"):
        ob = bpy.data.objects.get(name)
        if ob is None or not hasattr(ob.data, "vertices"):
            continue
        world_matrix = ob.matrix_world.copy()
        inverse = world_matrix.inverted()
        world = [world_matrix @ v.co for v in ob.data.vertices]
        x0, x1 = min(p.x for p in world), max(p.x for p in world)
        for vertex in ob.data.vertices:
            point = world_matrix @ vertex.co
            point.x = 2.32 + (point.x - x0) / max(x1 - x0, 1e-6) * 0.30
            vertex.co = inverse @ point
        ob.data.update()
        holder_changes.append(name)
    # The screen-left holder is the low-Y end in this camera; move it outward.
    left_holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if left_holder is not None:
        matrix = left_holder.matrix_world.copy()
        matrix.translation.y -= 0.008
        left_holder.matrix_world = matrix
    # Give the steeper end sleeve room at its upper corner by shifting the
    # remaining upright sleeves together; their internal spacing is preserved.
    for index in range(1, 7):
        vinyl = bpy.data.objects.get("INTERACT_Vinyl_%d" % index)
        if vinyl is None:
            continue
        matrix = vinyl.matrix_world.copy()
        matrix.translation.y += 0.008
        vinyl.matrix_world = matrix
    end_vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if end_vinyl is not None and hasattr(end_vinyl.data, "vertices"):
        end_vinyl.rotation_euler.x = -0.42
        bpy.context.view_layer.update()
        world = [end_vinyl.matrix_world @ v.co for v in end_vinyl.data.vertices]
        matrix = end_vinyl.matrix_world.copy()
        matrix.translation.z += 1.3775 - min(p.z for p in world)
        end_vinyl.matrix_world = matrix
    bpy.context.view_layer.update()
    scene["cathode_vinyl_clearance_v63"] = True
    return {"applied": True, "holders_trimmed": holder_changes,
            "left_holder_outward_y": -0.008, "upright_row_shift_y": 0.008,
            "end_vinyl_rotation_x": -0.42, "holder_depth_bounds_x": [2.32, 2.62]}


def refine_marked_vinyl_clearance_v64():
    """Apply the two user-marked micro-adjustments without altering other records."""
    scene = bpy.context.scene
    if scene.get("cathode_marked_vinyl_clearance_v64"):
        return {"applied": False, "reason": "already present"}
    holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y -= 0.008
        holder.matrix_world = matrix
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is not None and hasattr(vinyl.data, "vertices"):
        vinyl.rotation_euler.x = -0.48
        bpy.context.view_layer.update()
        world = [vinyl.matrix_world @ v.co for v in vinyl.data.vertices]
        matrix = vinyl.matrix_world.copy()
        matrix.translation.y -= 0.006
        matrix.translation.z += 1.3775 - min(p.z for p in world)
        vinyl.matrix_world = matrix
    bpy.context.view_layer.update()
    scene["cathode_marked_vinyl_clearance_v64"] = True
    return {"applied": True, "left_holder_y_delta": -0.008,
            "right_vinyl_rotation_x": -0.48, "right_vinyl_y_delta": -0.006}


def refine_outline_safe_vinyl_clearance_v65():
    """Add enough clearance for the outline bevel, not only the underlying meshes."""
    scene = bpy.context.scene
    if scene.get("cathode_outline_safe_vinyl_clearance_v65"):
        return {"applied": False, "reason": "already present"}
    holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y -= 0.010
        holder.matrix_world = matrix
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is not None and hasattr(vinyl.data, "vertices"):
        vinyl.rotation_euler.x = -0.52
        bpy.context.view_layer.update()
        matrix = vinyl.matrix_world.copy()
        matrix.translation.y -= 0.006
        vinyl.matrix_world = matrix
        bpy.context.view_layer.update()
        world = [vinyl.matrix_world @ v.co for v in vinyl.data.vertices]
        matrix = vinyl.matrix_world.copy()
        matrix.translation.z += 1.3775 - min(p.z for p in world)
        vinyl.matrix_world = matrix
    bpy.context.view_layer.update()
    scene["cathode_outline_safe_vinyl_clearance_v65"] = True
    return {"applied": True, "left_holder_y_delta": -0.010,
            "right_vinyl_rotation_x": -0.52, "right_vinyl_y_delta": -0.006}


def enforce_visible_outline_clearance_v66():
    """Separate the marked pieces by more than the outline's combined diameter."""
    scene = bpy.context.scene
    if scene.get("cathode_visible_outline_clearance_v66"):
        return {"applied": False, "reason": "already present"}
    holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y -= 0.030
        holder.matrix_world = matrix
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is not None and hasattr(vinyl.data, "vertices"):
        vinyl.rotation_euler.x = -0.52
        bpy.context.view_layer.update()
        matrix = vinyl.matrix_world.copy()
        matrix.translation.y -= 0.020
        vinyl.matrix_world = matrix
        bpy.context.view_layer.update()
        world = [vinyl.matrix_world @ v.co for v in vinyl.data.vertices]
        matrix = vinyl.matrix_world.copy()
        matrix.translation.z += 1.3775 - min(p.z for p in world)
        vinyl.matrix_world = matrix
    bpy.context.view_layer.update()
    scene["cathode_visible_outline_clearance_v66"] = True
    return {"applied": True, "left_holder_y_delta": -0.030,
            "right_vinyl_rotation_x": -0.52, "right_vinyl_y_delta": -0.020}


def apply_annotated_vinyl_fix_v68():
    """Apply the screenshot-annotated screen-left holder and near-upright end record fix."""
    scene = bpy.context.scene
    if scene.get("cathode_annotated_vinyl_fix_v68"):
        return {"applied": False, "reason": "already present"}

    # In the reference camera, the screen-left holder is the object named Right.
    holder = bpy.data.objects.get("SHELF_VinylRack_Right")
    if holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y += 0.020
        holder.matrix_world = matrix

    # The circled screen-right sleeve should be almost upright, with only a slight lean.
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is not None and hasattr(vinyl.data, "vertices"):
        vinyl.rotation_euler.x = -0.10
        bpy.context.view_layer.update()
        world = [vinyl.matrix_world @ v.co for v in vinyl.data.vertices]
        matrix = vinyl.matrix_world.copy()
        matrix.translation.z += 1.3775 - min(p.z for p in world)
        vinyl.matrix_world = matrix

    bpy.context.view_layer.update()
    scene["cathode_annotated_vinyl_fix_v68"] = True
    return {"applied": True, "screen_left_holder_y_delta": 0.020,
            "screen_right_vinyl_rotation_x": -0.10}


def set_near_touching_vinyl_clearance_v69():
    """Lean the end sleeve between its neighbors with outline-safe, near-touching gaps."""
    scene = bpy.context.scene
    if scene.get("cathode_near_touching_vinyl_clearance_v69"):
        return {"applied": False, "reason": "already present"}
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is not None and hasattr(vinyl.data, "vertices"):
        vinyl.rotation_euler.x = -0.29
        bpy.context.view_layer.update()
        world = [vinyl.matrix_world @ v.co for v in vinyl.data.vertices]
        matrix = vinyl.matrix_world.copy()
        matrix.translation.z += 1.3775 - min(p.z for p in world)
        vinyl.matrix_world = matrix
    bpy.context.view_layer.update()
    scene["cathode_near_touching_vinyl_clearance_v69"] = True
    return {"applied": True, "screen_right_vinyl_rotation_x": -0.29}


def seat_connected_outline_vinyl_v75():
    """Clear the shelf with the wireframe itself and retain near-contact above."""
    scene = bpy.context.scene
    if scene.get("cathode_connected_outline_vinyl_v75"):
        return {"applied": False, "reason": "already present"}
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is None:
        return {"applied": False, "reason": "end vinyl missing"}
    matrix = vinyl.matrix_world.copy()
    matrix.translation.y += 0.006
    matrix.translation.z += 0.0095
    vinyl.matrix_world = matrix
    bpy.context.view_layer.update()
    scene["cathode_connected_outline_vinyl_v75"] = True
    return {"applied": True, "world_y_delta": 0.006, "world_z_delta": 0.0095}


def rebuild_second_lowest_book_run_v77():
    """Replace duplicated lower-row books with one outline-safe edge-to-edge run."""
    scene = bpy.context.scene
    if scene.get("cathode_second_lowest_book_run_v77"):
        return {"applied": False, "reason": "already present"}

    originals = sorted(
        (
            ob for ob in bpy.data.objects
            if ob.name.startswith("BOOK_Lower_")
            and ob.name[len("BOOK_Lower_"):].isdigit()
        ),
        key=lambda ob: int(ob.name[len("BOOK_Lower_"):]),
    )
    if not originals:
        return {"applied": False, "reason": "lower book templates missing"}

    for ob in list(bpy.data.objects):
        if ob.name.startswith("BOOK_LowerRun_"):
            bpy.data.objects.remove(ob, do_unlink=True)

    widths = (0.034, 0.048, 0.038, 0.055, 0.036, 0.046, 0.041, 0.033,
              0.052, 0.039, 0.047, 0.035, 0.054)
    books = list(originals)
    collection = (originals[0].users_collection[0]
                  if originals[0].users_collection
                  else scene.collection)
    while len(books) < len(widths):
        template = originals[len(books) % len(originals)]
        duplicate = template.copy()
        duplicate.data = template.data.copy()
        duplicate.name = "BOOK_LowerRun_%02d" % len(books)
        collection.objects.link(duplicate)
        books.append(duplicate)

    run_min, run_max = 0.83, 1.89
    gap = (run_max - run_min - sum(widths)) / (len(widths) - 1)
    cursor = run_min
    rebuilt = []
    for index, (book, width) in enumerate(zip(books, widths)):
        book_min = cursor
        book_max = run_max if index == len(widths) - 1 else book_min + width
        bounds = set_world_axis_bounds(book, 1, book_min, book_max)
        book["cathode_book_run"] = "single second-lowest edge-to-edge run"
        rebuilt.append({"name": book.name, "world_y_bounds": bounds})
        cursor = book_max + gap

    bpy.context.view_layer.update()
    scene["cathode_second_lowest_book_run_v77"] = True
    return {"applied": True, "books": rebuilt, "mesh_gap": gap,
            "run_bounds_y": [run_min, run_max]}


def rebuild_packed_lower_book_run_v80():
    """Create one clean side-to-side lower run with thin connected outlines."""
    scene = bpy.context.scene
    if scene.get("cathode_packed_lower_book_run_v80"):
        return {"applied": False, "reason": "already present"}

    old_books = [ob for ob in bpy.data.objects if ob.name.startswith("BOOK_Lower")]
    material = None
    for ob in old_books:
        if ob.type == "MESH" and ob.data.materials:
            material = ob.data.materials[0]
            break
    collection = (old_books[0].users_collection[0]
                  if old_books and old_books[0].users_collection
                  else scene.collection)
    for ob in old_books:
        bpy.data.objects.remove(ob, do_unlink=True)

    raw_widths = (0.034, 0.048, 0.038, 0.055, 0.036, 0.046, 0.041, 0.033,
                  0.052, 0.039, 0.047, 0.035, 0.054, 0.040, 0.045, 0.037,
                  0.050, 0.034, 0.053, 0.038)
    run_min, run_max = 0.83, 1.89
    width_scale = (run_max - run_min) / sum(raw_widths)
    widths = [width * width_scale for width in raw_widths]
    heights = (0.205, 0.217, 0.229, 0.215, 0.241, 0.211, 0.224,
               0.205, 0.233, 0.217, 0.241, 0.211, 0.229, 0.205,
               0.224, 0.217, 0.237, 0.211, 0.229, 0.205)
    base_z = 0.5375
    depth = 0.16
    cursor = run_min
    created = []
    for index, (width, height) in enumerate(zip(widths, heights)):
        book_min = cursor
        book_max = run_max if index == len(widths) - 1 else cursor + width
        center_y = (book_min + book_max) * 0.5
        half_x, half_y, half_z = depth * 0.5, (book_max - book_min) * 0.5, height * 0.5
        verts = [
            (-half_x, -half_y, -half_z), (-half_x, -half_y, half_z),
            (-half_x, half_y, -half_z), (-half_x, half_y, half_z),
            (half_x, -half_y, -half_z), (half_x, -half_y, half_z),
            (half_x, half_y, -half_z), (half_x, half_y, half_z),
        ]
        faces = [
            (0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4),
            (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6),
        ]
        mesh = bpy.data.meshes.new("BOOK_LowerPacked_%02d_Mesh" % index)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        book = bpy.data.objects.new("BOOK_LowerPacked_%02d" % index, mesh)
        collection.objects.link(book)
        book.location = (2.4, center_y, base_z + half_z)
        if material is not None:
            mesh.materials.append(material)
        book["cathode_book_run"] = "packed side-to-side second-lowest run"
        book["cathode_horizontal_top"] = True
        created.append(book.name)
        cursor = book_max

    bpy.context.view_layer.update()
    scene["cathode_packed_lower_book_run_v80"] = True
    return {"applied": True, "books": created, "mesh_gap": 0.0,
            "run_bounds_y": [run_min, run_max]}


def refine_packed_lower_run_and_holder_v81():
    """Separate thin lower-book outlines and tuck only the screen-right holder inward."""
    scene = bpy.context.scene
    if scene.get("cathode_packed_lower_run_and_holder_v81"):
        return {"applied": False, "reason": "already present"}

    books = sorted(
        (ob for ob in bpy.data.objects if ob.name.startswith("BOOK_LowerPacked_")),
        key=lambda ob: ob.name,
    )
    raw_widths = (0.034, 0.048, 0.038, 0.055, 0.036, 0.046, 0.041, 0.033,
                  0.052, 0.039, 0.047, 0.035, 0.054, 0.040, 0.045, 0.037,
                  0.050, 0.034, 0.053, 0.038)
    run_min, run_max = 0.83, 1.89
    gap = 0.002
    usable_width = run_max - run_min - gap * (len(raw_widths) - 1)
    scale = usable_width / sum(raw_widths)
    widths = [width * scale for width in raw_widths]
    cursor = run_min
    for index, (book, width) in enumerate(zip(books, widths)):
        book_min = cursor
        book_max = run_max if index == len(books) - 1 else cursor + width
        half_width = (book_max - book_min) * 0.5
        for vertex in book.data.vertices:
            vertex.co.y = math.copysign(half_width, vertex.co.y)
        book.location.y = (book_min + book_max) * 0.5
        book["cathode_outline_safe_mesh_gap"] = gap
        cursor = book_max + gap

    # In the reference camera the screen-right support is the object named Left.
    holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y += 0.006
        holder.matrix_world = matrix

    bpy.context.view_layer.update()
    scene["cathode_packed_lower_run_and_holder_v81"] = True
    return {"applied": True, "book_mesh_gap": gap,
            "screen_right_holder_y_delta": 0.006}


def replace_all_outlines_connected_wireframe_v82(coll, move_holder=True):
    """Replace room-wide edge splines with uniformly joined rectangular wireframes."""
    scene = bpy.context.scene
    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        return {"applied": False, "reason": "already present"}

    removable_prefixes = (
        "CATHODE_WIREFRAME_",
        "CATHODE_BOOK_VINYL_",
    )
    for old in list(bpy.data.objects):
        upper = old.name.upper()
        if upper == "CATHODE_FLOWING_OUTLINES" or any(
            upper.startswith(prefix) for prefix in removable_prefixes
        ):
            bpy.data.objects.remove(old, do_unlink=True)

    mat = flow_material()
    count = 0
    for source in list(bpy.data.objects):
        if source.type != "MESH" or source.hide_render:
            continue
        upper = source.name.upper()
        if upper.startswith("CATHODE_") or source.get("cathode_suppress_flow_outline"):
            continue
        if "GLASS" in upper or "RAIN" in upper or not source.data.polygons:
            continue

        outline = source.copy()
        outline.data = source.data.copy()
        outline.name = "CATHODE_WIREFRAME_" + source.name
        coll.objects.link(outline)
        outline.data.materials.clear()
        outline.data.materials.append(mat)
        # Outline the structural source topology. Bevel-generated faces would
        # add stray parallel seams and spoil the clean rectangular joins.
        for modifier in list(outline.modifiers):
            if modifier.type == "BEVEL":
                outline.modifiers.remove(modifier)

        wire = outline.modifiers.new("Roomwide connected outline", "WIREFRAME")
        wire.thickness = 0.010
        wire.offset = -1.0 if upper.startswith("BOOK_LOWERPACKED_") else 1.0
        wire.use_replace = True
        wire.use_even_offset = True
        wire.use_relative_offset = False
        wire.use_boundary = True
        solid = outline.modifiers.new("Roomwide outline depth", "SOLIDIFY")
        solid.thickness = 0.002
        solid.offset = 0.0
        outline["cathode_roomwide_connected_outline_source"] = source.name
        count += 1

    holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if move_holder and holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y += 0.003
        holder.matrix_world = matrix

    bpy.context.view_layer.update()
    scene["cathode_roomwide_connected_wireframes_v82"] = True
    return {"applied": True, "outlined_meshes": count,
            "screen_right_holder_y_delta": 0.003 if move_holder else 0.0,
            "outline_thickness": 0.010}


def thicken_lower_books_and_close_holder_v83(coll):
    """Match upper-book line weight and close the last holder-to-vinyl gap."""
    scene = bpy.context.scene
    if scene.get("cathode_lower_books_and_holder_v83"):
        return {"applied": False, "reason": "already present"}

    corrected = []
    for book in bpy.data.objects:
        if book.type != "MESH" or not book.name.startswith("BOOK_LowerPacked_"):
            continue
        bm = bmesh.new()
        bm.from_mesh(book.data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(book.data)
        bm.free()
        book.data.update()
        corrected.append(book.name)

    holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y += 0.005
        holder.matrix_world = matrix

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_lower_books_and_holder_v83"] = True
    return {"applied": True, "corrected_lower_books": corrected,
            "screen_right_holder_y_delta": 0.005,
            "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0)}


def trim_holder_to_outline_contact_v84(coll):
    """Back the holder off from overlap to a near-zero positive outline gap."""
    scene = bpy.context.scene
    if scene.get("cathode_holder_outline_contact_v84"):
        return {"applied": False, "reason": "already present"}
    holder = bpy.data.objects.get("SHELF_VinylRack_Left")
    if holder is not None:
        matrix = holder.matrix_world.copy()
        matrix.translation.y -= 0.0022
        holder.matrix_world = matrix
    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_holder_outline_contact_v84"] = True
    return {"applied": True, "holder_y_delta": -0.0022,
            "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0)}


def rebuild_lower_row_from_top_books_v86(coll):
    """Fill the second-lowest cubby with exact copies of the upper upright books."""
    scene = bpy.context.scene
    if scene.get("cathode_lower_row_from_top_books_v86"):
        return {"applied": False, "reason": "already present"}

    templates = sorted(
        (
            ob for ob in bpy.data.objects
            if ob.name.startswith("BOOK_Mid_")
            and not ob.name.startswith("BOOK_MidStack_")
        ),
        key=lambda ob: min((ob.matrix_world @ v.co).y for v in ob.data.vertices),
    )
    if not templates:
        return {"applied": False, "reason": "upper upright book templates missing"}

    for old in list(bpy.data.objects):
        if old.name.startswith("BOOK_Lower"):
            bpy.data.objects.remove(old, do_unlink=True)

    run_min, run_max = 0.83, 1.89
    base_z = 0.5375
    count = 22
    selected = [templates[index % len(templates)] for index in range(count)]
    widths = []
    for template in selected:
        points = [template.matrix_world @ vertex.co for vertex in template.data.vertices]
        widths.append(max(point.y for point in points) - min(point.y for point in points))
    gap = (run_max - run_min - sum(widths)) / (count - 1)

    collection = (templates[0].users_collection[0]
                  if templates[0].users_collection
                  else scene.collection)
    cursor = run_min
    created = []
    for index, (template, width) in enumerate(zip(selected, widths)):
        book = template.copy()
        book.data = template.data.copy()
        book.name = "BOOK_LowerFromTop_%02d" % index
        collection.objects.link(book)
        points = [book.matrix_world @ vertex.co for vertex in book.data.vertices]
        current_min_y = min(point.y for point in points)
        current_max_y = max(point.y for point in points)
        current_min_z = min(point.z for point in points)
        target_min_y = cursor
        target_max_y = run_max if index == count - 1 else cursor + width
        matrix = book.matrix_world.copy()
        matrix.translation.y += ((target_min_y + target_max_y) * 0.5
                                 - (current_min_y + current_max_y) * 0.5)
        matrix.translation.z += base_z - current_min_z
        book.matrix_world = matrix
        book["cathode_book_run"] = "upper-book copies filling second-lowest cubby"
        created.append(book.name)
        cursor = target_max_y + gap

    bpy.context.view_layer.update()
    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_lower_row_from_top_books_v86"] = True
    return {"applied": True, "books": created, "gap": gap,
            "run_bounds_y": [run_min, run_max],
            "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0)}


def replace_center_slanted_lower_book_v87(coll):
    """Replace only the center slanted lower-row book with two upright copies."""
    scene = bpy.context.scene
    if scene.get("cathode_center_slanted_lower_book_v87"):
        return {"applied": False, "reason": "already present"}

    target = bpy.data.objects.get("BOOK_LowerFromTop_09")
    previous = bpy.data.objects.get("BOOK_LowerFromTop_08")
    following = bpy.data.objects.get("BOOK_LowerFromTop_10")
    templates = [
        bpy.data.objects.get("BOOK_Mid_0"),
        bpy.data.objects.get("BOOK_Mid_2"),
    ]
    if target is None or previous is None or following is None or any(
            template is None for template in templates):
        return {"applied": False, "reason": "required books missing"}

    def world_bounds(ob):
        points = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
        return {
            "min_y": min(point.y for point in points),
            "max_y": max(point.y for point in points),
            "min_z": min(point.z for point in points),
        }

    previous_max = world_bounds(previous)["max_y"]
    following_min = world_bounds(following)["min_y"]
    widths = []
    for template in templates:
        bounds = world_bounds(template)
        widths.append(bounds["max_y"] - bounds["min_y"])
    gap = (following_min - previous_max - sum(widths)) / 3.0
    if gap <= 0.0:
        return {"applied": False, "reason": "replacement slot too narrow"}

    collection = (target.users_collection[0]
                  if target.users_collection
                  else scene.collection)
    bpy.data.objects.remove(target, do_unlink=True)

    cursor = previous_max + gap
    created = []
    for index, (template, width) in enumerate(zip(templates, widths)):
        book = template.copy()
        book.data = template.data.copy()
        book.name = "BOOK_LowerFromTop_09%c" % (65 + index)
        collection.objects.link(book)
        bounds = world_bounds(book)
        matrix = book.matrix_world.copy()
        matrix.translation.y += cursor - bounds["min_y"]
        matrix.translation.z += 0.5375 - bounds["min_z"]
        book.matrix_world = matrix
        book["cathode_book_run"] = "upright replacement for center slanted book"
        created.append(book.name)
        cursor += width + gap

    bpy.context.view_layer.update()
    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_center_slanted_lower_book_v87"] = True
    return {
        "applied": True,
        "removed": "BOOK_LowerFromTop_09",
        "created": created,
        "gap": gap,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def restack_top_horizontal_books_v88(coll):
    """Restack the three existing horizontal books and center them in depth."""
    scene = bpy.context.scene
    if scene.get("cathode_top_horizontal_books_v88"):
        return {"applied": False, "reason": "already present"}

    # Largest on the shelf, then the medium and smallest books above it.
    ordered = [
        bpy.data.objects.get("BOOK_MidStack_1"),
        bpy.data.objects.get("BOOK_MidStack_0"),
        bpy.data.objects.get("BOOK_MidStack_2"),
    ]
    if any(book is None for book in ordered):
        return {"applied": False, "reason": "horizontal stack missing"}

    def bounds(ob):
        points = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
        return {
            "min_x": min(point.x for point in points),
            "max_x": max(point.x for point in points),
            "min_z": min(point.z for point in points),
            "max_z": max(point.z for point in points),
        }

    target_center_x = 2.48
    base_z = 1.7975
    outline_clearance = 0.020
    cursor_z = base_z
    placements = []
    for book in ordered:
        current = bounds(book)
        matrix = book.matrix_world.copy()
        matrix.translation.x += target_center_x - (
            (current["min_x"] + current["max_x"]) * 0.5
        )
        matrix.translation.z += cursor_z - current["min_z"]
        book.matrix_world = matrix
        bpy.context.view_layer.update()
        placed = bounds(book)
        placements.append((book.name, placed["min_z"], placed["max_z"]))
        cursor_z = placed["max_z"] + outline_clearance

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_top_horizontal_books_v88"] = True
    return {
        "applied": True,
        "placements": placements,
        "center_x": target_center_x,
        "outline_clearance": outline_clearance,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def close_top_horizontal_stack_gaps_v89(coll):
    """Close visible gaps in the horizontal stack without intersecting the books."""
    scene = bpy.context.scene
    if scene.get("cathode_top_horizontal_stack_gaps_v89"):
        return {"applied": False, "reason": "already present"}

    ordered = [
        bpy.data.objects.get("BOOK_MidStack_1"),
        bpy.data.objects.get("BOOK_MidStack_0"),
        bpy.data.objects.get("BOOK_MidStack_2"),
    ]
    if any(book is None for book in ordered):
        return {"applied": False, "reason": "horizontal stack missing"}

    def z_bounds(ob):
        points = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
        return min(point.z for point in points), max(point.z for point in points)

    base_z = 1.7975
    clearance = 0.001
    cursor_z = base_z
    placements = []
    for book in ordered:
        current_min, _ = z_bounds(book)
        matrix = book.matrix_world.copy()
        matrix.translation.z += cursor_z - current_min
        book.matrix_world = matrix
        bpy.context.view_layer.update()
        placed_min, placed_max = z_bounds(book)
        placements.append((book.name, placed_min, placed_max))
        cursor_z = placed_max + clearance

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_top_horizontal_stack_gaps_v89"] = True
    return {
        "applied": True,
        "placements": placements,
        "mesh_clearance": clearance,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def rebuild_record_player_tonearm_v90(coll):
    """Replace the bent wire-like tonearm with one clean rigid arm beam."""
    scene = bpy.context.scene
    if scene.get("cathode_record_player_tonearm_v90"):
        return {"applied": False, "reason": "already present"}

    old_arm = bpy.data.objects.get("INTERACT_RecordPlayer_Arm")
    if old_arm is None:
        return {"applied": False, "reason": "record-player arm missing"}
    arm_material = next((material for material in old_arm.data.materials if material), None)
    collection = (old_arm.users_collection[0]
                  if old_arm.users_collection
                  else scene.collection)
    bpy.data.objects.remove(old_arm, do_unlink=True)

    start = Vector((2.455, 1.255, 1.510))
    end = Vector((2.405, 1.126, 1.504))
    direction = end - start
    length = direction.length
    midpoint = (start + end) * 0.5
    thickness = 0.018

    bm = bmesh.new()
    rotation = direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
    scale = Matrix.Diagonal((thickness, thickness, length, 1.0))
    transform = Matrix.Translation(midpoint) @ rotation @ scale
    bmesh.ops.create_cube(bm, size=1.0, matrix=transform)
    mesh = bpy.data.meshes.new("INTERACT_RecordPlayer_Arm_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    arm = bpy.data.objects.new("INTERACT_RecordPlayer_Arm", mesh)
    collection.objects.link(arm)
    if arm_material is not None:
        arm.data.materials.append(arm_material)
        arm["cathode_grayscale_material"] = arm_material.name
    bevel = arm.modifiers.new("Tonearm edge softening", "BEVEL")
    bevel.width = 0.0025
    bevel.segments = 2
    arm["cathode_tonearm_style"] = "straight conventional rigid arm"
    arm["cathode_tonearm_start"] = tuple(start)
    arm["cathode_tonearm_end"] = tuple(end)

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_record_player_tonearm_v90"] = True
    return {
        "applied": True,
        "arm": arm.name,
        "length": length,
        "thickness": thickness,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def shrink_record_player_headshell_v91(coll):
    """Reduce the headshell to two-thirds size while keeping its arm joint fixed."""
    scene = bpy.context.scene
    if scene.get("cathode_record_player_headshell_v91"):
        return {"applied": False, "reason": "already present"}

    headshell = bpy.data.objects.get("INTERACT_RecordPlayer_Headshell")
    if headshell is None or headshell.type != "MESH":
        return {"applied": False, "reason": "record-player headshell missing"}

    points = [headshell.matrix_world @ vertex.co for vertex in headshell.data.vertices]
    anchor = Vector((
        (min(point.x for point in points) + max(point.x for point in points)) * 0.5,
        max(point.y for point in points),
        (min(point.z for point in points) + max(point.z for point in points)) * 0.5,
    ))
    inverse = headshell.matrix_world.inverted()
    factor = 2.0 / 3.0
    for vertex in headshell.data.vertices:
        world = headshell.matrix_world @ vertex.co
        vertex.co = inverse @ (anchor + (world - anchor) * factor)
    headshell.data.update()
    headshell["cathode_headshell_scale_v91"] = factor
    headshell["cathode_headshell_fixed_anchor"] = tuple(anchor)

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)
    scene["cathode_record_player_headshell_v91"] = True
    return {
        "applied": True,
        "headshell": headshell.name,
        "scale_factor": factor,
        "fixed_anchor": tuple(anchor),
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def slim_record_player_arm_and_headshell_v92(coll):
    """Slim the tonearm geometry and use finer outlines on its two end pieces."""
    scene = bpy.context.scene
    if scene.get("cathode_slim_record_player_arm_v92"):
        return {"applied": False, "reason": "already present"}

    arm = bpy.data.objects.get("INTERACT_RecordPlayer_Arm")
    headshell = bpy.data.objects.get("INTERACT_RecordPlayer_Headshell")
    if arm is None or arm.type != "MESH" or headshell is None or headshell.type != "MESH":
        return {"applied": False, "reason": "tonearm components missing"}

    # Preserve the arm's full pivot-to-headshell length while reducing only
    # its cross-section around the original centerline.
    start = Vector(arm.get("cathode_tonearm_start", (2.455, 1.255, 1.510)))
    end = Vector(arm.get("cathode_tonearm_end", (2.405, 1.126, 1.504)))
    axis = (end - start).normalized()
    arm_factor = 0.60
    arm_inverse = arm.matrix_world.inverted()
    for vertex in arm.data.vertices:
        world = arm.matrix_world @ vertex.co
        centerline = start + axis * (world - start).dot(axis)
        vertex.co = arm_inverse @ (centerline + (world - centerline) * arm_factor)
    arm.data.update()
    for modifier in arm.modifiers:
        if modifier.type == "BEVEL":
            modifier.width *= arm_factor
    arm["cathode_tonearm_cross_section_factor_v92"] = arm_factor

    # Keep the headshell's useful length and rear attachment point, reducing
    # only its local width and height.
    shell_factor = 0.70
    local_center_x = sum(vertex.co.x for vertex in headshell.data.vertices) / len(headshell.data.vertices)
    local_center_z = sum(vertex.co.z for vertex in headshell.data.vertices) / len(headshell.data.vertices)
    for vertex in headshell.data.vertices:
        vertex.co.x = local_center_x + (vertex.co.x - local_center_x) * shell_factor
        vertex.co.z = local_center_z + (vertex.co.z - local_center_z) * shell_factor
    headshell.data.update()
    headshell["cathode_headshell_width_height_factor_v92"] = shell_factor

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    outline_thickness = 0.0045
    outline_depth = 0.0012
    adjusted = []
    for source in (arm, headshell):
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source.name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = outline_thickness
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = outline_depth
        adjusted.append(outline.name)

    scene["cathode_slim_record_player_arm_v92"] = True
    return {
        "applied": True,
        "arm_cross_section_factor": arm_factor,
        "headshell_width_height_factor": shell_factor,
        "outline_thickness": outline_thickness,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def slim_record_player_pivot_and_add_mount_v93(coll):
    """Reduce the pivot and add a centered pin/yoke that visibly holds the arm."""
    scene = bpy.context.scene
    if scene.get("cathode_record_player_pivot_mount_v93"):
        return {"applied": False, "reason": "already present"}

    pivot = bpy.data.objects.get("INTERACT_RecordPlayer_Pivot")
    arm = bpy.data.objects.get("INTERACT_RecordPlayer_Arm")
    if pivot is None or pivot.type != "MESH" or arm is None or arm.type != "MESH":
        return {"applied": False, "reason": "pivot or tonearm missing"}

    pivot_points = [pivot.matrix_world @ vertex.co for vertex in pivot.data.vertices]
    pivot_center_x = (min(point.x for point in pivot_points) + max(point.x for point in pivot_points)) * 0.5
    pivot_center_y = (min(point.y for point in pivot_points) + max(point.y for point in pivot_points)) * 0.5
    pivot_base_z = min(point.z for point in pivot_points)
    pivot_anchor = Vector((pivot_center_x, pivot_center_y, pivot_base_z))
    pivot_factor = 0.75
    pivot_inverse = pivot.matrix_world.inverted()
    for vertex in pivot.data.vertices:
        world = pivot.matrix_world @ vertex.co
        vertex.co = pivot_inverse @ (pivot_anchor + (world - pivot_anchor) * pivot_factor)
    pivot.data.update()
    pivot["cathode_pivot_uniform_scale_v93"] = pivot_factor

    old_mount = bpy.data.objects.get("INTERACT_RecordPlayer_PivotMount")
    if old_mount is not None:
        bpy.data.objects.remove(old_mount, do_unlink=True)

    material = next((item for item in pivot.data.materials if item), None)
    collection = (pivot.users_collection[0]
                  if pivot.users_collection
                  else scene.collection)
    pin_center = Vector((pivot_center_x, pivot_center_y, 1.501))
    pin_radius = 0.011
    pin_depth = 0.030
    arm_start = Vector(arm.get("cathode_tonearm_start", (2.455, 1.255, 1.510)))
    bridge_start = Vector((pivot_center_x, pivot_center_y, arm_start.z))
    bridge_direction = arm_start - bridge_start

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=8,
        radius1=pin_radius,
        radius2=pin_radius,
        depth=pin_depth,
        matrix=Matrix.Translation(pin_center),
    )
    if bridge_direction.length > 1.0e-6:
        bridge_midpoint = (bridge_start + arm_start) * 0.5
        bridge_rotation = bridge_direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bridge_scale = Matrix.Diagonal((0.012, 0.012, bridge_direction.length + 0.010, 1.0))
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(bridge_midpoint) @ bridge_rotation @ bridge_scale,
        )
    mesh = bpy.data.meshes.new("INTERACT_RecordPlayer_PivotMount_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    mount = bpy.data.objects.new("INTERACT_RecordPlayer_PivotMount", mesh)
    collection.objects.link(mount)
    if material is not None:
        mount.data.materials.append(material)
    bevel = mount.modifiers.new("Pivot mount edge softening", "BEVEL")
    bevel.width = 0.0015
    bevel.segments = 2
    mount["cathode_pivot_mount"] = "center pin and arm bridge"

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    fine_sources = (
        "INTERACT_RecordPlayer_Arm",
        "INTERACT_RecordPlayer_Headshell",
        "INTERACT_RecordPlayer_Pivot",
        "INTERACT_RecordPlayer_PivotMount",
    )
    outline_thickness = 0.0045
    outline_depth = 0.0012
    adjusted = []
    for source_name in fine_sources:
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = outline_thickness
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = outline_depth
        adjusted.append(outline.name)

    scene["cathode_record_player_pivot_mount_v93"] = True
    return {
        "applied": True,
        "pivot_scale_factor": pivot_factor,
        "mount": mount.name,
        "outline_thickness": outline_thickness,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def lower_record_player_arm_and_pin_v94(coll):
    """Lower and flatten the tonearm, then shorten its pivot pin to meet it."""
    scene = bpy.context.scene
    if scene.get("cathode_lower_record_player_arm_v94"):
        return {"applied": False, "reason": "already present"}

    arm = bpy.data.objects.get("INTERACT_RecordPlayer_Arm")
    pivot = bpy.data.objects.get("INTERACT_RecordPlayer_Pivot")
    if arm is None or arm.type != "MESH" or pivot is None or pivot.type != "MESH":
        return {"applied": False, "reason": "tonearm components missing"}

    arm_material = next((item for item in arm.data.materials if item), None)
    arm_start = Vector((2.455, 1.255, 1.502))
    arm_end = Vector((2.405, 1.126, 1.500))
    arm_direction = arm_end - arm_start
    arm_thickness = 0.0108
    arm_midpoint = (arm_start + arm_end) * 0.5

    bm = bmesh.new()
    arm_rotation = arm_direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
    arm_scale = Matrix.Diagonal((arm_thickness, arm_thickness, arm_direction.length, 1.0))
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Translation(arm_midpoint) @ arm_rotation @ arm_scale,
    )
    new_arm_mesh = bpy.data.meshes.new("INTERACT_RecordPlayer_Arm_Mesh_v94")
    bm.to_mesh(new_arm_mesh)
    bm.free()
    old_arm_mesh = arm.data
    arm.data = new_arm_mesh
    arm.matrix_world = Matrix.Identity(4)
    if arm_material is not None:
        arm.data.materials.append(arm_material)
    if old_arm_mesh.users == 0:
        bpy.data.meshes.remove(old_arm_mesh)
    arm["cathode_tonearm_start"] = tuple(arm_start)
    arm["cathode_tonearm_end"] = tuple(arm_end)
    arm["cathode_tonearm_lowered_v94"] = True

    old_mount = bpy.data.objects.get("INTERACT_RecordPlayer_PivotMount")
    if old_mount is not None:
        bpy.data.objects.remove(old_mount, do_unlink=True)

    pivot_points = [pivot.matrix_world @ vertex.co for vertex in pivot.data.vertices]
    pivot_center_x = (min(point.x for point in pivot_points) + max(point.x for point in pivot_points)) * 0.5
    pivot_center_y = (min(point.y for point in pivot_points) + max(point.y for point in pivot_points)) * 0.5
    pivot_top_z = max(point.z for point in pivot_points)
    pin_bottom = pivot_top_z - 0.003
    pin_top = arm_start.z + arm_thickness * 0.55
    pin_depth = pin_top - pin_bottom
    pin_center = Vector((pivot_center_x, pivot_center_y, (pin_bottom + pin_top) * 0.5))
    pin_radius = 0.010
    bridge_start = Vector((pivot_center_x, pivot_center_y, arm_start.z))
    bridge_direction = arm_start - bridge_start

    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=8,
        radius1=pin_radius,
        radius2=pin_radius,
        depth=pin_depth,
        matrix=Matrix.Translation(pin_center),
    )
    if bridge_direction.length > 1.0e-6:
        bridge_midpoint = (bridge_start + arm_start) * 0.5
        bridge_rotation = bridge_direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bridge_scale = Matrix.Diagonal((0.011, 0.011, bridge_direction.length + 0.009, 1.0))
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation(bridge_midpoint) @ bridge_rotation @ bridge_scale,
        )
    mount_mesh = bpy.data.meshes.new("INTERACT_RecordPlayer_PivotMount_Mesh_v94")
    bm.to_mesh(mount_mesh)
    bm.free()
    collection = (pivot.users_collection[0]
                  if pivot.users_collection
                  else scene.collection)
    mount = bpy.data.objects.new("INTERACT_RecordPlayer_PivotMount", mount_mesh)
    collection.objects.link(mount)
    pivot_material = next((item for item in pivot.data.materials if item), None)
    if pivot_material is not None:
        mount.data.materials.append(pivot_material)
    bevel = mount.modifiers.new("Pivot mount edge softening", "BEVEL")
    bevel.width = 0.0013
    bevel.segments = 2
    mount["cathode_pivot_mount"] = "shortened pin for lowered arm"

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    fine_sources = (
        "INTERACT_RecordPlayer_Arm",
        "INTERACT_RecordPlayer_Headshell",
        "INTERACT_RecordPlayer_Pivot",
        "INTERACT_RecordPlayer_PivotMount",
    )
    outline_thickness = 0.0045
    adjusted = []
    for source_name in fine_sources:
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = outline_thickness
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = 0.0012
        adjusted.append(outline.name)

    scene["cathode_lower_record_player_arm_v94"] = True
    return {
        "applied": True,
        "arm_start": tuple(arm_start),
        "arm_end": tuple(arm_end),
        "pin_depth": pin_depth,
        "mount": mount.name,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def fit_record_player_to_base_and_shelf_v95(coll):
    """Fit the circular assembly inside its base and pull the player off the back wall."""
    scene = bpy.context.scene
    if scene.get("cathode_record_player_fit_v95"):
        return {"applied": False, "reason": "already present"}

    circular_names = (
        "INTERACT_RecordPlayer_Disc",
        "INTERACT_RecordPlayer_Record",
        "INTERACT_RecordPlayer_Label",
    )
    circular = [bpy.data.objects.get(name) for name in circular_names]
    base = bpy.data.objects.get("INTERACT_RecordPlayer_Base")
    if base is None or any(item is None or item.type != "MESH" for item in circular):
        return {"applied": False, "reason": "record-player geometry missing"}

    center = Vector((2.49, 1.10, 0.0))
    scale_factor = 0.85
    for item in circular:
        inverse = item.matrix_world.inverted()
        for vertex in item.data.vertices:
            world = item.matrix_world @ vertex.co
            world.x = center.x + (world.x - center.x) * scale_factor
            world.y = center.y + (world.y - center.y) * scale_factor
            vertex.co = inverse @ world
        item.data.update()
        item["cathode_record_xy_scale_v95"] = scale_factor

    # X is the shelf depth axis here; negative X pulls the complete player
    # forward and away from the closed back panel.
    forward_delta_x = -0.025
    moved = []
    for item in bpy.data.objects:
        if not item.name.startswith("INTERACT_RecordPlayer_"):
            continue
        matrix = item.matrix_world.copy()
        matrix.translation.x += forward_delta_x
        item.matrix_world = matrix
        moved.append(item.name)

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    fine_sources = (
        "INTERACT_RecordPlayer_Arm",
        "INTERACT_RecordPlayer_Headshell",
        "INTERACT_RecordPlayer_Pivot",
        "INTERACT_RecordPlayer_PivotMount",
    )
    adjusted = []
    for source_name in fine_sources:
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = 0.0045
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = 0.0012
        adjusted.append(outline.name)

    scene["cathode_record_player_fit_v95"] = True
    return {
        "applied": True,
        "circular_scale_factor": scale_factor,
        "forward_delta_x": forward_delta_x,
        "moved_objects": moved,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def resize_camera_and_rotate_polaroids_v96(coll):
    """Shrink the shelf camera and restack four Polaroids in landscape orientation."""
    scene = bpy.context.scene
    if scene.get("cathode_camera_polaroids_v96"):
        return {"applied": False, "reason": "already present"}

    removed = []
    for name in ("SHELF_Camera_Flash", "SHELF_Camera_Viewfinder"):
        item = bpy.data.objects.get(name)
        if item is not None:
            removed.append(item.name)
            bpy.data.objects.remove(item, do_unlink=True)

    camera_parts = [
        item for item in bpy.data.objects
        if item.name.startswith("SHELF_Camera_") and item.type == "MESH"
    ]
    if not camera_parts:
        return {"applied": False, "reason": "camera components missing"}
    camera_factor = 0.78
    camera_anchor = Vector((2.50, 1.74, 0.9575))
    camera_transform = (
        Matrix.Translation(camera_anchor)
        @ Matrix.Scale(camera_factor, 4)
        @ Matrix.Translation(-camera_anchor)
    )
    for item in camera_parts:
        item.matrix_world = camera_transform @ item.matrix_world
        item["cathode_camera_scale_v96"] = camera_factor

    target_centers = {
        "A": Vector((2.470, 1.300, 0.0)),
        "B": Vector((2.455, 1.360, 0.0)),
        "C": Vector((2.480, 1.420, 0.0)),
        "D": Vector((2.465, 1.480, 0.0)),
    }
    clockwise = Matrix.Rotation(-math.pi * 0.5, 4, "Z")
    polaroids = []
    for letter, target in target_centers.items():
        card = bpy.data.objects.get("SHELF_Polaroid_%s_Card" % letter)
        photo = bpy.data.objects.get("SHELF_Polaroid_%s_Photo" % letter)
        if card is None or photo is None:
            return {"applied": False, "reason": "Polaroid pair %s missing" % letter}
        center = Vector((card.matrix_world.translation.x, card.matrix_world.translation.y, 0.0))
        transform = Matrix.Translation(target) @ clockwise @ Matrix.Translation(-center)
        card.matrix_world = transform @ card.matrix_world
        photo.matrix_world = transform @ photo.matrix_world
        card["cathode_polaroid_orientation_v96"] = "landscape, clockwise 90 degrees"
        photo["cathode_polaroid_orientation_v96"] = "landscape, clockwise 90 degrees"
        polaroids.extend((card.name, photo.name))

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    fine_sources = (
        "INTERACT_RecordPlayer_Arm",
        "INTERACT_RecordPlayer_Headshell",
        "INTERACT_RecordPlayer_Pivot",
        "INTERACT_RecordPlayer_PivotMount",
    )
    adjusted = []
    for source_name in fine_sources:
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = 0.0045
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = 0.0012
        adjusted.append(outline.name)

    scene["cathode_camera_polaroids_v96"] = True
    return {
        "applied": True,
        "camera_scale_factor": camera_factor,
        "removed_camera_parts": removed,
        "polaroid_objects": polaroids,
        "polaroid_rotation_degrees": -90.0,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def shrink_camera_lens_and_two_layer_polaroids_v97(coll):
    """Shrink only the lens and arrange Polaroids on two alternating layers."""
    scene = bpy.context.scene
    if scene.get("cathode_camera_lens_polaroids_v97"):
        return {"applied": False, "reason": "already present"}

    lens_outer = bpy.data.objects.get("SHELF_Camera_LensOuter")
    lens_glass = bpy.data.objects.get("SHELF_Camera_LensGlass")
    if lens_outer is None or lens_glass is None:
        return {"applied": False, "reason": "camera lens components missing"}

    outer_points = [lens_outer.matrix_world @ vertex.co for vertex in lens_outer.data.vertices]
    lens_anchor = Vector((
        max(point.x for point in outer_points),
        (min(point.y for point in outer_points) + max(point.y for point in outer_points)) * 0.5,
        (min(point.z for point in outer_points) + max(point.z for point in outer_points)) * 0.5,
    ))
    lens_factor = 0.72
    lens_transform = (
        Matrix.Translation(lens_anchor)
        @ Matrix.Scale(lens_factor, 4)
        @ Matrix.Translation(-lens_anchor)
    )
    for item in (lens_outer, lens_glass):
        item.matrix_world = lens_transform @ item.matrix_world
        item["cathode_lens_scale_v97"] = lens_factor

    # A/C share the bottom level; B/D share the top level. Each photo keeps
    # its existing placement relative to its card.
    layer_card_min_z = {
        "A": 0.958,
        "B": 0.965,
        "C": 0.958,
        "D": 0.965,
    }
    layer_assignments = []
    for letter, target_min_z in layer_card_min_z.items():
        card = bpy.data.objects.get("SHELF_Polaroid_%s_Card" % letter)
        photo = bpy.data.objects.get("SHELF_Polaroid_%s_Photo" % letter)
        if card is None or photo is None:
            return {"applied": False, "reason": "Polaroid pair %s missing" % letter}
        points = [card.matrix_world @ vertex.co for vertex in card.data.vertices]
        current_min_z = min(point.z for point in points)
        delta_z = target_min_z - current_min_z
        for item in (card, photo):
            matrix = item.matrix_world.copy()
            matrix.translation.z += delta_z
            item.matrix_world = matrix
            item["cathode_polaroid_layer_v97"] = (
                "bottom" if letter in ("A", "C") else "top"
            )
        layer_assignments.append((letter, "bottom" if letter in ("A", "C") else "top"))

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    adjusted = []
    for source_name in (
        "INTERACT_RecordPlayer_Arm",
        "INTERACT_RecordPlayer_Headshell",
        "INTERACT_RecordPlayer_Pivot",
        "INTERACT_RecordPlayer_PivotMount",
    ):
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = 0.0045
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = 0.0012
        adjusted.append(outline.name)

    scene["cathode_camera_lens_polaroids_v97"] = True
    return {
        "applied": True,
        "lens_scale_factor": lens_factor,
        "lens_anchor": tuple(lens_anchor),
        "polaroid_layers": layer_assignments,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def raise_top_polaroid_layer_v98(coll):
    """Raise B/D enough for their outlines to clear the lower A/C layer."""
    scene = bpy.context.scene
    if scene.get("cathode_polaroid_top_clearance_v98"):
        return {"applied": False, "reason": "already present"}

    bottom_items = []
    for letter in ("A", "C"):
        for suffix in ("Card", "Photo"):
            item = bpy.data.objects.get("SHELF_Polaroid_%s_%s" % (letter, suffix))
            if item is None:
                return {"applied": False, "reason": "lower Polaroid layer missing"}
            bottom_items.append(item)
    bottom_top_z = max(
        (item.matrix_world @ vertex.co).z
        for item in bottom_items
        for vertex in item.data.vertices
    )

    outline_safe_gap = 0.020
    target_top_card_min_z = bottom_top_z + outline_safe_gap
    moved = []
    for letter in ("B", "D"):
        card = bpy.data.objects.get("SHELF_Polaroid_%s_Card" % letter)
        photo = bpy.data.objects.get("SHELF_Polaroid_%s_Photo" % letter)
        if card is None or photo is None:
            return {"applied": False, "reason": "upper Polaroid layer missing"}
        card_min_z = min(
            (card.matrix_world @ vertex.co).z for vertex in card.data.vertices
        )
        delta_z = target_top_card_min_z - card_min_z
        for item in (card, photo):
            matrix = item.matrix_world.copy()
            matrix.translation.z += delta_z
            item.matrix_world = matrix
            item["cathode_polaroid_outline_clearance_v98"] = outline_safe_gap
            moved.append(item.name)

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    adjusted = []
    for source_name in (
        "INTERACT_RecordPlayer_Arm",
        "INTERACT_RecordPlayer_Headshell",
        "INTERACT_RecordPlayer_Pivot",
        "INTERACT_RecordPlayer_PivotMount",
    ):
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = 0.0045
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = 0.0012
        adjusted.append(outline.name)

    scene["cathode_polaroid_top_clearance_v98"] = True
    return {
        "applied": True,
        "bottom_layer_top_z": bottom_top_z,
        "top_layer_card_min_z": target_top_card_min_z,
        "outline_safe_gap": outline_safe_gap,
        "moved": moved,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def spread_and_lower_polaroids_v99(coll):
    """Clear same-layer horizontal overlaps and tighten the two vertical layers."""
    scene = bpy.context.scene
    if scene.get("cathode_polaroid_spread_v99"):
        return {"applied": False, "reason": "already present"}

    target_center_y = {
        "A": 1.250,
        "B": 1.310,
        "C": 1.455,
        "D": 1.520,
    }
    moved_xy = []
    for letter, target_y in target_center_y.items():
        card = bpy.data.objects.get("SHELF_Polaroid_%s_Card" % letter)
        photo = bpy.data.objects.get("SHELF_Polaroid_%s_Photo" % letter)
        if card is None or photo is None:
            return {"applied": False, "reason": "Polaroid pair %s missing" % letter}
        delta_y = target_y - card.matrix_world.translation.y
        for item in (card, photo):
            matrix = item.matrix_world.copy()
            matrix.translation.y += delta_y
            item.matrix_world = matrix
            item["cathode_polaroid_spread_y_v99"] = target_y
        moved_xy.append((letter, target_y))

    bottom_items = []
    for letter in ("A", "C"):
        for suffix in ("Card", "Photo"):
            bottom_items.append(
                bpy.data.objects.get("SHELF_Polaroid_%s_%s" % (letter, suffix))
            )
    bottom_top_z = max(
        (item.matrix_world @ vertex.co).z
        for item in bottom_items
        for vertex in item.data.vertices
    )
    tighter_gap = 0.012
    target_top_card_min_z = bottom_top_z + tighter_gap
    moved_z = []
    for letter in ("B", "D"):
        card = bpy.data.objects.get("SHELF_Polaroid_%s_Card" % letter)
        photo = bpy.data.objects.get("SHELF_Polaroid_%s_Photo" % letter)
        current_min_z = min(
            (card.matrix_world @ vertex.co).z for vertex in card.data.vertices
        )
        delta_z = target_top_card_min_z - current_min_z
        for item in (card, photo):
            matrix = item.matrix_world.copy()
            matrix.translation.z += delta_z
            item.matrix_world = matrix
            item["cathode_polaroid_tighter_layer_gap_v99"] = tighter_gap
        moved_z.append((letter, delta_z))

    if scene.get("cathode_roomwide_connected_wireframes_v82"):
        del scene["cathode_roomwide_connected_wireframes_v82"]
    rebuilt = replace_all_outlines_connected_wireframe_v82(coll, move_holder=False)

    polaroid_outline_thickness = 0.006
    polaroid_outlines = []
    for letter in "ABCD":
        for suffix in ("Card", "Photo"):
            source_name = "SHELF_Polaroid_%s_%s" % (letter, suffix)
            outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
            if outline is None:
                continue
            for modifier in outline.modifiers:
                if modifier.type == "WIREFRAME":
                    modifier.thickness = polaroid_outline_thickness
                elif modifier.type == "SOLIDIFY":
                    modifier.thickness = 0.0015
            polaroid_outlines.append(outline.name)

    adjusted = []
    for source_name in (
        "INTERACT_RecordPlayer_Arm",
        "INTERACT_RecordPlayer_Headshell",
        "INTERACT_RecordPlayer_Pivot",
        "INTERACT_RecordPlayer_PivotMount",
    ):
        outline = bpy.data.objects.get("CATHODE_WIREFRAME_" + source_name)
        if outline is None:
            continue
        for modifier in outline.modifiers:
            if modifier.type == "WIREFRAME":
                modifier.thickness = 0.0045
            elif modifier.type == "SOLIDIFY":
                modifier.thickness = 0.0012
        adjusted.append(outline.name)

    scene["cathode_polaroid_spread_v99"] = True
    return {
        "applied": True,
        "horizontal_centers_y": moved_xy,
        "top_layer_moves_z": moved_z,
        "vertical_gap": tighter_gap,
        "polaroid_outline_thickness": polaroid_outline_thickness,
        "polaroid_outlines": polaroid_outlines,
        "adjusted_outlines": adjusted,
        "roomwide_outlines_rebuilt": rebuilt.get("outlined_meshes", 0),
    }


def rebuild_dark_windows_and_looping_rain_v100(coll):
    """Remove the exterior view and add a seamless 240-frame window-rain loop."""
    scene = bpy.context.scene
    if scene.get("cathode_dark_window_rain_v100"):
        return {"applied": False, "reason": "already present"}

    exterior = bpy.data.objects.get("CATHODE_WINDOW_EXTERIOR_FLAT")
    if exterior is not None:
        bpy.data.objects.remove(exterior, do_unlink=True)

    dark_glass = bpy.data.materials.get("CATHODE_WINDOW_DARK_GLASS")
    if dark_glass is None:
        dark_glass = bpy.data.materials.new("CATHODE_WINDOW_DARK_GLASS")
        dark_glass.use_nodes = True
        bsdf = dark_glass.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            base = bsdf.inputs.get("Base Color")
            if base is not None:
                base.default_value = (0.003, 0.004, 0.006, 1.0)
            roughness = bsdf.inputs.get("Roughness")
            if roughness is not None:
                roughness.default_value = 0.26
            metallic = bsdf.inputs.get("Metallic")
            if metallic is not None:
                metallic.default_value = 0.08

    glass_objects = []
    for name in ("WINDOW_1_Glass", "WINDOW_2_Glass"):
        glass = bpy.data.objects.get(name)
        if glass is None:
            return {"applied": False, "reason": "%s missing" % name}
        glass.hide_render = False
        glass.hide_viewport = False
        glass.data.materials.clear()
        glass.data.materials.append(dark_glass)
        glass["cathode_window_style_v100"] = "dark exterior void"
        glass_objects.append(glass.name)

    rain_material = bpy.data.materials.get("CATHODE_RAIN_GLINT")
    if rain_material is None:
        rain_material = bpy.data.materials.new("CATHODE_RAIN_GLINT")
        rain_material.use_nodes = True
        bsdf = rain_material.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            base = bsdf.inputs.get("Base Color")
            if base is not None:
                base.default_value = (0.42, 0.48, 0.56, 1.0)
            roughness = bsdf.inputs.get("Roughness")
            if roughness is not None:
                roughness.default_value = 0.18
            emission = bsdf.inputs.get("Emission Color")
            if emission is None:
                emission = bsdf.inputs.get("Emission")
            if emission is not None:
                emission.default_value = (0.32, 0.39, 0.50, 1.0)
            emission_strength = bsdf.inputs.get("Emission Strength")
            if emission_strength is not None:
                emission_strength.default_value = 1.4

    for old in list(bpy.data.objects):
        if old.name.startswith("CATHODE_RAIN_Window"):
            bpy.data.objects.remove(old, do_unlink=True)
    old_mesh = bpy.data.meshes.get("CATHODE_RAIN_DropletMesh")
    if old_mesh is not None and old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

    rain_collection = bpy.data.collections.get("CATHODE_WINDOW_RAIN")
    if rain_collection is None:
        rain_collection = bpy.data.collections.new("CATHODE_WINDOW_RAIN")
        scene.collection.children.link(rain_collection)

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    droplet_mesh = bpy.data.meshes.new("CATHODE_RAIN_DropletMesh")
    bm.to_mesh(droplet_mesh)
    bm.free()
    droplet_mesh.materials.append(rain_material)

    scene.frame_start = 1
    scene.frame_end = 240
    scene.render.fps = 24
    loop_frames = 240
    rng = __import__("random").Random(20260828)
    window_ranges = (
        (1, -1.98, -0.82),
        (2, 0.82, 1.98),
    )
    drops = []
    for window_index, min_x, max_x in window_ranges:
        for index in range(18):
            drop = bpy.data.objects.new(
                "CATHODE_RAIN_Window%d_%02d" % (window_index, index),
                droplet_mesh,
            )
            rain_collection.objects.link(drop)
            x = rng.uniform(min_x, max_x)
            top_z = rng.uniform(2.42, 2.57)
            bottom_z = rng.uniform(1.30, 1.58)
            phase = rng.randrange(1, loop_frames + 1)
            lifetime = rng.randrange(58, 112)
            width = rng.uniform(0.0055, 0.0105)
            depth = rng.uniform(0.0020, 0.0034)
            height = rng.uniform(0.035, 0.075)
            drop.location = (x, 2.692, top_z)
            drop.scale = (0.0, 0.0, 0.0)
            drop["cathode_rain_phase"] = phase
            drop["cathode_rain_lifetime"] = lifetime
            drop["cathode_rain_loop_frames"] = loop_frames
            drop["cathode_rain_behavior"] = "roll, impact pop, disappear"

            event_offsets = (-loop_frames, 0, loop_frames)
            for offset in event_offsets:
                start = phase + offset
                keyframes = (
                    (start, top_z, (0.0, 0.0, 0.0)),
                    (start + 3, top_z - 0.018, (width, depth, height)),
                    (start + lifetime - 10, bottom_z + 0.060, (width, depth, height)),
                    (start + lifetime - 5, bottom_z, (width * 2.15, depth, height * 0.28)),
                    (start + lifetime, bottom_z, (0.0, 0.0, 0.0)),
                    (start + lifetime + 1, top_z, (0.0, 0.0, 0.0)),
                )
                for frame, z_value, scale_value in keyframes:
                    drop.location.z = z_value
                    drop.scale = scale_value
                    drop.keyframe_insert(data_path="location", index=2, frame=frame)
                    drop.keyframe_insert(data_path="scale", frame=frame)

            action = drop.animation_data.action if drop.animation_data else None
            if action is not None:
                for layer in action.layers:
                    for strip in layer.strips:
                        for channelbag in strip.channelbags:
                            for curve in channelbag.fcurves:
                                for keyframe in curve.keyframe_points:
                                    keyframe.interpolation = "LINEAR"
            drops.append(drop.name)

    moon_settings = []
    for name in ("LIGHT_WindowWest", "LIGHT_WindowEast"):
        light = bpy.data.objects.get(name)
        if light is None or light.type != "LIGHT":
            continue
        light.data.energy = 180.0
        light.data.color = (0.34, 0.39, 0.48)
        light["cathode_moon_base_energy"] = 180.0
        light["cathode_future_lightning_target"] = True
        moon_settings.append(name)

    scene.frame_set(1)
    scene["cathode_dark_window_rain_v100"] = True
    scene["cathode_rain_loop_frames"] = loop_frames
    scene["cathode_lightning_enabled"] = False
    return {
        "applied": True,
        "removed_exterior": exterior is not None,
        "dark_glass": glass_objects,
        "rain_drops": len(drops),
        "loop_frames": loop_frames,
        "moon_lights": moon_settings,
        "lightning_enabled": False,
    }


def refine_dark_window_rain_v101():
    """Keep the rain monochrome and make its rolling streaks more slender."""
    scene = bpy.context.scene
    if scene.get("cathode_dark_window_rain_refined_v101"):
        return {"applied": False, "reason": "already present"}

    droplet_mesh = bpy.data.meshes.get("CATHODE_RAIN_DropletMesh")
    if droplet_mesh is None:
        return {"applied": False, "reason": "rain mesh missing"}
    for vertex in droplet_mesh.vertices:
        vertex.co.x *= 0.60
    droplet_mesh.update()

    rain_material = bpy.data.materials.get("CATHODE_RAIN_GLINT")
    if rain_material is not None and rain_material.use_nodes:
        bsdf = rain_material.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            base = bsdf.inputs.get("Base Color")
            if base is not None:
                base.default_value = (0.50, 0.50, 0.53, 1.0)
            emission = bsdf.inputs.get("Emission Color")
            if emission is None:
                emission = bsdf.inputs.get("Emission")
            if emission is not None:
                emission.default_value = (0.38, 0.38, 0.42, 1.0)
            emission_strength = bsdf.inputs.get("Emission Strength")
            if emission_strength is not None:
                emission_strength.default_value = 1.15

    dark_glass = bpy.data.materials.get("CATHODE_WINDOW_DARK_GLASS")
    if dark_glass is not None and dark_glass.use_nodes:
        bsdf = dark_glass.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            base = bsdf.inputs.get("Base Color")
            if base is not None:
                base.default_value = (0.0015, 0.0015, 0.0018, 1.0)

    moon_lights = []
    for name in ("LIGHT_WindowWest", "LIGHT_WindowEast"):
        light = bpy.data.objects.get(name)
        if light is None or light.type != "LIGHT":
            continue
        light.data.color = (0.42, 0.43, 0.47)
        moon_lights.append(name)

    scene["cathode_dark_window_rain_refined_v101"] = True
    return {
        "applied": True,
        "droplet_width_factor": 0.60,
        "moon_lights": moon_lights,
        "loop_timing_unchanged": True,
    }


def densify_and_speed_window_rain_v102():
    """Create denser, faster, shorter rain that exits below the window."""
    scene = bpy.context.scene
    if scene.get("cathode_dense_fast_rain_v102"):
        return {"applied": False, "reason": "already present"}

    for old in list(bpy.data.objects):
        if old.name.startswith("CATHODE_RAIN_Window"):
            bpy.data.objects.remove(old, do_unlink=True)

    droplet_mesh = bpy.data.meshes.get("CATHODE_RAIN_DropletMesh")
    if droplet_mesh is None:
        return {"applied": False, "reason": "rain mesh missing"}
    for vertex in droplet_mesh.vertices:
        vertex.co.z *= 0.50
    droplet_mesh.update()

    rain_collection = bpy.data.collections.get("CATHODE_WINDOW_RAIN")
    if rain_collection is None:
        rain_collection = bpy.data.collections.new("CATHODE_WINDOW_RAIN")
        scene.collection.children.link(rain_collection)

    scene.frame_start = 1
    scene.frame_end = 240
    scene.render.fps = 24
    loop_frames = 240
    drops_per_window = 120
    rng = __import__("random").Random(20260829)
    window_ranges = (
        (1, -1.99, -0.81, 0),
        (2, 0.81, 1.99, 19),
    )
    drops = []
    lifetimes = []
    terminal_heights = []
    for window_index, min_x, max_x, phase_offset in window_ranges:
        phase_step = loop_frames / float(drops_per_window)
        for index in range(drops_per_window):
            drop = bpy.data.objects.new(
                "CATHODE_RAIN_Window%d_%03d" % (window_index, index),
                droplet_mesh,
            )
            rain_collection.objects.link(drop)
            x = rng.uniform(min_x, max_x)
            top_z = rng.uniform(2.58, 2.72)
            bottom_z = rng.uniform(1.04, 1.14)
            phase = int((index * phase_step + rng.uniform(0.0, phase_step) + phase_offset) % loop_frames) + 1
            lifetime = rng.randrange(24, 43)
            width = rng.uniform(0.0048, 0.0090)
            depth = rng.uniform(0.0018, 0.0030)
            height = rng.uniform(0.032, 0.068)
            drop.location = (x, 2.692, top_z)
            drop.scale = (0.0, 0.0, 0.0)
            drop["cathode_rain_phase"] = phase
            drop["cathode_rain_lifetime"] = lifetime
            drop["cathode_rain_loop_frames"] = loop_frames
            drop["cathode_rain_behavior"] = "fast fall past sill, subtle offscreen pop"

            for offset in (-loop_frames, 0, loop_frames):
                start = phase + offset
                keyframes = (
                    (start, top_z, (0.0, 0.0, 0.0)),
                    (start + 2, top_z - 0.035, (width, depth, height)),
                    (start + lifetime - 5, 1.20, (width, depth, height)),
                    (start + lifetime - 2, bottom_z, (width * 1.7, depth, height * 0.22)),
                    (start + lifetime, bottom_z, (0.0, 0.0, 0.0)),
                    (start + lifetime + 1, top_z, (0.0, 0.0, 0.0)),
                )
                for frame, z_value, scale_value in keyframes:
                    drop.location.z = z_value
                    drop.scale = scale_value
                    drop.keyframe_insert(data_path="location", index=2, frame=frame)
                    drop.keyframe_insert(data_path="scale", frame=frame)

            action = drop.animation_data.action if drop.animation_data else None
            if action is not None:
                for layer in action.layers:
                    for strip in layer.strips:
                        for channelbag in strip.channelbags:
                            for curve in channelbag.fcurves:
                                for keyframe in curve.keyframe_points:
                                    keyframe.interpolation = "LINEAR"
            drops.append(drop.name)
            lifetimes.append(lifetime)
            terminal_heights.append(bottom_z)

    scene.frame_set(1)
    scene["cathode_dense_fast_rain_v102"] = True
    scene["cathode_rain_drop_count_v102"] = len(drops)
    return {
        "applied": True,
        "rain_drops": len(drops),
        "drops_per_window": drops_per_window,
        "lifetime_range_frames": [min(lifetimes), max(lifetimes)],
        "terminal_height_range": [min(terminal_heights), max(terminal_heights)],
        "droplet_length_factor": 0.50,
        "loop_frames": loop_frames,
    }


def build_thunderstorm_grass_stage_v103():
    """Add a window-only exterior grass stage and much heavier, faster rain."""
    scene = bpy.context.scene
    if scene.get("cathode_thunderstorm_grass_stage_v103"):
        return {"applied": False, "reason": "already present"}

    # The old opaque panes made the exterior read as a featureless black card.
    # The architectural wall and frame now provide the window mask instead.
    for name in ("WINDOW_1_Glass", "WINDOW_2_Glass"):
        glass = bpy.data.objects.get(name)
        if glass is not None:
            glass.hide_render = True
            glass["cathode_hidden_for_exterior_stage"] = True

    old_flat = bpy.data.objects.get("CATHODE_WINDOW_EXTERIOR_FLAT")
    if old_flat is not None:
        bpy.data.objects.remove(old_flat, do_unlink=True)
    for old in list(bpy.data.objects):
        if old.name.startswith("CATHODE_STORM_") or old.name.startswith("CATHODE_RAIN_Window"):
            bpy.data.objects.remove(old, do_unlink=True)

    stage_collection = bpy.data.collections.get("CATHODE_EXTERIOR_STORM_STAGE")
    if stage_collection is None:
        stage_collection = bpy.data.collections.new("CATHODE_EXTERIOR_STORM_STAGE")
        scene.collection.children.link(stage_collection)

    def principled_material(name, color, roughness=0.9):
        material = bpy.data.materials.get(name)
        if material is None:
            material = bpy.data.materials.new(name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (*color, 1.0)
        emission.inputs["Strength"].default_value = 1.0
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        return material

    enclosure_mat = bpy.data.materials.get("CATHODE_STORM_ENCLOSURE")
    if enclosure_mat is None:
        enclosure_mat = bpy.data.materials.new("CATHODE_STORM_ENCLOSURE")
    enclosure_mat.use_nodes = True
    enclosure_nodes = enclosure_mat.node_tree.nodes
    enclosure_links = enclosure_mat.node_tree.links
    enclosure_nodes.clear()
    enclosure_output = enclosure_nodes.new("ShaderNodeOutputMaterial")
    enclosure_emission = enclosure_nodes.new("ShaderNodeEmission")
    enclosure_emission.inputs["Color"].default_value = (0.035, 0.043, 0.058, 1.0)
    enclosure_emission.inputs["Strength"].default_value = 1.0
    enclosure_links.new(enclosure_emission.outputs["Emission"], enclosure_output.inputs["Surface"])
    mask_mat = bpy.data.materials.get("CATHODE_STORM_OUTER_MASK")
    if mask_mat is None:
        mask_mat = bpy.data.materials.new("CATHODE_STORM_OUTER_MASK")
    mask_mat.use_nodes = True
    mask_nodes = mask_mat.node_tree.nodes
    mask_links = mask_mat.node_tree.links
    mask_nodes.clear()
    mask_output = mask_nodes.new("ShaderNodeOutputMaterial")
    mask_emission = mask_nodes.new("ShaderNodeEmission")
    mask_emission.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    mask_emission.inputs["Strength"].default_value = 1.0
    mask_links.new(mask_emission.outputs["Emission"], mask_output.inputs["Surface"])
    blade_dark = principled_material(
        "CATHODE_STORM_GRASS_DARK", (0.055, 0.065, 0.072), 0.96
    )
    blade_mid = principled_material(
        "CATHODE_STORM_GRASS_MID", (0.13, 0.145, 0.155), 0.92
    )
    blade_pale = principled_material(
        "CATHODE_STORM_GRASS_PALE", (0.245, 0.255, 0.265), 0.88
    )

    ground_mat = bpy.data.materials.get("CATHODE_STORM_GRASS_GROUND")
    if ground_mat is None:
        ground_mat = bpy.data.materials.new("CATHODE_STORM_GRASS_GROUND")
    ground_mat.use_nodes = True
    nodes = ground_mat.node_tree.nodes
    links = ground_mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    ground_emission = nodes.new("ShaderNodeEmission")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 8.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = (0.018, 0.022, 0.028, 1.0)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.11, 0.122, 0.13, 1.0)
    texcoord = nodes.new("ShaderNodeTexCoord")
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], ground_emission.inputs["Color"])
    ground_emission.inputs["Strength"].default_value = 1.0
    links.new(ground_emission.outputs["Emission"], output.inputs["Surface"])

    def add_box(name, center, dimensions, material):
        cx, cy, cz = center
        hx, hy, hz = (value * 0.5 for value in dimensions)
        vertices = [
            (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
            (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
        ]
        faces = [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
        ]
        mesh = bpy.data.meshes.new(name + "_Mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        stage_collection.objects.link(obj)
        obj.location = (cx, cy, cz)
        obj.data.materials.append(material)
        return obj

    # Two shallow shadow rooms are physically contained behind the apertures.
    # The inclined lower surfaces read as exterior ground from the elevated
    # home camera, while the side/top panels guarantee that no grass can leak
    # around the architecture when an interactive camera shifts position.
    window_apertures = (
        (1, -2.06, -0.74),
        (2, 0.74, 2.06),
    )
    stage_y_front, stage_y_back = 2.86, 3.64
    ground_z_front, ground_z_back = 1.275, 1.72
    ground_patches = []
    for window_index, aperture_x_min, aperture_x_max in window_apertures:
        x_min = aperture_x_min + 0.035
        x_max = aperture_x_max - 0.035
        width = x_max - x_min
        ground_mesh = bpy.data.meshes.new(
            "CATHODE_STORM_GrassGround_W%d_Mesh" % window_index
        )
        ground_vertices = [
            (x_min, stage_y_front, ground_z_front),
            (x_max, stage_y_front, ground_z_front),
            (x_max, stage_y_back, ground_z_back),
            (x_min, stage_y_back, ground_z_back),
        ]
        ground_mesh.from_pydata(ground_vertices, [], [(0, 1, 2, 3)])
        ground_mesh.update()
        ground = bpy.data.objects.new(
            "CATHODE_STORM_GrassGround_W%d" % window_index, ground_mesh
        )
        stage_collection.objects.link(ground)
        ground.data.materials.append(ground_mat)
        ground["cathode_exterior_floor_extension"] = True
        ground["cathode_window_shadow_room"] = window_index
        ground_patches.append((window_index, x_min, x_max))

        back_wall = add_box(
            "CATHODE_STORM_BackWall_W%d" % window_index,
            ((x_min + x_max) * 0.5, stage_y_back + 0.025, 1.925),
            (width, 0.05, 1.33),
            enclosure_mat,
        )
        left_wall = add_box(
            "CATHODE_STORM_LeftWall_W%d" % window_index,
            (x_min, (stage_y_front + stage_y_back) * 0.5, 1.925),
            (0.035, stage_y_back - stage_y_front, 1.33),
            enclosure_mat,
        )
        right_wall = add_box(
            "CATHODE_STORM_RightWall_W%d" % window_index,
            (x_max, (stage_y_front + stage_y_back) * 0.5, 1.925),
            (0.035, stage_y_back - stage_y_front, 1.33),
            enclosure_mat,
        )
        roof = add_box(
            "CATHODE_STORM_Roof_W%d" % window_index,
            ((x_min + x_max) * 0.5, (stage_y_front + stage_y_back) * 0.5, 2.585),
            (width, stage_y_back - stage_y_front, 0.035),
            enclosure_mat,
        )
        for obj in (back_wall, left_wall, right_wall, roof):
            obj["cathode_window_only_occluder"] = True

    # Actual crossed blade geometry, dense enough to read as grass through the
    # oblique bird's-eye windows without using or projecting a source image.
    rng = __import__("random").Random(20260830)
    blade_vertices = []
    blade_faces = []
    blade_materials = []
    blades_per_window = 2400
    blade_count = blades_per_window * len(ground_patches)
    for window_index, x_min, x_max in ground_patches:
        for index in range(blades_per_window):
            x = rng.uniform(x_min + 0.018, x_max - 0.018)
            y = rng.uniform(stage_y_front + 0.018, stage_y_back - 0.018)
            depth_t = (y - stage_y_front) / (stage_y_back - stage_y_front)
            ground_z = ground_z_front + (ground_z_back - ground_z_front) * depth_t
            base_z = ground_z + rng.uniform(0.006, 0.014)
            height = rng.uniform(0.035, 0.105)
            width = rng.uniform(0.0034, 0.0090)
            lean_x = rng.uniform(-0.018, 0.018)
            lean_y = rng.uniform(-0.016, 0.016)
            angle = rng.uniform(0.0, math.tau)
            material_index = 0 if rng.random() < 0.52 else (1 if rng.random() < 0.86 else 2)
            for cross_angle in (angle, angle + math.pi * 0.5):
                dx = math.cos(cross_angle) * width
                dy = math.sin(cross_angle) * width
                base = len(blade_vertices)
                blade_vertices.extend([
                    (x - dx, y - dy, base_z),
                    (x + dx, y + dy, base_z),
                    (x + lean_x + dx * 0.16, y + lean_y + dy * 0.16, base_z + height * 0.84),
                    (x + lean_x, y + lean_y, base_z + height),
                ])
                blade_faces.append((base, base + 1, base + 2, base + 3))
                blade_materials.append(material_index)

    blade_mesh = bpy.data.meshes.new("CATHODE_STORM_GrassBlades_Mesh")
    blade_mesh.from_pydata(blade_vertices, [], blade_faces)
    blade_mesh.update()
    blade_obj = bpy.data.objects.new("CATHODE_STORM_GrassBlades", blade_mesh)
    stage_collection.objects.link(blade_obj)
    blade_obj.data.materials.append(blade_dark)
    blade_obj.data.materials.append(blade_mid)
    blade_obj.data.materials.append(blade_pale)
    for polygon, material_index in zip(blade_mesh.polygons, blade_materials):
        polygon.material_index = material_index
    blade_obj["cathode_3d_grass_blades"] = blade_count
    blade_obj["cathode_generated_not_image"] = True

    # A restrained overhead moon wash keeps the exterior dark-grey rather than
    # pitch black and gives the real blade geometry enough tonal separation.
    old_light = bpy.data.objects.get("LIGHT_ExteriorStormWash")
    if old_light is not None:
        bpy.data.objects.remove(old_light, do_unlink=True)
    light_data = bpy.data.lights.new("LIGHT_ExteriorStormWash_Data", type="AREA")
    light_data.energy = 210.0
    light_data.shape = "RECTANGLE"
    light_data.size = 4.0
    light_data.size_y = 2.2
    light_data.color = (0.42, 0.46, 0.52)
    storm_light = bpy.data.objects.new("LIGHT_ExteriorStormWash", light_data)
    stage_collection.objects.link(storm_light)
    storm_light.location = (0.0, 3.28, 2.54)
    storm_light.rotation_euler = (0.0, 0.0, 0.0)
    storm_light["cathode_future_lightning_target"] = True

    droplet_mesh = bpy.data.meshes.get("CATHODE_RAIN_DropletMesh")
    if droplet_mesh is None:
        return {"applied": False, "reason": "rain mesh missing"}
    rain_material = bpy.data.materials.get("CATHODE_RAIN_GLINT")
    if rain_material is not None:
        rain_material.use_nodes = True
        rain_nodes = rain_material.node_tree.nodes
        rain_links = rain_material.node_tree.links
        rain_nodes.clear()
        rain_output = rain_nodes.new("ShaderNodeOutputMaterial")
        rain_emission = rain_nodes.new("ShaderNodeEmission")
        rain_emission.inputs["Color"].default_value = (0.58, 0.60, 0.64, 1.0)
        rain_emission.inputs["Strength"].default_value = 1.45
        rain_links.new(rain_emission.outputs["Emission"], rain_output.inputs["Surface"])
    rain_collection = bpy.data.collections.get("CATHODE_WINDOW_RAIN")
    if rain_collection is None:
        rain_collection = bpy.data.collections.new("CATHODE_WINDOW_RAIN")
        scene.collection.children.link(rain_collection)

    scene.frame_start = 1
    scene.frame_end = 240
    scene.render.fps = 24
    loop_frames = 240
    drops_per_window = 1080
    rain_rng = __import__("random").Random(20260831)
    window_ranges = (
        (1, -2.03, -0.77, 0),
        (2, 0.77, 2.03, 11),
    )
    drops = []
    lifetimes = []
    terminal_heights = []
    for window_index, min_x, max_x, phase_offset in window_ranges:
        phase_step = loop_frames / float(drops_per_window)
        for index in range(drops_per_window):
            drop = bpy.data.objects.new(
                "CATHODE_RAIN_Window%d_%03d" % (window_index, index), droplet_mesh
            )
            rain_collection.objects.link(drop)
            x = rain_rng.uniform(min_x, max_x)
            # Keep the rainfall immediately outside the glazing. Distributing
            # it through the full stage depth makes most drops disappear behind
            # the architectural mask and visually thins out the storm.
            y = rain_rng.uniform(2.85, 3.02)
            top_z = rain_rng.uniform(2.56, 2.72)
            bottom_z = rain_rng.uniform(0.11, 0.19)
            phase = int(
                (index * phase_step + rain_rng.uniform(0.0, max(phase_step, 1.0)) + phase_offset)
                % loop_frames
            ) + 1
            lifetime = rain_rng.randrange(10, 19)
            width = rain_rng.uniform(0.0040, 0.0078)
            depth = rain_rng.uniform(0.0016, 0.0028)
            height = rain_rng.uniform(0.026, 0.055)
            drop.location = (x, y, top_z)
            drop.scale = (0.0, 0.0, 0.0)
            drop["cathode_rain_phase"] = phase
            drop["cathode_rain_lifetime"] = lifetime
            drop["cathode_rain_loop_frames"] = loop_frames
            drop["cathode_rain_behavior"] = "thunderstorm-fast fall to grass, seamless reset"

            for offset in (-loop_frames, 0, loop_frames):
                start = phase + offset
                keyframes = (
                    (start, top_z, (0.0, 0.0, 0.0)),
                    (start + 1, top_z - 0.06, (width, depth, height)),
                    (start + lifetime - 3, 0.34, (width, depth, height)),
                    (start + lifetime - 1, bottom_z, (width * 1.45, depth, height * 0.18)),
                    (start + lifetime, bottom_z, (0.0, 0.0, 0.0)),
                    (start + lifetime + 1, top_z, (0.0, 0.0, 0.0)),
                )
                for frame, z_value, scale_value in keyframes:
                    drop.location.z = z_value
                    drop.scale = scale_value
                    drop.keyframe_insert(data_path="location", index=2, frame=frame)
                    drop.keyframe_insert(data_path="scale", frame=frame)

            action = drop.animation_data.action if drop.animation_data else None
            if action is not None:
                for layer in action.layers:
                    for strip in layer.strips:
                        for channelbag in strip.channelbags:
                            for curve in channelbag.fcurves:
                                for keyframe in curve.keyframe_points:
                                    keyframe.interpolation = "LINEAR"
            drops.append(drop.name)
            lifetimes.append(lifetime)
            terminal_heights.append(bottom_z)

    scene.frame_set(1)
    scene["cathode_thunderstorm_grass_stage_v103"] = True
    scene["cathode_lightning_enabled"] = False
    scene["cathode_exterior_visibility"] = "masked by north wall and visible only through windows"
    return {
        "applied": True,
        "rain_drops": len(drops),
        "drops_per_window": drops_per_window,
        "lifetime_range_frames": [min(lifetimes), max(lifetimes)],
        "terminal_height_range": [min(terminal_heights), max(terminal_heights)],
        "grass_blades": blade_count,
        "loop_frames": loop_frames,
        "lightning_enabled": False,
    }


def expose_window_stage_in_viewport_v104():
    """Keep the exterior stage visible in Blender's viewport and final render."""
    scene = bpy.context.scene
    glass_states = {}
    for name in ("WINDOW_1_Glass", "WINDOW_2_Glass"):
        glass = bpy.data.objects.get(name)
        if glass is None:
            continue
        glass.hide_render = True
        glass.hide_viewport = True
        glass.hide_set(True)
        glass["cathode_hidden_for_exterior_stage"] = True
        glass_states[name] = {
            "hide_render": glass.hide_render,
            "hide_viewport": glass.hide_viewport,
            "hidden": glass.hide_get(),
        }

    stage_collection = bpy.data.collections.get("CATHODE_EXTERIOR_STORM_STAGE")
    stage_objects = []
    if stage_collection is not None:
        stage_collection.hide_render = False
        stage_collection.hide_viewport = False
        for obj in stage_collection.objects:
            obj.hide_render = False
            obj.hide_viewport = False
            obj.hide_set(False)
            stage_objects.append(obj.name)

    rain_collection = bpy.data.collections.get("CATHODE_WINDOW_RAIN")
    rain_objects = []
    if rain_collection is not None:
        rain_collection.hide_render = False
        rain_collection.hide_viewport = False
        for obj in rain_collection.objects:
            obj.hide_render = False
            obj.hide_viewport = False
            obj.hide_set(False)
            rain_objects.append(obj.name)

    scene.frame_set(1)
    scene["cathode_window_stage_viewport_visible_v104"] = True
    return {
        "applied": True,
        "glass": glass_states,
        "stage_objects": len(stage_objects),
        "rain_objects": len(rain_objects),
    }


def build_full_exterior_field_source_v105():
    """Build an unrestricted exterior source set for later window-plate baking."""
    scene = bpy.context.scene
    if scene.get("cathode_full_exterior_field_source_v105"):
        return {"applied": False, "reason": "already present"}

    # Preserve the completed rain rig but remove it from both viewport and
    # rendering while the exterior composition is designed.
    rain_collection = bpy.data.collections.get("CATHODE_WINDOW_RAIN")
    rain_count = 0
    if rain_collection is not None:
        rain_collection.hide_render = True
        rain_collection.hide_viewport = True
        for obj in rain_collection.objects:
            obj.hide_render = True
            obj.hide_viewport = True
            obj.hide_set(True)
            rain_count += 1

    # Remove the shallow proof-of-concept rooms. This source field is allowed
    # to extend freely because it will be rendered, approved, and baked later.
    removed = []
    for old in list(bpy.data.objects):
        if old.name.startswith("CATHODE_STORM_") or old.name == "LIGHT_ExteriorStormWash":
            removed.append(old.name)
            bpy.data.objects.remove(old, do_unlink=True)

    source_collection = bpy.data.collections.get("CATHODE_EXTERIOR_SOURCE_FIELD")
    if source_collection is None:
        source_collection = bpy.data.collections.new("CATHODE_EXTERIOR_SOURCE_FIELD")
        scene.collection.children.link(source_collection)
    source_collection.hide_render = False
    source_collection.hide_viewport = False

    def emission_material(name, color, strength=1.0):
        material = bpy.data.materials.get(name)
        if material is None:
            material = bpy.data.materials.new(name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (*color, 1.0)
        emission.inputs["Strength"].default_value = strength
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        return material

    sky_material = emission_material(
        "CATHODE_SOURCE_STORM_SKY", (0.045, 0.055, 0.072), 1.0
    )
    silhouette_material = emission_material(
        "CATHODE_SOURCE_HORIZON_DARK", (0.012, 0.016, 0.022), 1.0
    )
    blade_dark = emission_material(
        "CATHODE_SOURCE_GRASS_DARK", (0.045, 0.052, 0.058), 1.0
    )
    blade_mid = emission_material(
        "CATHODE_SOURCE_GRASS_MID", (0.105, 0.118, 0.127), 1.0
    )
    blade_pale = emission_material(
        "CATHODE_SOURCE_GRASS_PALE", (0.205, 0.218, 0.228), 1.0
    )

    ground_material = bpy.data.materials.get("CATHODE_SOURCE_GRASS_GROUND")
    if ground_material is None:
        ground_material = bpy.data.materials.new("CATHODE_SOURCE_GRASS_GROUND")
    ground_material.use_nodes = True
    nodes = ground_material.node_tree.nodes
    links = ground_material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.8
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.76
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.16
    ramp.color_ramp.elements[0].color = (0.012, 0.016, 0.020, 1.0)
    ramp.color_ramp.elements[1].position = 0.84
    ramp.color_ramp.elements[1].color = (0.085, 0.096, 0.104, 1.0)
    texcoord = nodes.new("ShaderNodeTexCoord")
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    def add_box(name, center, dimensions, material):
        cx, cy, cz = center
        hx, hy, hz = (value * 0.5 for value in dimensions)
        vertices = [
            (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
            (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
        ]
        faces = [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
        ]
        mesh = bpy.data.meshes.new(name + "_Mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        source_collection.objects.link(obj)
        obj.location = (cx, cy, cz)
        obj.data.materials.append(material)
        return obj

    field_x_min, field_x_max = -6.0, 11.0
    field_y_min, field_y_max = 2.84, 14.0
    field_center_x = (field_x_min + field_x_max) * 0.5
    field_center_y = (field_y_min + field_y_max) * 0.5
    field_width = field_x_max - field_x_min
    field_depth = field_y_max - field_y_min
    ground = add_box(
        "CATHODE_SOURCE_GrassField",
        (field_center_x, field_center_y, 0.035),
        (field_width, field_depth, 0.07),
        ground_material,
    )
    ground["cathode_exterior_source_field"] = True
    backdrop = add_box(
        "CATHODE_SOURCE_StormBackdrop",
        (field_center_x, field_y_max + 0.06, 2.55),
        (field_width, 0.12, 5.10),
        sky_material,
    )
    backdrop["cathode_exterior_source_backdrop"] = True

    # A low irregular horizon prevents the field from reading as a flat card.
    horizon_rng = __import__("random").Random(20260902)
    horizon_vertices = []
    horizon_faces = []
    horizon_segments = 72
    step = field_width / horizon_segments
    for index in range(horizon_segments):
        x0 = field_x_min + index * step
        x1 = x0 + step * 1.04
        z_top0 = horizon_rng.uniform(0.48, 1.16)
        z_top1 = max(0.42, min(1.22, z_top0 + horizon_rng.uniform(-0.24, 0.24)))
        base = len(horizon_vertices)
        horizon_vertices.extend([
            (x0, field_y_max - 0.08, 0.05),
            (x1, field_y_max - 0.08, 0.05),
            (x1, field_y_max - 0.08, z_top1),
            (x0, field_y_max - 0.08, z_top0),
        ])
        horizon_faces.append((base, base + 1, base + 2, base + 3))
    horizon_mesh = bpy.data.meshes.new("CATHODE_SOURCE_Horizon_Mesh")
    horizon_mesh.from_pydata(horizon_vertices, [], horizon_faces)
    horizon_mesh.update()
    horizon = bpy.data.objects.new("CATHODE_SOURCE_Horizon", horizon_mesh)
    source_collection.objects.link(horizon)
    horizon.data.materials.append(silhouette_material)

    # One combined crossed-blade mesh gives real depth without thousands of
    # independent objects. Density is biased toward the first half of the field
    # where the room cameras see the most parallax.
    rng = __import__("random").Random(20260901)
    blade_vertices = []
    blade_faces = []
    blade_material_indices = []
    blade_count = 28000
    for index in range(blade_count):
        x = rng.uniform(field_x_min + 0.05, field_x_max - 0.05)
        depth_mix = rng.random() ** 1.55
        y = field_y_min + 0.05 + depth_mix * (field_depth - 0.10)
        base_z = 0.078 + rng.uniform(-0.005, 0.014)
        height = rng.uniform(0.075, 0.245)
        width = rng.uniform(0.0045, 0.0140)
        lean_x = rng.uniform(-0.035, 0.035)
        lean_y = rng.uniform(-0.032, 0.032)
        angle = rng.uniform(0.0, math.tau)
        material_index = 0 if rng.random() < 0.56 else (1 if rng.random() < 0.88 else 2)
        for cross_angle in (angle, angle + math.pi * 0.5):
            dx = math.cos(cross_angle) * width
            dy = math.sin(cross_angle) * width
            base = len(blade_vertices)
            blade_vertices.extend([
                (x - dx, y - dy, base_z),
                (x + dx, y + dy, base_z),
                (x + lean_x + dx * 0.15, y + lean_y + dy * 0.15, base_z + height * 0.84),
                (x + lean_x, y + lean_y, base_z + height),
            ])
            blade_faces.append((base, base + 1, base + 2, base + 3))
            blade_material_indices.append(material_index)

    blade_mesh = bpy.data.meshes.new("CATHODE_SOURCE_GrassBlades_Mesh")
    blade_mesh.from_pydata(blade_vertices, [], blade_faces)
    blade_mesh.update()
    blades = bpy.data.objects.new("CATHODE_SOURCE_GrassBlades", blade_mesh)
    source_collection.objects.link(blades)
    blades.data.materials.append(blade_dark)
    blades.data.materials.append(blade_mid)
    blades.data.materials.append(blade_pale)
    for polygon, material_index in zip(blade_mesh.polygons, blade_material_indices):
        polygon.material_index = material_index
    blades["cathode_source_grass_blades"] = blade_count

    light_data = bpy.data.lights.new("LIGHT_ExteriorSourceMoon_Data", type="AREA")
    light_data.energy = 340.0
    light_data.shape = "RECTANGLE"
    light_data.size = 14.0
    light_data.size_y = 9.0
    light_data.color = (0.42, 0.46, 0.52)
    moon_light = bpy.data.objects.new("LIGHT_ExteriorSourceMoon", light_data)
    source_collection.objects.link(moon_light)
    moon_light.location = (field_center_x, 8.0, 5.2)
    moon_light.rotation_euler = (0.0, 0.0, 0.0)

    scene.frame_set(1)
    scene["cathode_full_exterior_field_source_v105"] = True
    scene["cathode_exterior_source_status"] = "temporary full 3D field for window plate baking"
    scene["cathode_rain_hidden_for_exterior_design"] = True
    return {
        "applied": True,
        "removed_shadow_room_objects": len(removed),
        "hidden_rain_objects": rain_count,
        "grass_blades": blade_count,
        "field_bounds": [field_x_min, field_x_max, field_y_min, field_y_max],
        "horizon_segments": horizon_segments,
    }


def shift_world_x(ob, delta):
    """Translate an object in world X without disturbing its local details."""
    if ob is None:
        return
    if ob.parent is None:
        ob.location.x += delta
        return
    world_matrix = ob.matrix_world.copy()
    world_matrix.translation.x += delta
    ob.matrix_world = world_matrix


def rebuild_camera_and_tuck_shelf_items(mats):
    """Make the shelf camera read clearly and seat all loose items in depth."""
    scene = bpy.context.scene
    if scene.get("cathode_shelf_depth_and_camera_fix_applied"):
        return {"applied": False, "reason": "already present"}

    moved = {}

    def move_group(label, predicate, delta):
        objects = [ob for ob in bpy.data.objects if predicate(ob)]
        for ob in objects:
            shift_world_x(ob, delta)
        moved[label] = {"objects": [ob.name for ob in objects],
                        "delta_x": round(delta, 6)}

    # World X is the shelf's front-to-back axis. These offsets leave a visible
    # inset from the front carcass plane at x=2.30 while keeping the pieces on
    # their existing cubby floors and preserving the bottom/top cubbies.
    move_group("globe", lambda ob: ob.name.startswith("SHELF_Globe"), 0.12)
    move_group("polaroids", lambda ob: ob.name.startswith("SHELF_Polaroid_"), 0.08)
    move_group("record_player", lambda ob: ob.name.startswith("INTERACT_RecordPlayer_"), 0.13)
    target = bpy.data.objects.get("TARGET_VINYLS")
    if target is not None:
        shift_world_x(target, 0.13)
        moved["record_player_target"] = {"objects": [target.name], "delta_x": 0.13}

    camera_parts = [ob for ob in bpy.data.objects if ob.name.startswith("SHELF_Camera_")]
    for ob in camera_parts:
        shift_world_x(ob, 0.15)
    moved["camera_depth"] = {"objects": [ob.name for ob in camera_parts], "delta_x": 0.15}

    camera = bpy.data.objects.get("SHELF_Camera_Body")
    body_shape = {}
    if camera is not None:
        # Lower the whole assembly to the shelf surface, then make the body a
        # little smaller so it reads as a compact camera rather than a box.
        for ob in camera_parts:
            ob.location.z -= 0.04
        body_shape = {
            "x": resize_object_axis(camera, 0, 2.50, 0.16),
            "y": resize_object_axis(camera, 1, 1.74, 0.22),
            "z": resize_object_axis(camera, 2, 1.0375, 0.16),
        }
        camera["cathode_camera_silhouette"] = "compact body with circular lens, flash, and viewfinder"

    flash = bpy.data.objects.get("SHELF_Camera_Flash")
    viewfinder = bpy.data.objects.get("SHELF_Camera_Viewfinder")
    if flash is not None:
        flash.location.z = 1.145
    if viewfinder is not None:
        viewfinder.location.z = 1.145

    generated = []
    if bpy.data.objects.get("SHELF_Camera_LensRing") is None:
        bpy.ops.mesh.primitive_torus_add(
            major_radius=0.056,
            minor_radius=0.006,
            major_segments=20,
            minor_segments=8,
            location=(2.36, 1.74, 1.0775),
            rotation=(0.0, math.pi / 2.0, 0.0),
        )
        ring = bpy.context.object
        ring.name = "SHELF_Camera_LensRing"
        ring.data.materials.append(mats["dark"])
        ring["cathode_camera_detail"] = "front lens ring"
        generated.append(ring.name)
    if bpy.data.objects.get("SHELF_Camera_ShutterButton") is None:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12,
            radius=0.016,
            depth=0.010,
            location=(2.49, 1.67, 1.176),
        )
        button = bpy.context.object
        button.name = "SHELF_Camera_ShutterButton"
        button.location.z = 1.125
        button.data.materials.append(mats["mid"])
        button["cathode_camera_detail"] = "top shutter button"
        generated.append(button.name)

    scene["cathode_shelf_depth_and_camera_fix_applied"] = True
    return {
        "applied": True,
        "moved": moved,
        "camera_body_shape": body_shape,
        "generated_camera_details": generated,
    }


def hollow_vinyl_racks():
    """Replace each solid triangular vinyl support with a hollow triangle frame."""
    scene = bpy.context.scene
    if scene.get("cathode_vinyl_rack_hollows_applied"):
        return {"applied": False, "reason": "already present"}

    changed = []
    for name in ("SHELF_VinylRack_Left", "SHELF_VinylRack_Right"):
        ob = bpy.data.objects.get(name)
        if ob is None or not hasattr(ob.data, "vertices") or len(ob.data.vertices) < 3:
            continue
        world_vertices = [ob.matrix_world @ vertex.co for vertex in ob.data.vertices]
        x_min = min(point.x for point in world_vertices)
        x_max = max(point.x for point in world_vertices)
        y_min = min(point.y for point in world_vertices)
        y_max = max(point.y for point in world_vertices)
        z_min = min(point.z for point in world_vertices)
        z_max = max(point.z for point in world_vertices)
        # Preserve the original right-triangle silhouette and inset a similar
        # triangle toward its centroid to form the open center.
        outer = [Vector((x_min, z_min)), Vector((x_max, z_min)),
                 Vector((x_max, z_max))]
        centroid = sum(outer, Vector((0.0, 0.0))) / 3.0
        inner_scale = 0.56
        inner = [centroid + (point - centroid) * inner_scale for point in outer]
        world_points = []
        for y in (y_min, y_max):
            world_points.extend(Vector((point.x, y, point.y)) for point in outer)
            world_points.extend(Vector((point.x, y, point.y)) for point in inner)
        inverse = ob.matrix_world.inverted()
        vertices = [inverse @ point for point in world_points]
        # Index layout per depth: outer 0..2, inner 3..5; back starts at 6.
        faces = []
        for base, reverse in ((0, False), (6, True)):
            for index in range(3):
                nxt = (index + 1) % 3
                quad = (base + index, base + nxt, base + 3 + nxt, base + 3 + index)
                faces.append(tuple(reversed(quad)) if reverse else quad)
        for index in range(3):
            nxt = (index + 1) % 3
            faces.append((index, 6 + index, 6 + nxt, nxt))
            faces.append((3 + index, 3 + nxt, 9 + nxt, 9 + index))
        mesh = bpy.data.meshes.new(name + "_HollowMesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        for material in ob.data.materials:
            mesh.materials.append(material)
        ob.data = mesh
        ob["cathode_vinyl_holder"] = "hollow triangular frame with inset triangular cutout"
        changed.append(name)

    scene["cathode_vinyl_rack_hollows_applied"] = True
    return {"applied": True, "objects": changed, "inner_scale": inner_scale}


def seat_camera_lens():
    """Close the tiny gaps between the camera body, barrel, glass, and ring."""
    scene = bpy.context.scene
    if scene.get("cathode_camera_lens_seated"):
        return {"applied": False, "reason": "already present"}
    moved = []
    # Shift the lens stack toward the body just enough for overlapping contact:
    # the barrel meets the body front and the ring meets the glass face.
    for name in ("SHELF_Camera_LensOuter", "SHELF_Camera_LensGlass",
                 "SHELF_Camera_LensRing"):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            shift_world_x(ob, 0.01)
            moved.append(name)
    scene["cathode_camera_lens_seated"] = True
    return {"applied": True, "objects": moved, "delta_x": 0.01}


def align_camera_lens_centerline():
    """Align the front lens ring vertically with the lowered lens barrel."""
    scene = bpy.context.scene
    if scene.get("cathode_camera_lens_centerline_aligned"):
        return {"applied": False, "reason": "already present"}
    ring = bpy.data.objects.get("SHELF_Camera_LensRing")
    barrel = bpy.data.objects.get("SHELF_Camera_LensOuter")
    if ring is None or barrel is None:
        return {"applied": False, "reason": "lens parts missing"}
    ring.location.z = barrel.location.z
    scene["cathode_camera_lens_centerline_aligned"] = True
    return {"applied": True, "ring": ring.name, "barrel": barrel.name,
            "center_z": round(barrel.location.z, 6)}


def remove_camera_outer_lens_ring():
    """Remove the added outer torus while retaining the modeled lens barrel."""
    scene = bpy.context.scene
    if scene.get("cathode_camera_outer_lens_ring_removed"):
        return {"applied": False, "reason": "already removed"}
    ring = bpy.data.objects.get("SHELF_Camera_LensRing")
    if ring is None:
        scene["cathode_camera_outer_lens_ring_removed"] = True
        return {"applied": False, "reason": "ring missing"}
    name = ring.name
    bpy.data.objects.remove(ring, do_unlink=True)
    scene["cathode_camera_outer_lens_ring_removed"] = True
    return {"applied": True, "removed": name}


def recompose_polaroids():
    """Make four thin, slightly jumbled polaroids that can stack naturally."""
    scene = bpy.context.scene
    if scene.get("cathode_polaroid_stack_recomposed"):
        return {"applied": False, "reason": "already present"}
    card_a = bpy.data.objects.get("SHELF_Polaroid_A_Card")
    photo_a = bpy.data.objects.get("SHELF_Polaroid_A_Photo")
    card_b = bpy.data.objects.get("SHELF_Polaroid_B_Card")
    photo_b = bpy.data.objects.get("SHELF_Polaroid_B_Photo")
    if None in (card_a, photo_a, card_b, photo_b):
        return {"applied": False, "reason": "polaroid source objects missing"}

    def duplicate_object(template, name):
        duplicate = template.copy()
        duplicate.data = template.data.copy()
        duplicate.name = name
        for collection in template.users_collection:
            collection.objects.link(duplicate)
        return duplicate

    card_c = duplicate_object(card_a, "SHELF_Polaroid_C_Card")
    photo_c = duplicate_object(photo_a, "SHELF_Polaroid_C_Photo")
    card_d = duplicate_object(card_b, "SHELF_Polaroid_D_Card")
    photo_d = duplicate_object(photo_b, "SHELF_Polaroid_D_Photo")
    pairs = (
        (card_a, photo_a, 2.46, 1.35, -0.18, 0.9600),
        (card_b, photo_b, 2.44, 1.46,  0.11, 0.9645),
        (card_c, photo_c, 2.47, 1.57, -0.08, 0.9690),
        (card_d, photo_d, 2.45, 1.66,  0.20, 0.9735),
    )
    original_photo_offset = Vector((0.0027, 0.0218))
    changed = []
    for index, (card, photo, x, y, angle, card_z) in enumerate(pairs):
        card.rotation_euler.z = angle
        card.location.x = x
        card.location.y = y
        resize_object_axis(card, 2, card_z, 0.004)
        dx = original_photo_offset.x * math.cos(angle) - original_photo_offset.y * math.sin(angle)
        dy = original_photo_offset.x * math.sin(angle) + original_photo_offset.y * math.cos(angle)
        photo.rotation_euler.z = angle
        photo.location.x = x + dx
        photo.location.y = y + dy
        resize_object_axis(photo, 2, card_z + 0.003, 0.002)
        card["cathode_polaroid_stack_index"] = index
        card["cathode_polaroid_thin_card"] = True
        photo["cathode_polaroid_stack_index"] = index
        photo["cathode_polaroid_thin_photo"] = True
        changed.extend((card.name, photo.name))

    scene["cathode_polaroid_stack_recomposed"] = True
    return {
        "applied": True,
        "count": 4,
        "objects": changed,
        "card_thickness": 0.004,
        "photo_thickness": 0.002,
    }


def separate_polaroid_stack_layers():
    """Give each thin card/photo pair its own non-intersecting stack layer."""
    scene = bpy.context.scene
    if scene.get("cathode_polaroid_stack_layers_separated"):
        return {"applied": False, "reason": "already separated"}
    cards = [bpy.data.objects.get("SHELF_Polaroid_%s_Card" % letter)
             for letter in ("A", "B", "C", "D")]
    photos = [bpy.data.objects.get("SHELF_Polaroid_%s_Photo" % letter)
              for letter in ("A", "B", "C", "D")]
    if any(ob is None for ob in cards + photos):
        return {"applied": False, "reason": "polaroid stack members missing"}
    layers = []
    for index, (card, photo) in enumerate(zip(cards, photos)):
        card_z = 0.960 + index * 0.007
        resize_object_axis(card, 2, card_z, 0.004)
        resize_object_axis(photo, 2, card_z + 0.003, 0.002)
        layers.append({"index": index, "card_z": round(card_z, 6),
                       "photo_z": round(card_z + 0.003, 6)})
    scene["cathode_polaroid_stack_layers_separated"] = True
    return {"applied": True, "layers": layers, "layer_step": 0.007}


def style_polaroid_surfaces(mats):
    """Make the card borders white and the inset image panels visibly dark."""
    scene = bpy.context.scene
    already_styled = bool(scene.get("cathode_polaroid_surfaces_styled"))
    changed = []
    for letter in ("A", "B", "C", "D"):
        card = bpy.data.objects.get("SHELF_Polaroid_%s_Card" % letter)
        photo = bpy.data.objects.get("SHELF_Polaroid_%s_Photo" % letter)
        if card is None or photo is None:
            continue
        card.data.materials.clear()
        card.data.materials.append(mats["white"])
        for polygon in card.data.polygons:
            polygon.material_index = 0
        photo.data.materials.clear()
        photo.data.materials.append(mats["dark"])
        for polygon in photo.data.polygons:
            polygon.material_index = 0
        card["cathode_polaroid_border_material"] = mats["white"].name
        photo["cathode_polaroid_image_material"] = mats["dark"].name
        changed.extend((card.name, photo.name))
    scene["cathode_polaroid_surfaces_styled"] = True
    return {"applied": True, "reapplied": already_styled, "objects": changed,
            "border_material": mats["white"].name,
            "image_material": mats["dark"].name}


def restore_other_vinyls():
    """Restore every non-leftmost record to its original upright placement."""
    scene = bpy.context.scene
    baselines = {
        "INTERACT_Vinyl_1": ((2.4, 1.545, 1.495), (0.0, 0.0, 0.0)),
        "INTERACT_Vinyl_2": ((2.4, 1.577, 1.495), (0.0, 0.0, 0.0)),
        "INTERACT_Vinyl_3": ((2.4, 1.607, 1.495), (0.0, 0.0, 0.0)),
        "INTERACT_Vinyl_4": ((2.4, 1.639, 1.495), (0.0, 0.0, 0.0)),
        "INTERACT_Vinyl_5": ((2.4, 1.669, 1.495), (0.0, 0.0, 0.0)),
        # The rightmost record is returned upright per the latest correction.
        "INTERACT_Vinyl_6": ((2.4, 1.701, 1.4956), (0.0, 0.0, 0.0)),
    }
    restored = []
    for name, (location, rotation) in baselines.items():
        vinyl = bpy.data.objects.get(name)
        if vinyl is None:
            continue
        vinyl.location = location
        vinyl.rotation_euler = rotation
        restored.append(name)
    scene["cathode_other_vinyls_restored"] = True
    return {"applied": True, "objects": restored, "baseline": baselines}


def seat_left_vinyl():
    """Lean only the leftmost vinyl backward so its lower edge rests on the holder."""
    scene = bpy.context.scene
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is None or not hasattr(vinyl.data, "vertices"):
        return {"applied": False, "reason": "left vinyl missing"}
    # Reset the leftmost record before applying the intentional change so
    # rebuilding from a prior output never compounds the tilt or translation.
    vinyl.location = (2.4, 1.515, 1.495)
    vinyl.rotation_euler = (-0.38, 0.0, 0.0)
    bpy.context.view_layer.update()
    world_vertices = [vinyl.matrix_world @ vertex.co for vertex in vinyl.data.vertices]
    min_y = min(point.y for point in world_vertices)
    min_z = min(point.z for point in world_vertices)
    # Move the leaning record left far enough to clear Vinyl_1. Its lower edge
    # still crosses the holder's y=1.465..1.485 depth, so it rests on the
    # holder instead of floating in front of it.
    vinyl.location.y += 1.442 - min_y
    vinyl.location.z += 1.3775 - min_z
    vinyl["cathode_vinyl_seated"] = "leftmost sleeve leans into left triangular holder"
    scene["cathode_left_vinyl_seated"] = True
    bpy.context.view_layer.update()
    final_vertices = [vinyl.matrix_world @ vertex.co for vertex in vinyl.data.vertices]
    return {
        "applied": True,
        "object": vinyl.name,
        "rotation_x": -0.38,
        "world_y_min": round(min(point.y for point in final_vertices), 6),
        "world_z_min": round(min(point.z for point in final_vertices), 6),
    }


def tighten_left_vinyl_contact():
    """Remove the last visible gap where the leaning vinyl meets its holder."""
    scene = bpy.context.scene
    vinyl = bpy.data.objects.get("INTERACT_Vinyl_0")
    if vinyl is None or not hasattr(vinyl.data, "vertices"):
        return {"applied": False, "reason": "left vinyl missing"}
    world_vertices = [vinyl.matrix_world @ vertex.co for vertex in vinyl.data.vertices]
    current_min_y = min(point.y for point in world_vertices)
    # Reassert the leftward placement after all transforms have evaluated.
    vinyl.location.y += 1.442 - current_min_y
    vinyl["cathode_vinyl_holder_contact"] = "slight physical overlap at left holder"
    scene["cathode_left_vinyl_contact_tightened"] = True
    bpy.context.view_layer.update()
    final_vertices = [vinyl.matrix_world @ vertex.co for vertex in vinyl.data.vertices]
    return {"applied": True, "world_y_min": round(min(point.y for point in final_vertices), 6),
            "holder_y_max": 1.485}


def shift_all_vinyls_left():
    """Translate the complete vinyl row toward the user's left view."""
    # Positive world-Y is the user's left from the room camera's viewpoint.
    delta_y = 0.035
    moved = []
    for index in range(7):
        vinyl = bpy.data.objects.get("INTERACT_Vinyl_%d" % index)
        if vinyl is None:
            continue
        vinyl.location.y += delta_y
        moved.append(vinyl.name)
    bpy.context.view_layer.update()
    bpy.context.scene["cathode_vinyl_row_shifted_left"] = True
    return {"applied": True, "delta_y": delta_y, "objects": moved}


def clear_steepened_leftmost_vinyl():
    """Give the steeper leftmost record clearance from its upright neighbor."""
    delta_y = 0.022
    moved = []
    for index in range(1, 7):
        vinyl = bpy.data.objects.get("INTERACT_Vinyl_%d" % index)
        if vinyl is None:
            continue
        vinyl.location.y += delta_y
        moved.append(vinyl.name)
    bpy.context.view_layer.update()
    bpy.context.scene["cathode_steepened_vinyl_clearance"] = True
    return {"applied": True, "delta_y": delta_y, "objects": moved}


def replace_diploma_with_image(mats):
    """Fit the supplied diploma into the existing frame as a subdued image plane."""
    paper = bpy.data.objects.get("ART_DiplomaPaper")
    if paper is None:
        return {"object": None, "image": None, "removed_old_details": []}

    old_fill = bpy.data.objects.get("CATHODE_DIPLOMA_FRAME_FILL")
    if old_fill is not None:
        bpy.data.objects.remove(old_fill, do_unlink=True)

    # The attachment is intentionally loaded only as the diploma artwork and
    # then packed into the output blend; it is not used anywhere else in the
    # scene and is remapped into the Cathode grayscale palette below.
    image_candidates = (
        Path(r"C:\Users\BRIANZ~1\AppData\Local\Temp\codex-clipboard-6d5c5fea-1fc2-44d5-bb25-2c72425fedd6.png"),
        Path(r"C:\Users\Brian Zeng\AppData\Local\Temp\codex-clipboard-6d5c5fea-1fc2-44d5-bb25-2c72425fedd6.png"),
    )
    image_path = next((path for path in image_candidates if path.exists()), None)
    image = bpy.data.images.get("CATHODE_DIPLOMA_REFERENCE")
    if image is None and image_path is not None:
        if image is None:
            image = bpy.data.images.load(str(image_path), check_existing=False)
            image.name = "CATHODE_DIPLOMA_REFERENCE"
    if image is not None:
        try:
            image.pack()
        except RuntimeError:
            pass

    old_details = []
    for ob in list(bpy.data.objects):
        if (ob.name.startswith("ART_DiplomaLine_") or ob.name == "ART_DiplomaSeal"
                or ob.name.startswith("ART_DiplomaBorder_")):
            old_details.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)

    if image is None:
        # Keep the frame valid if the temporary attachment is unavailable.
        paper["cathode_diploma_image_missing"] = True
        return {"object": paper.name, "image": None, "removed_old_details": old_details}

    mat_name = "CATHODE_DIPLOMA_GRAYSCALE"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emission_node = nodes.new("ShaderNodeEmission")
    emission_node.inputs["Strength"].default_value = 0.92
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    bw = nodes.new("ShaderNodeRGBToBW")
    ramp = nodes.new("ShaderNodeValToRGB")
    # Compress the diploma's white paper and gold seal into the same restrained
    # charcoal/mid-grey range as the room while preserving legible dark type.
    ramp.color_ramp.interpolation = "EASE"
    elems = ramp.color_ramp.elements
    elems[0].position, elems[0].color = 0.0, (0.035, 0.035, 0.035, 1.0)
    elems[1].position, elems[1].color = 1.0, (0.30, 0.30, 0.30, 1.0)
    mid = elems.new(0.72)
    mid.color = (0.20, 0.20, 0.20, 1.0)
    links.new(tex.outputs["Color"], bw.inputs["Color"])
    links.new(bw.outputs["Val"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission_node.inputs["Color"])
    links.new(emission_node.outputs["Emission"], out.inputs["Surface"])

    # Make one flush mesh for the whole frame: the center quad carries the
    # native-aspect diploma, while top/bottom quads carry a matching paper fill.
    # Keeping these coplanar removes the floating/stacked-plane appearance.
    frame_width, frame_height = 0.52, 0.66
    aspect = image.size[0] / float(image.size[1])
    x_world = 2.6165
    y_center, z_center = -2.28, 2.10
    image_width = frame_width
    image_height = image_width / aspect
    y0, y1 = y_center - image_width / 2.0, y_center + image_width / 2.0
    z0, z1 = z_center - image_height / 2.0, z_center + image_height / 2.0
    frame_y0, frame_y1 = y_center - frame_width / 2.0, y_center + frame_width / 2.0
    frame_z0, frame_z1 = z_center - frame_height / 2.0, z_center + frame_height / 2.0
    fill_mat = bpy.data.materials.get("CATHODE_DIPLOMA_PAPER_FILL")
    if fill_mat is None:
        fill_mat = bpy.data.materials.new("CATHODE_DIPLOMA_PAPER_FILL")
    fill_mat.use_nodes = True
    fill_nodes = fill_mat.node_tree.nodes
    fill_links = fill_mat.node_tree.links
    fill_nodes.clear()
    fill_out = fill_nodes.new("ShaderNodeOutputMaterial")
    fill_emission = fill_nodes.new("ShaderNodeEmission")
    # Match the white endpoint of CATHODE_DIPLOMA_GRAYSCALE exactly so the
    # preserved-aspect artwork blends into the added top/bottom fill.
    fill_emission.inputs["Color"].default_value = (0.30, 0.30, 0.30, 1.0)
    fill_emission.inputs["Strength"].default_value = 0.92
    fill_links.new(fill_emission.outputs["Emission"], fill_out.inputs["Surface"])
    verts = []
    faces = []
    material_indices = []
    uv_coords = []

    def append_quad(qa, qb, za, zb, material_index, coords):
        base = len(verts)
        verts.extend([
            (x_world, qa, za), (x_world, qa, zb),
            (x_world, qb, zb), (x_world, qb, za),
        ])
        faces.append((base, base + 1, base + 2, base + 3))
        material_indices.append(material_index)
        uv_coords.append(coords)

    # All three quads use the same -X-facing winding and share one plane.
    append_quad(y0, y1, frame_z0, z0, 1,
                ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)))
    append_quad(y0, y1, z0, z1, 0,
                ((1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)))
    append_quad(y0, y1, z1, frame_z1, 1,
                ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)))
    mesh = bpy.data.meshes.new("ART_DiplomaPaper_Grayscale_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    mesh.materials.append(mat)
    mesh.materials.append(fill_mat)
    for poly, material_index, coords in zip(mesh.polygons, material_indices, uv_coords):
        poly.material_index = material_index
    uv = mesh.uv_layers.new(name="UVMap")
    # The wall is viewed from negative X, where increasing world Y projects to
    # screen-left. Reverse U so the supplied diploma reads left-to-right.
    for poly, coords in zip(mesh.polygons, uv_coords):
        for loop_index, coord in zip(poly.loop_indices, coords):
            uv.data[loop_index].uv = coord
    paper.data = mesh
    paper.location = (0.0, 0.0, 0.0)
    paper["cathode_suppress_flow_outline"] = True
    paper["cathode_diploma_frame_fill"] = "coplanar top/bottom quads in this single mesh"
    paper["cathode_diploma_image"] = image.name
    paper["cathode_diploma_fit"] = "native aspect centered with coplanar edge-to-edge INTERACT_Diploma paper fill"
    paper["cathode_diploma_grayscale_material"] = mat.name
    paper["cathode_diploma_world_bounds"] = [x_world, y0, y1, z0, z1]
    return {
        "object": paper.name,
        "image": image.name,
        "image_source": str(image_path),
        "material": mat.name,
        "frame_fill": "coplanar_quads_in_ART_DiplomaPaper",
        "frame_fill_material": fill_mat.name,
        "removed_old_details": old_details,
        "center": [y_center, z_center],
        "size": [round(image_width, 6), round(image_height, 6)],
        "aspect_ratio": round(aspect, 6),
        "fit_mode": "native_aspect_with_coplanar_edge_to_edge_frame_fill",
        "flush_x": x_world,
    }


def rebuild_pulsar_map(mats):
    """Model a restrained pulsar map as raised rods attached to the frame."""
    removed = []
    for ob in list(bpy.data.objects):
        upper = ob.name.upper()
        if upper.startswith(("ART_PULSARRAY_", "ART_PULSARSTAR_")) or ob.name in {
            "CATHODE_PULSAR_MAP_FIELD", "CATHODE_PULSAR_MAP_LINES",
            "CATHODE_PULSAR_MAP_MODEL",
        }:
            removed.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)

    back = bpy.data.objects.get("ART_PulsarMap_Back")
    if back is None:
        return {"field": None, "model": None, "ray_count": 0,
                "signal_ticks": 0, "removed": removed}

    # The existing back panel is the physical dark ground. All new marks are
    # actual mesh rods a few millimetres in front of it, not a pasted image.
    front_x = min((back.matrix_world @ vertex.co).x for vertex in back.data.vertices)
    x = front_x - 0.008
    # The camera reads increasing world Y as screen-left, so placing the hub
    # at -1.48 makes the convergence point clearly left of frame center.
    center = Vector((x, -1.48, 2.10))
    y_min, y_max = -1.83, -1.34
    z_min, z_max = 1.81, 2.39
    line_radius = 0.0032
    mesh_name = "CATHODE_PULSAR_MAP_MODEL"
    verts = []
    faces = []

    def add_cylinder(a, b, radius=line_radius, sides=8):
        """Append a capped cylinder segment to the shared map mesh."""
        a, b = Vector(a), Vector(b)
        axis = b - a
        if axis.length < 1.0e-6:
            return
        axis.normalize()
        ref = Vector((1.0, 0.0, 0.0))
        if abs(axis.dot(ref)) > 0.92:
            ref = Vector((0.0, 1.0, 0.0))
        u = axis.cross(ref).normalized()
        v = axis.cross(u).normalized()
        base = len(verts)
        for point in (a, b):
            for i in range(sides):
                angle = math.tau * i / sides
                verts.append(tuple(point + radius * (math.cos(angle) * u + math.sin(angle) * v)))
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((base + i, base + j, base + sides + j, base + sides + i))
        faces.append(tuple(base + i for i in reversed(range(sides))))
        faces.append(tuple(base + sides + i for i in range(sides)))

    angles = (0.00, 0.31, 0.66, 1.06, 1.50, 2.04, 2.53, 2.98,
              3.56, 4.04, 4.50, 4.72, 5.25, 5.78)
    factors = (1.00, 0.88, 0.93, 0.98, 0.84, 1.00, 0.92, 0.86,
               0.96, 1.00, 0.90, 0.95, 1.00, 0.88)
    for ray_index, (angle, factor) in enumerate(zip(angles, factors)):
        direction = Vector((math.cos(angle), math.sin(angle)))
        # Find the distance to the correct inner frame edge, then vary the
        # endpoint slightly so the drawing has the asymmetry of a real map.
        candidates = []
        if abs(direction.x) > 1.0e-6:
            candidates.append(((y_max if direction.x > 0 else y_min) - center.y) / direction.x)
        if abs(direction.y) > 1.0e-6:
            candidates.append(((z_max if direction.y > 0 else z_min) - center.z) / direction.y)
        boundary = min(value for value in candidates if value > 0)
        length = boundary * factor
        end = Vector((x, center.y + direction.x * length,
                      center.z + direction.y * length))
        add_cylinder(center, end)

    # Physical hub and a short standoff tie the radial assembly into the
    # existing framed backing rather than leaving a floating 2D drawing.
    add_cylinder((front_x + 0.001, center.y, center.z),
                 (front_x - 0.016, center.y, center.z), radius=0.018, sides=12)

    mesh = bpy.data.meshes.new(mesh_name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    model = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.scene.collection.objects.link(model)
    model.data.materials.append(mats["white"])
    model["cathode_pulsar_map_model"] = True
    model["cathode_pulsar_map_attached_to"] = "ART_PulsarMap_Back"
    model["cathode_pulsar_map_ray_count"] = len(angles)
    model["cathode_pulsar_map_signal_ticks"] = 0
    model["cathode_pulsar_map_line_weight"] = line_radius
    return {
        "field": None,
        "model": model.name,
        "ray_count": len(angles),
        "signal_ticks": 0,
        "removed": removed,
    }


def preserve_targets():
    targets = []
    for ob in bpy.data.objects:
        if is_preserved(ob.name):
            ob["cathode_preserved"] = True
            targets.append(ob.name)
    return targets


def add_room_ink(scene):
    # Use the current active camera and a small camera-local line collection;
    # this is deliberately restrained and never hides the underlying geometry.
    cam = scene.camera
    if cam is None:
        return []
    coll = bpy.data.collections.get("CATHODE_RESTYLE")
    if coll is None:
        coll = bpy.data.collections.new("CATHODE_RESTYLE")
        scene.collection.children.link(coll)
    return []


def main():
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not input_path.exists():
        raise FileNotFoundError("Input Blender file not found: %s" % input_path)
    bpy.ops.wm.open_mainfile(filepath=str(input_path))
    scene = bpy.context.scene
    scene["cathode_source_file"] = str(input_path)
    scene["cathode_restyle_version"] = "v55"
    remove_old_exterior()
    removed_top_plant, removed_platform = remove_requested_geometry()
    floor_grid = make_floor_squares()
    shelf_tuck = tuck_right_shelf_flush()
    copy_original_materials()
    mats = style_materials()
    changed = apply_values(mats)
    arm_restyled = restyle_record_player_arm(mats)
    shelf_rebuild = rebuild_shelf_contents()
    horizontal_book_stack = restore_and_reorder_horizontal_book_stack()
    vertical_book_run = seat_vertical_book_run()
    vertical_book_lean = lean_leftmost_vertical_book()
    camera_shelf_fix = rebuild_camera_and_tuck_shelf_items(mats)
    vinyl_rack_hollows = hollow_vinyl_racks()
    vinyl_holder_separation = separate_vinyl_holders()
    camera_lens_fix = seat_camera_lens()
    camera_lens_alignment = align_camera_lens_centerline()
    camera_outer_ring = remove_camera_outer_lens_ring()
    polaroid_recomposition = recompose_polaroids()
    polaroid_layer_separation = separate_polaroid_stack_layers()
    polaroid_surface_styling = style_polaroid_surfaces(mats)
    other_vinyls_restored = restore_other_vinyls()
    left_vinyl_seating = seat_left_vinyl()
    left_vinyl_contact = tighten_left_vinyl_contact()
    vinyl_row_shift = shift_all_vinyls_left()
    steepened_vinyl_clearance = clear_steepened_leftmost_vinyl()
    vinyl_system_expansion = {"applied": False, "reason": "dimensions preserved; positional fixes only"}
    diploma = replace_diploma_with_image(mats)
    pulsar_map = rebuild_pulsar_map(mats)
    targets = preserve_targets()
    restyle_coll = bpy.data.collections.get("CATHODE_RESTYLE")
    if restyle_coll is None:
        restyle_coll = bpy.data.collections.new("CATHODE_RESTYLE")
        scene.collection.children.link(restyle_coll)
    flat_exterior = add_flat_exterior(scene, restyle_coll)
    opened_glass = open_window_glass_for_exterior()
    flow_obj, flow_edges = add_flowing_outlines(scene, restyle_coll)
    # The existing rain/lightning animation and timeline are intentionally left
    # untouched. Record them for the QA report instead of rewriting them.
    frame_start, frame_end, fps = scene.frame_start, scene.frame_end, scene.render.fps
    scene.world.color = (0.002, 0.002, 0.002)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    # Keep the render path native in Blender 5.2; the flowing ink remains
    # bright without requiring a compositor output node (which was removed
    # from the default node set in this release).
    if args.render:
        original_frame = scene.frame_current
        scene.frame_set(max(scene.frame_start, min(scene.frame_end, args.frame)))
        scene.render.filepath = str(Path(args.render).resolve())
        bpy.ops.render.render(write_still=True)
        scene.frame_set(original_frame)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    report_path = output_path.with_name(output_path.stem + "-report.json")
    with report_path.open("w", encoding="utf-8") as f:
        json.dump({
            "source": str(input_path),
            "output": str(output_path),
            "changed_mesh_objects": changed,
            "preserved_named_objects": targets,
            "materials": [m.name for m in mats.values()],
            "flat_exterior": flat_exterior.name if flat_exterior else None,
            "flat_exterior_style": flat_exterior.get("cathode_flat_exterior_style") if flat_exterior else None,
            "window_glass_hidden": opened_glass,
            "removed_shelf_top_plant": removed_top_plant,
            "removed_extra_floor_plane": removed_platform,
            "floor_grid_square_fix": floor_grid,
            "shelf_flush_fix": shelf_tuck,
            "record_player_arm_restyled": arm_restyled,
            "shelf_rebuild": shelf_rebuild,
            "horizontal_book_stack": horizontal_book_stack,
            "vertical_book_run": vertical_book_run,
            "vertical_book_lean": vertical_book_lean,
            "camera_and_shelf_depth_fix": camera_shelf_fix,
            "vinyl_rack_hollows": vinyl_rack_hollows,
            "vinyl_holder_separation": vinyl_holder_separation,
            "vinyl_system_expansion": vinyl_system_expansion,
            "camera_lens_fix": camera_lens_fix,
            "camera_lens_alignment": camera_lens_alignment,
            "camera_outer_ring_removed": camera_outer_ring,
            "polaroid_recomposition": polaroid_recomposition,
            "polaroid_layer_separation": polaroid_layer_separation,
            "polaroid_surface_styling": polaroid_surface_styling,
            "other_vinyls_restored": other_vinyls_restored,
            "left_vinyl_seating": left_vinyl_seating,
            "left_vinyl_contact": left_vinyl_contact,
            "vinyl_row_shift": vinyl_row_shift,
            "steepened_vinyl_clearance": steepened_vinyl_clearance,
            "diploma_rebuild": diploma,
            "pulsar_map_rebuild": pulsar_map,
            "flow_outline_object": flow_obj.name if flow_obj else None,
            "flow_outline_edges": flow_edges,
            "flow_animation": {
                "start_frame": 1,
                "end_frame": 240,
                "clock_delta": 4.0 * math.pi,
                "interpolation": "LINEAR",
                "cycles_modifier": True,
                "seamless_phase_match": True,
            },
            "modeled_exterior_removed": True,
            "timeline": {"start": frame_start, "end": frame_end, "fps": fps},
            "layout_rebuilt": False,
            "interaction_contract_rebuilt": False,
        }, f, indent=2)
    print("Cathode room restyle written to", output_path)


if __name__ == "__main__":
    main()
