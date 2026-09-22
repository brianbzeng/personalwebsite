"""Constrain the moonlight to the windows and soften the monitor glow."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v111-white-moonlight.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v112-soft-window-glow.blend"),
    )
    parser.add_argument("--render-dir", default=str(HERE / "outputs" / "blender"))
    return parser.parse_args(argv)


def remove_object(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return False
    data = ob.data if hasattr(ob, "data") else None
    bpy.data.objects.remove(ob, do_unlink=True)
    if data is not None and getattr(data, "users", 1) == 0:
        if isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
        elif isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
    return True


def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def configure_window_light(name, x):
    light = bpy.data.objects.get(name)
    if light is None or light.type != "LIGHT":
        raise RuntimeError(f"Missing window light: {name}")
    light.data.type = "AREA"
    light.location = (x, 2.785, 2.10)
    aim(light, (x, 1.55, 1.50))
    light.data.energy = 112.0
    light.data.color = (0.76, 0.82, 0.96)
    light.data.shape = "RECTANGLE"
    light.data.size = 0.96
    light.data.size_y = 1.02
    light.data.spread = math.radians(46.0)
    light.data.use_shadow = True
    light.data.diffuse_factor = 1.0
    light.data.specular_factor = 0.20
    light.data.volume_factor = 0.0
    if hasattr(light.data, "use_custom_distance"):
        light.data.use_custom_distance = True
        light.data.cutoff_distance = 1.55
    light["cathode_window_only_soft_glow_v112"] = True
    return {
        "name": light.name,
        "location": [round(value, 5) for value in light.location],
        "energy": light.data.energy,
        "spread_degrees": 46.0,
        "cutoff_distance": light.data.cutoff_distance,
        "size": [light.data.size, light.data.size_y],
    }


def tone_down_monitor():
    material = bpy.data.materials.get("CATHODE_MONITOR_WHITE_EMISSION_v111")
    if material is None or not material.use_nodes:
        raise RuntimeError("Monitor emission material missing")
    emission_nodes = [node for node in material.node_tree.nodes if node.type == "EMISSION"]
    if not emission_nodes:
        raise RuntimeError("Monitor emission node missing")
    for node in emission_nodes:
        node.inputs["Strength"].default_value = 1.35
        node.inputs["Color"].default_value = (0.86, 0.90, 0.98, 1.0)

    light = bpy.data.objects.get("LIGHT_MonitorWhite_v111")
    if light is None or light.type != "LIGHT":
        raise RuntimeError("Monitor fill light missing")
    light.data.energy = 82.0
    light.data.color = (0.88, 0.92, 1.0)
    light.data.spread = math.radians(92.0)
    light.data.specular_factor = 0.25
    light.data.volume_factor = 0.0
    if hasattr(light.data, "use_custom_distance"):
        light.data.use_custom_distance = True
        light.data.cutoff_distance = 1.35
    return {
        "material": material.name,
        "emission_strength": 1.35,
        "light": light.name,
        "light_energy": light.data.energy,
        "light_cutoff": light.data.cutoff_distance,
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

    removed = [
        name
        for name in (
            "LIGHT_MoonRays_Window1_v111",
            "LIGHT_MoonRays_Window2_v111",
            "LIGHT_MoonDirectional_v111",
            "VOLUME_MoonlightHaze_v111",
        )
        if remove_object(name)
    ]
    windows = [
        configure_window_light("LIGHT_WindowWest", -1.4),
        configure_window_light("LIGHT_WindowEast", 1.4),
    ]
    monitor = tone_down_monitor()
    scene["cathode_soft_window_only_glow_v112"] = True
    scene["cathode_restyle_version"] = "v112"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "windows": qa_camera(
            "CAM_QA_WindowOnlySoftGlow_v112",
            (0.0, -0.30, 2.05),
            (0.0, 2.60, 1.95),
            45.0,
        ),
        "desk": qa_camera(
            "CAM_QA_TonedMonitor_v112",
            (-2.45, -0.95, 2.35),
            (0.0, 2.08, 1.08),
            50.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v112-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v112-soft-light-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    residual = [
        name
        for name in (
            "LIGHT_MoonRays_Window1_v111",
            "LIGHT_MoonRays_Window2_v111",
            "LIGHT_MoonDirectional_v111",
            "VOLUME_MoonlightHaze_v111",
        )
        if bpy.data.objects.get(name) is not None
    ]
    if residual:
        raise RuntimeError(f"Long-range lighting helpers remain: {residual}")
    report = {
        "source": str(input_path),
        "output": str(output_path),
        "removed_long_range_helpers": removed,
        "window_lights": windows,
        "monitor": monitor,
        "residual_long_range_helpers": residual,
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V112_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
