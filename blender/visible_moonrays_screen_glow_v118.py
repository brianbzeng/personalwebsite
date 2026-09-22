"""Make the moonlight readable and move monitor glow to an enlarged screen face."""

from pathlib import Path
import argparse
import json
import math
import sys

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v117-soft-downright-light.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v118-visible-rays-screen-glow.blend"),
    )
    parser.add_argument("--render-dir", default=str(HERE / "outputs" / "blender"))
    return parser.parse_args(argv)


def remove_prefixed(prefix):
    removed = []
    for ob in list(bpy.data.objects):
        if ob.name.startswith(prefix):
            removed.append(ob.name)
            bpy.data.objects.remove(ob, do_unlink=True)
    return removed


def emission_material(name, color, strength):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (*color, 1.0)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1.0)
    emission.inputs["Strength"].default_value = strength
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def create_quad(name, corners, material, tag):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(corners, [], [(0, 1, 2, 3)])
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob[tag] = True
    return ob


def create_band(name, center, direction, perpendicular, length, width, material):
    along = direction * (length * 0.5)
    across = perpendicular * (width * 0.5)
    corners = [
        center - along - across,
        center + along - across,
        center + along + across,
        center - along + across,
    ]
    return create_quad(
        name,
        [tuple(corner) for corner in corners],
        material,
        "cathode_visible_moonray_landing_v118",
    )


def rebuild_visible_moonrays():
    removed = remove_prefixed("CATHODE_DeskBlindProjection_")
    core_material = emission_material(
        "CATHODE_MoonrayLanding_Core_v118",
        (0.76, 0.81, 0.92),
        1.05,
    )
    feather_material = emission_material(
        "CATHODE_MoonrayLanding_Feather_v118",
        (0.48, 0.53, 0.63),
        0.34,
    )
    angle = math.radians(120.0)
    direction = Vector((math.cos(angle), math.sin(angle), 0.0)).normalized()
    perpendicular = Vector((-direction.y, direction.x, 0.0)).normalized()
    center = Vector((0.14, 1.94, 0.83145))
    length = 0.62
    offsets = (-0.135, -0.090, -0.045, 0.0, 0.045, 0.090, 0.135)
    created = []
    for index, offset in enumerate(offsets):
        band_center = center + perpendicular * offset
        feather = create_band(
            f"CATHODE_DeskBlindProjection_Feather_{index:02d}_v118",
            Vector((band_center.x, band_center.y, 0.83142)),
            direction,
            perpendicular,
            length,
            0.060,
            feather_material,
        )
        core = create_band(
            f"CATHODE_DeskBlindProjection_Core_{index:02d}_v118",
            Vector((band_center.x, band_center.y, 0.83147)),
            direction,
            perpendicular,
            length,
            0.020,
            core_material,
        )
        created.extend((feather.name, core.name))

    physical = []
    for ob in bpy.data.objects:
        if ob.name.startswith("LIGHT_WindowGapBand_") and ob.type == "LIGHT":
            ob.data.energy = 260.0
            ob.data.color = (0.82, 0.87, 1.0)
            physical.append(ob.name)
    for name in ("LIGHT_WindowWest", "LIGHT_WindowEast"):
        ob = bpy.data.objects.get(name)
        if ob is not None and ob.type == "LIGHT":
            ob.data.energy = 34.0

    return {
        "removed": removed,
        "created": created,
        "visible_band_count": len(offsets),
        "physical_gap_lights_strengthened": physical,
        "direction": "visually_down_and_right",
    }


def near(value, target, tolerance=0.002):
    return abs(value - target) <= tolerance


def enlarge_monitor_aperture_mesh(ob):
    if ob is None or ob.type != "MESH":
        return 0
    changed = 0
    for vert in ob.data.vertices:
        x, y, z = vert.co
        original = vert.co.copy()

        # Body aperture: enlarge the opening while preserving the outer shell.
        if near(abs(x), 0.615) and (near(z, 0.935) or near(z, 1.385)):
            x = math.copysign(0.655, x)
        if near(z, 0.935) and abs(x) <= 0.656:
            z = 0.905
        elif near(z, 1.385) and abs(x) <= 0.656:
            z = 1.415

        # Screen outline: follow the enlarged display rectangle exactly.
        if near(abs(x), 0.595) and (near(z, 0.945) or near(z, 1.375)):
            x = math.copysign(0.635, x)
        if near(z, 0.945) and abs(x) <= 0.636:
            z = 0.915
        elif near(z, 1.375) and abs(x) <= 0.636:
            z = 1.405

        vert.co = (x, y, z)
        if (vert.co - original).length > 1e-6:
            changed += 1
    ob.data.update()
    return changed


def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def limit_distance(data, distance):
    if hasattr(data, "use_custom_distance"):
        data.use_custom_distance = True
        data.cutoff_distance = distance


