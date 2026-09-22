"""White/grey lighting pass, blind-wand attachment, mouse-pad fit, and exterior reset."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v110-cubby-thin-blinds.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v111-white-moonlight.blend"),
    )
    parser.add_argument("--render-dir", default=str(HERE / "outputs" / "blender"))
    return parser.parse_args(argv)


def world_bounds(ob):
    points = [ob.matrix_world @ Vector(corner) for corner in ob.bound_box]
    return {
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
    }


def rounded_bounds(ob):
    result = world_bounds(ob)
    return {key: [round(value, 6) for value in values] for key, values in result.items()}


def matrix_values(ob):
    return tuple(round(value, 9) for row in ob.matrix_world for value in row)


def snapshot_transforms():
    return {ob.name: matrix_values(ob) for ob in bpy.data.objects}


def remove_object(name):
    ob = bpy.data.objects.get(name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
        return True
    return False


def remove_collection_tree(name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        return {"collection": name, "objects": 0, "children": 0, "status": "missing"}
    all_collections = []

    def gather(current):
        for child in current.children:
            gather(child)
        all_collections.append(current)

    gather(collection)
    objects = set()
    for current in all_collections:
        objects.update(current.objects)
    for ob in objects:
        bpy.data.objects.remove(ob, do_unlink=True)
    for current in all_collections:
        if bpy.data.collections.get(current.name) is not None:
            bpy.data.collections.remove(current)
    return {
        "collection": name,
        "objects": len(objects),
        "children": max(0, len(all_collections) - 1),
        "status": "removed",
    }


def clear_exterior():
    reports = [
        remove_collection_tree("CATHODE_WINDOW_RAIN"),
        remove_collection_tree("CATHODE_EXTERIOR_STORM_STAGE"),
    ]
    # Clean any orphaned exterior helpers that were linked outside those collections.
    prefixes = ("CATHODE_RAIN_", "CATHODE_STORM_")
    extras = [ob.name for ob in bpy.data.objects if ob.name.startswith(prefixes)]
    for name in extras:
        remove_object(name)
    return {"collections": reports, "orphaned_helpers_removed": extras}


def attach_blind_wands():
    reports = []
    target_top = 2.635
    for index in (1, 2):
        cord = bpy.data.objects.get(f"WINDOW_{index}_BlindCord")
        pull = bpy.data.objects.get(f"WINDOW_{index}_BlindPull")
        if cord is None:
            reports.append({"window": index, "status": "missing_cord"})
            continue
        before = rounded_bounds(cord)
        current = world_bounds(cord)
        bottom = current["min"][2]
        extension = max(0.0, target_top - current["max"][2])
        if extension:
            cord.dimensions.z += extension
            cord.location.z += extension * 0.5
            bpy.context.view_layer.objects.active = cord
            cord.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            cord.select_set(False)
        bpy.context.view_layer.update()
        outline = V106.replace_outline(cord, thickness=0.005)
        outline.matrix_world = cord.matrix_world.copy()
        cord["cathode_attached_to_headrail_v111"] = True
        after = rounded_bounds(cord)
        pull_bounds = rounded_bounds(pull) if pull else None
        reports.append({
            "window": index,
            "status": "wand_extended_to_headrail",
            "before": before,
            "after": after,
            "bottom_preserved": abs(after["min"][2] - bottom) < 1e-5,
            "headrail_target_z": target_top,
            "pull": pull_bounds,
            "outline": outline.name,
        })
    return reports


def enlarge_mouse_pad():
    pad = bpy.data.objects.get("DESK_MousePad")
    desk = bpy.data.objects.get("DESK_Carcass_Cohesive")
    monitor_base = bpy.data.objects.get("DESK_MonitorBase")
    if pad is None or desk is None or monitor_base is None:
        return {"status": "missing_required_object"}
    before = rounded_bounds(pad)
    pad.location.y = 1.92
    pad.dimensions = (2.50, 0.64, 0.009)
    bpy.context.view_layer.objects.active = pad
    pad.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    pad.select_set(False)
    bpy.context.view_layer.update()
    outline = V106.replace_outline(pad, thickness=0.005)
    outline.matrix_world = pad.matrix_world.copy()
    after = rounded_bounds(pad)
    desk_bounds = rounded_bounds(desk)
    monitor_bounds = rounded_bounds(monitor_base)
    pad["cathode_expanded_mousepad_v111"] = True
    return {
        "status": "expanded_rectangle_with_clearances",
        "before": before,
        "after": after,
        "desk": desk_bounds,
        "monitor_base": monitor_bounds,
        "inside_desktop_xy": (
            after["min"][0] > desk_bounds["min"][0]
            and after["max"][0] < desk_bounds["max"][0]
            and after["min"][1] > desk_bounds["min"][1]
            and after["max"][1] < desk_bounds["max"][1]
        ),
        "clear_of_monitor_base": after["max"][1] < monitor_bounds["min"][1],
        "outline": outline.name,
    }


def white_emission_material():
    material = bpy.data.materials.get("CATHODE_MONITOR_WHITE_EMISSION_v111")
    if material is None:
        material = bpy.data.materials.new("CATHODE_MONITOR_WHITE_EMISSION_v111")
    material.use_nodes = True
    material.diffuse_color = (0.92, 0.94, 1.0, 1.0)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.92, 0.95, 1.0, 1.0)
    emission.inputs["Strength"].default_value = 3.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def light_collection():
    collection = bpy.data.collections.get("LIGHTING")
    if collection is None:
        collection = bpy.data.collections.new("LIGHTING")
        bpy.context.scene.collection.children.link(collection)
    return collection


def ensure_light(name, kind):
    existing = bpy.data.objects.get(name)
    if existing is not None and existing.type == "LIGHT":
        existing.data.type = kind
        return existing
    if existing is not None:
        bpy.data.objects.remove(existing, do_unlink=True)
    data = bpy.data.lights.new(name + "_Data", kind)
    ob = bpy.data.objects.new(name, data)
    light_collection().objects.link(ob)
    return ob


def configure_area(name, location, target, energy, color, size, size_y):
    light = ensure_light(name, "AREA")
    light.location = location
    aim(light, target)
    light.data.energy = energy
    light.data.color = color
    light.data.shape = "RECTANGLE"
    light.data.size = size
    light.data.size_y = size_y
    return light


def configure_spot(name, location, target, energy, color):
    light = ensure_light(name, "SPOT")
    light.location = location
    aim(light, target)
    light.data.energy = energy
    light.data.color = color
    light.data.spot_size = math.radians(58.0)
    light.data.spot_blend = 0.62
    light.data.shadow_soft_size = 0.18
    return light


def configure_sun(name, direction_target, energy, color):
    light = ensure_light(name, "SUN")
    light.location = (0.0, 2.9, 3.15)
    aim(light, direction_target)
    light.data.energy = energy
    light.data.color = color
    light.data.angle = math.radians(2.5)
    return light


def create_room_haze():
    remove_object("VOLUME_MoonlightHaze_v111")
    material = bpy.data.materials.get("VOLUME_MoonlightHaze_Material_v111")
    if material is None:
        material = bpy.data.materials.new("VOLUME_MoonlightHaze_Material_v111")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (0.72, 0.78, 0.88, 1.0)
    volume.inputs["Density"].default_value = 0.006
    volume.inputs["Anisotropy"].default_value = 0.35
    links.new(volume.outputs["Volume"], output.inputs["Volume"])

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 1.60))
    haze = bpy.context.object
    haze.name = "VOLUME_MoonlightHaze_v111"
    haze.dimensions = (5.50, 5.50, 3.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    haze.data.materials.append(material)
    haze.display_type = "WIRE"
    haze.hide_select = True
    haze["cathode_subtle_moonlight_volume_v111"] = True
    return haze


def configure_lighting():
    screen = bpy.data.objects.get("INTERACT_Monitor_Screen")
    if screen is None:
        raise RuntimeError("Monitor screen missing")
    screen.data.materials.clear()
    screen.data.materials.append(white_emission_material())
    for polygon in screen.data.polygons:
        polygon.material_index = 0
    screen["cathode_white_monitor_emission_v111"] = True

    disabled = {}
    for name in ("LIGHT_DeskLamp", "LIGHT_NeonEast", "LIGHT_NeonNorth", "LIGHT_NeonFill"):
        light = bpy.data.objects.get(name)
        if light is not None and light.type == "LIGHT":
            disabled[name] = light.data.energy
            light.data.energy = 0.0

    soft_key = bpy.data.objects.get("LIGHT_SoftKey")
    if soft_key is not None and soft_key.type == "LIGHT":
        soft_key.data.energy = 28.0
        soft_key.data.color = (0.72, 0.74, 0.78)

    cool_white = (0.72, 0.80, 1.0)
    window_lights = []
    for index, (name, x) in enumerate((("LIGHT_WindowWest", -1.4), ("LIGHT_WindowEast", 1.4)), 1):
        area = configure_area(
            name,
            (x, 2.86, 2.12),
            (x, 0.75, 0.92),
            520.0,
            cool_white,
            1.28,
            1.30,
        )
        ray = configure_spot(
            f"LIGHT_MoonRays_Window{index}_v111",
            (x, 2.98, 2.55),
            (x, 0.40, 0.68),
            330.0,
            cool_white,
        )
        window_lights.extend([area.name, ray.name])

    moon_sun = configure_sun(
        "LIGHT_MoonDirectional_v111",
        (0.0, -0.55, 0.62),
        1.15,
        cool_white,
    )
    window_lights.append(moon_sun.name)

    monitor = configure_area(
        "LIGHT_MonitorWhite_v111",
        (0.0, 2.405, 1.17),
        (0.0, 0.95, 0.84),
        200.0,
        (0.92, 0.95, 1.0),
        1.05,
        0.40,
    )
    monitor.data.spread = math.radians(115.0)
    haze = create_room_haze()

    world = bpy.context.scene.world
    if world is not None:
        world.color = (0.001, 0.002, 0.004)
        if world.use_nodes:
            background = world.node_tree.nodes.get("Background")
            if background is not None:
                background.inputs["Color"].default_value = (0.002, 0.004, 0.009, 1.0)
                background.inputs["Strength"].default_value = 0.045

    scene = bpy.context.scene
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = -0.30
    return {
        "monitor_screen": screen.name,
        "monitor_light": monitor.name,
        "disabled_lights": disabled,
        "window_lights": window_lights,
        "neutral_soft_key_energy": soft_key.data.energy if soft_key else None,
        "haze": haze.name,
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


def audit(before, allowed_changed, allowed_deleted):
    changed = []
    deleted = []
    for name, old_matrix in before.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            if name not in allowed_deleted and not name.startswith(("CATHODE_RAIN_", "CATHODE_STORM_")):
                deleted.append(name)
            continue
        if matrix_values(ob) != old_matrix and name not in allowed_changed:
            changed.append(name)
    if changed or deleted:
        raise RuntimeError(f"Unexpected scene changes: changed={changed}, deleted={deleted}")
    return {"unexpected_changed": changed, "unexpected_deleted": deleted}


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
    before = snapshot_transforms()
    exterior_names = {
        ob.name
        for collection_name in ("CATHODE_WINDOW_RAIN", "CATHODE_EXTERIOR_STORM_STAGE")
        if (collection := bpy.data.collections.get(collection_name)) is not None
        for ob in collection.all_objects
    }

    exterior = clear_exterior()
    wands = attach_blind_wands()
    mouse_pad = enlarge_mouse_pad()
    lighting = configure_lighting()
    bpy.context.view_layer.update()

    allowed_changed = {
        "WINDOW_1_BlindCord", "WINDOW_2_BlindCord", "DESK_MousePad",
        "LIGHT_WindowWest", "LIGHT_WindowEast",
        "CATHODE_WIREFRAME_WINDOW_1_BlindCord",
        "CATHODE_WIREFRAME_WINDOW_2_BlindCord",
        "CATHODE_WIREFRAME_DESK_MousePad",
    }
    allowed_deleted = exterior_names | {
        "CATHODE_WIREFRAME_WINDOW_1_BlindCord",
        "CATHODE_WIREFRAME_WINDOW_2_BlindCord",
        "CATHODE_WIREFRAME_DESK_MousePad",
    }
    scene_audit = audit(before, allowed_changed, allowed_deleted)

    scene["cathode_white_moonlight_pass_v111"] = True
    scene["cathode_restyle_version"] = "v111"
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "desk": qa_camera("CAM_QA_WhiteMonitorMousePad_v111", (-2.65, -1.05, 2.45), (0.0, 2.05, 1.02), 48.0),
        "windows": qa_camera("CAM_QA_MoonlitWindows_v111", (0.0, -0.65, 2.15), (0.0, 2.62, 2.02), 44.0),
        "wand": qa_camera("CAM_QA_AttachedBlindWand_v111", (0.82, 0.62, 2.25), (1.98, 2.61, 2.33), 58.0),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v111-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v111-lighting-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "exterior": exterior,
        "blind_wands": wands,
        "mouse_pad": mouse_pad,
        "lighting": lighting,
        "audit": scene_audit,
        "renders": renders,
    }
    report_path = output_path.with_name(output_path.stem + "-report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("V111_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
