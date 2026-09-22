"""Project parallel down-right light bands through blind gaps and strengthen the monitor halo."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v113-directed-window-patterns.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v114-blind-gap-patterns.blend"),
    )
    parser.add_argument("--render-dir", default=str(HERE / "outputs" / "blender"))
    return parser.parse_args(argv)


def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def light_collection():
    collection = bpy.data.collections.get("LIGHTING")
    if collection is None:
        collection = bpy.data.collections.new("LIGHTING")
        bpy.context.scene.collection.children.link(collection)
    return collection


def ensure_light(name, kind):
    ob = bpy.data.objects.get(name)
    if ob is not None and ob.type == "LIGHT":
        ob.data.type = kind
        return ob
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
    data = bpy.data.lights.new(name + "_Data", kind)
    ob = bpy.data.objects.new(name, data)
    light_collection().objects.link(ob)
    return ob


def remove_light(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return False
    data = ob.data if ob.type == "LIGHT" else None
    bpy.data.objects.remove(ob, do_unlink=True)
    if data is not None and data.users == 0:
        bpy.data.lights.remove(data)
    return True


def limit_distance(data, distance):
    if hasattr(data, "use_custom_distance"):
        data.use_custom_distance = True
        data.cutoff_distance = distance


def configure_gap_band(name, source):
    direction = Vector((0.90, -0.95, -1.65))
    light = ensure_light(name, "AREA")
    light.location = source
    aim(light, Vector(source) + direction)
    light.data.energy = 168.0
    light.data.color = (0.78, 0.85, 1.0)
    light.data.shape = "RECTANGLE"
    light.data.size = 0.64
    light.data.size_y = 0.012
    light.data.spread = math.radians(12.0)
    light.data.diffuse_factor = 1.0
    light.data.specular_factor = 0.08
    light.data.volume_factor = 0.0
    light.data.use_shadow = True
    limit_distance(light.data, 2.35)
    light["cathode_blind_gap_parallel_band_v114"] = True
    return light


def configure_window_patterns():
    removed = [
        name for name in ("LIGHT_WindowPatternWest_v113", "LIGHT_WindowPatternEast_v113")
        if remove_light(name)
    ]
    for name in ("LIGHT_WindowWest", "LIGHT_WindowEast"):
        light = bpy.data.objects.get(name)
        if light is not None and light.type == "LIGHT":
            light.data.energy = 24.0
            light.data.spread = math.radians(30.0)
            limit_distance(light.data, 1.15)

    gap_z = (2.0425, 2.0975, 2.1525, 2.2075, 2.2625, 2.3175, 2.3725)
    bands = []
    for window, x in ((1, -1.12), (2, 1.68)):
        for index, z in enumerate(gap_z):
            name = f"LIGHT_WindowGapBand_W{window}_{index:02d}_v114"
            light = configure_gap_band(name, (x, 2.775, z))
            bands.append({
                "name": light.name,
                "window": window,
                "source": [x, 2.775, z],
                "energy": light.data.energy,
                "spread_degrees": 12.0,
                "cutoff": light.data.cutoff_distance,
            })
    return {"removed_cones": removed, "gap_bands": bands}


def configure_halo_point(name, location, energy):
    light = ensure_light(name, "POINT")
    light.location = location
    light.data.energy = energy
    light.data.color = (0.84, 0.90, 1.0)
    light.data.shadow_soft_size = 0.20
    light.data.diffuse_factor = 1.0
    light.data.specular_factor = 0.08
    light.data.volume_factor = 0.0
    light.data.use_shadow = False
    limit_distance(light.data, 0.62)
    light["cathode_monitor_halo_point_v114"] = True
    return light


def configure_monitor_halo():
    back = bpy.data.objects.get("LIGHT_MonitorAuraBack_v113")
    if back is not None and back.type == "LIGHT":
        back.data.energy = 118.0
        back.data.spread = math.radians(125.0)
        limit_distance(back.data, 0.62)

    points = []
    for suffix, location in (
        ("TL", (-0.54, 2.585, 1.36)),
        ("TR", (0.54, 2.585, 1.36)),
        ("BL", (-0.54, 2.585, 0.96)),
        ("BR", (0.54, 2.585, 0.96)),
    ):
        point = configure_halo_point(f"LIGHT_MonitorHalo_{suffix}_v114", location, 28.0)
        points.append(point.name)

    front = bpy.data.objects.get("LIGHT_MonitorWhite_v111")
    if front is not None and front.type == "LIGHT":
        front.data.energy = 56.0
        limit_distance(front.data, 1.10)

    material = bpy.data.materials.get("CATHODE_MONITOR_WHITE_EMISSION_v111")
    emission_strength = None
    if material is not None and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "EMISSION":
                node.inputs["Strength"].default_value = 1.10
                emission_strength = 1.10
    return {
        "backlight": back.name if back else None,
        "backlight_energy": back.data.energy if back else None,
        "halo_points": points,
        "halo_point_energy": 28.0,
        "front_light_energy": front.data.energy if front else None,
        "screen_emission_strength": emission_strength,
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

    windows = configure_window_patterns()
    monitor = configure_monitor_halo()
    scene["cathode_blind_gap_patterns_v114"] = True
    scene["cathode_restyle_version"] = "v114"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "desk_pattern": qa_camera(
            "CAM_QA_DeskBands_v114",
            (-2.65, -0.35, 2.70),
            (-0.38, 2.02, 0.91),
            46.0,
        ),
        "monitor_halo": qa_camera(
            "CAM_QA_MonitorHalo_v114",
            (-1.55, 0.82, 1.75),
            (0.0, 2.50, 1.18),
            60.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v114-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v114-pattern-halo-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "windows": windows,
        "monitor": monitor,
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V114_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