def lighting_collection():
    collection = bpy.data.collections.get("LIGHTING")
    if collection is None:
        collection = bpy.data.collections.new("LIGHTING")
        bpy.context.scene.collection.children.link(collection)
    return collection


def ensure_point(name, location):
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != "LIGHT":
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
        data = bpy.data.lights.new(name + "_Data", "POINT")
        ob = bpy.data.objects.new(name, data)
        lighting_collection().objects.link(ob)
    ob.data.type = "POINT"
    ob.location = location
    return ob


def enlarge_screen_and_move_glow():
    removed_rear_plane = remove_prefixed("CATHODE_MonitorAura_")

    # Disable every rear-facing halo element so the glow reads from the display.
    disabled_rear = []
    for name in (
        "LIGHT_MonitorAuraBack_v113",
        "LIGHT_MonitorHalo_TL_v114",
        "LIGHT_MonitorHalo_TR_v114",
        "LIGHT_MonitorHalo_BL_v114",
        "LIGHT_MonitorHalo_BR_v114",
    ):
        ob = bpy.data.objects.get(name)
        if ob is not None and ob.type == "LIGHT":
            ob.data.energy = 0.0
            ob.hide_render = True
            disabled_rear.append(name)

    screen = bpy.data.objects.get("INTERACT_Monitor_Screen")
    old_dimensions = tuple(screen.dimensions) if screen is not None else None
    if screen is not None:
        screen.dimensions = (1.27, 0.012, 0.49)
        bpy.context.view_layer.objects.active = screen
        screen.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        screen.select_set(False)

    body_changed = enlarge_monitor_aperture_mesh(bpy.data.objects.get("INTERACT_Monitor_Body"))
    outline_changed = enlarge_monitor_aperture_mesh(bpy.data.objects.get("CATHODE_ASSEMBLY_OUTLINE_Monitor"))

    material = bpy.data.materials.get("CATHODE_MONITOR_WHITE_EMISSION_v111")
    emission_strength = None
    if material is not None and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "EMISSION":
                node.inputs["Strength"].default_value = 1.55
                emission_strength = 1.55

    front = bpy.data.objects.get("LIGHT_MonitorWhite_v111")
    if front is not None and front.type == "LIGHT":
        front.hide_render = False
        front.location = (0.0, 2.414, 1.16)
        aim(front, (0.0, 1.42, 0.80))
        front.data.energy = 112.0
        front.data.color = (0.86, 0.91, 1.0)
        front.data.shape = "RECTANGLE"
        front.data.size = 1.21
        front.data.size_y = 0.45
        front.data.spread = math.radians(105.0)
        front.data.use_shadow = True
        limit_distance(front.data, 1.45)

    screen_face_points = []
    for suffix, location in (
        ("TL", (-0.48, 2.420, 1.34)),
        ("TR", (0.48, 2.420, 1.34)),
        ("BL", (-0.48, 2.420, 0.98)),
        ("BR", (0.48, 2.420, 0.98)),
    ):
        point = ensure_point(f"LIGHT_MonitorScreenFace_{suffix}_v118", location)
        point.data.energy = 20.0
        point.data.color = (0.84, 0.90, 1.0)
        point.data.shadow_soft_size = 0.13
        point.data.use_shadow = True
        point.data.specular_factor = 0.10
        limit_distance(point.data, 0.55)
        point["cathode_monitor_screen_face_glow_v118"] = True
        screen_face_points.append(point.name)

    return {
        "removed_rear_plane": removed_rear_plane,
        "disabled_rear_lights": disabled_rear,
        "screen_old_dimensions": list(old_dimensions) if old_dimensions else None,
        "screen_new_dimensions": list(screen.dimensions) if screen else None,
        "body_vertices_changed": body_changed,
        "outline_vertices_changed": outline_changed,
        "screen_emission_strength": emission_strength,
        "front_area_light": front.name if front else None,
        "screen_face_points": screen_face_points,
    }


def qa_camera(name, location, target, lens):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.cameras.new(name + "_Data")
    camera = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    camera.data.lens = lens
    aim(camera, target)
    return camera


def render(scene, camera, path, size):
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

    moonrays = rebuild_visible_moonrays()
    monitor = enlarge_screen_and_move_glow()
    scene["cathode_visible_moonrays_v118"] = True
    scene["cathode_monitor_screen_face_glow_v118"] = True
    scene["cathode_restyle_version"] = "v118"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "moonrays": qa_camera(
            "CAM_QA_VisibleMoonrays_v118",
            (-2.45, -0.15, 2.82),
            (-0.10, 1.92, 0.87),
            48.0,
        ),
        "monitor": qa_camera(
            "CAM_QA_ExpandedScreenGlow_v118",
            (-1.55, 0.82, 1.75),
            (0.0, 2.43, 1.18),
            60.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v118-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v118-visible-rays-screen-glow-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "moonrays": moonrays,
        "monitor": monitor,
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V118_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
