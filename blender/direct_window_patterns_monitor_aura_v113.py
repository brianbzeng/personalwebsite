"""Aim blind-filtered moonlight down-right and add a restrained monitor aura."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v112-soft-window-glow.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v113-directed-window-patterns.blend"),
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


def limit_distance(data, distance):
    if hasattr(data, "use_custom_distance"):
        data.use_custom_distance = True
        data.cutoff_distance = distance


def configure_soft_window_area(name, source, target):
    light = ensure_light(name, "AREA")
    light.location = source
    aim(light, target)
    light.data.energy = 46.0
    light.data.color = (0.76, 0.82, 0.96)
    light.data.shape = "RECTANGLE"
    light.data.size = 0.52
    light.data.size_y = 0.52
    light.data.spread = math.radians(34.0)
    light.data.diffuse_factor = 1.0
    light.data.specular_factor = 0.14
    light.data.volume_factor = 0.0
    light.data.use_shadow = True
    limit_distance(light.data, 1.35)
    light["cathode_top_right_window_soft_glow_v113"] = True
    return light


def configure_pattern_spot(name, source, target):
    light = ensure_light(name, "SPOT")
    light.location = source
    aim(light, target)
    light.data.energy = 158.0
    light.data.color = (0.78, 0.85, 1.0)
    light.data.spot_size = math.radians(24.0)
    light.data.spot_blend = 0.72
    light.data.shadow_soft_size = 0.12
    light.data.diffuse_factor = 1.0
    light.data.specular_factor = 0.10
    light.data.volume_factor = 0.0
    light.data.use_shadow = True
    limit_distance(light.data, 2.45)
    light["cathode_blind_filtered_down_right_pattern_v113"] = True
    return light


def configure_window_lighting():
    settings = [
        {
            "index": 1,
            "area_name": "LIGHT_WindowWest",
            "spot_name": "LIGHT_WindowPatternWest_v113",
            "source": (-1.12, 2.785, 2.48),
            "target": (-0.18, 1.86, 0.83),
        },
        {
            "index": 2,
            "area_name": "LIGHT_WindowEast",
            "spot_name": "LIGHT_WindowPatternEast_v113",
            "source": (1.68, 2.785, 2.48),
            "target": (2.55, 1.52, 0.55),
        },
    ]
    report = []
    for item in settings:
        area = configure_soft_window_area(item["area_name"], item["source"], item["target"])
        spot = configure_pattern_spot(item["spot_name"], item["source"], item["target"])
        report.append({
            "window": item["index"],
            "source": list(item["source"]),
            "target": list(item["target"]),
            "area": area.name,
            "area_energy": area.data.energy,
            "pattern": spot.name,
            "pattern_energy": spot.data.energy,
            "pattern_angle_degrees": 24.0,
            "pattern_cutoff": spot.data.cutoff_distance,
            "direction": "down_and_positive_x",
        })
    return report


def configure_monitor_aura():
    aura = ensure_light("LIGHT_MonitorAuraBack_v113", "AREA")
    aura.location = (0.0, 2.565, 1.17)
    aim(aura, (0.0, 2.79, 1.17))
    aura.data.energy = 58.0
    aura.data.color = (0.84, 0.89, 1.0)
    aura.data.shape = "RECTANGLE"
    aura.data.size = 1.48
    aura.data.size_y = 0.66
    aura.data.spread = math.radians(112.0)
    aura.data.diffuse_factor = 1.0
    aura.data.specular_factor = 0.08
    aura.data.volume_factor = 0.0
    aura.data.use_shadow = True
    limit_distance(aura.data, 0.52)
    aura["cathode_monitor_backlight_aura_v113"] = True

    front = bpy.data.objects.get("LIGHT_MonitorWhite_v111")
    if front is not None and front.type == "LIGHT":
        front.data.energy = 68.0
        front.data.specular_factor = 0.18
        limit_distance(front.data, 1.20)

    material = bpy.data.materials.get("CATHODE_MONITOR_WHITE_EMISSION_v111")
    emission_strength = None
    if material is not None and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "EMISSION":
                node.inputs["Strength"].default_value = 1.25
                emission_strength = 1.25
    return {
        "aura": aura.name,
        "aura_energy": aura.data.energy,
        "aura_cutoff": aura.data.cutoff_distance,
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

    windows = configure_window_lighting()
    monitor = configure_monitor_aura()
    scene["cathode_directed_window_patterns_v113"] = True
    scene["cathode_restyle_version"] = "v113"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "desk_pattern": qa_camera(
            "CAM_QA_DeskWindowPattern_v113",
            (-2.65, -0.30, 2.72),
            (-0.45, 2.02, 0.92),
            46.0,
        ),
        "monitor_aura": qa_camera(
            "CAM_QA_MonitorAura_v113",
            (-1.75, 0.72, 1.82),
            (0.0, 2.50, 1.18),
            58.0,
        ),
        "windows": qa_camera(
            "CAM_QA_DirectedWindows_v113",
            (0.0, -0.25, 2.25),
            (0.0, 2.60, 2.02),
            45.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v113-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v113-directed-light-overview.png"
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
    print("V113_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
