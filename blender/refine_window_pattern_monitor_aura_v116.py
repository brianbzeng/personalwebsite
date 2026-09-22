"""Refine the visible blind pattern and monitor aura without moving room models."""

from pathlib import Path
import argparse
import json
import sys

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v115-visible-light-pattern.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v116-refined-rays-aura.blend"),
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
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
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


def create_plane_quad(name, corners, material, tag):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(corners, [], [(0, 1, 2, 3)])
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob[tag] = True
    return ob


def create_band(name, center, direction, perpendicular, length, width, material, tag):
    along = direction * (length * 0.5)
    across = perpendicular * (width * 0.5)
    corners = [
        center - along - across,
        center + along - across,
        center + along + across,
        center - along + across,
    ]
    return create_plane_quad(name, [tuple(corner) for corner in corners], material, tag)


def build_soft_desk_pattern():
    removed = remove_prefixed("CATHODE_DeskBlindProjection_")
    core_material = emission_material(
        "CATHODE_BlindProjection_Core_v116",
        (0.34, 0.38, 0.46),
        0.32,
    )
    feather_material = emission_material(
        "CATHODE_BlindProjection_Feather_v116",
        (0.20, 0.23, 0.29),
        0.11,
    )

    # The rear-left endpoint is the visually high side of the desk; the strips
    # travel down and to screen-right, matching the top-right window source.
    direction = Vector((0.90, -0.43, 0.0)).normalized()
    perpendicular = Vector((0.43, 0.90, 0.0)).normalized()
    center = Vector((-0.10, 1.92, 0.83145))
    length = 1.25
    offsets = (-0.060, -0.030, 0.0, 0.030, 0.060)
    created = []
    for index, offset in enumerate(offsets):
        band_center = center + perpendicular * offset
        feather_center = Vector((band_center.x, band_center.y, 0.83142))
        core_center = Vector((band_center.x, band_center.y, 0.83147))
        feather = create_band(
            f"CATHODE_DeskBlindProjection_Feather_{index:02d}_v116",
            feather_center,
            direction,
            perpendicular,
            length,
            0.038,
            feather_material,
            "cathode_soft_desk_pattern_v116",
        )
        core = create_band(
            f"CATHODE_DeskBlindProjection_Core_{index:02d}_v116",
            core_center,
            direction,
            perpendicular,
            length,
            0.012,
            core_material,
            "cathode_soft_desk_pattern_v116",
        )
        created.extend((feather.name, core.name))
    return {
        "removed": removed,
        "created": created,
        "band_count": len(offsets),
        "direction": "top_right_source_down_and_screen_right",
        "surface_z": center.z,
        "mousepad_top_z": 0.8305,
        "keyboard_bottom_z": 0.8325,
    }


def limit_distance(data, distance):
    if hasattr(data, "use_custom_distance"):
        data.use_custom_distance = True
        data.cutoff_distance = distance


def create_box(name, location, dimensions, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    ob["cathode_monitor_subtle_aura_rim_v116"] = True
    return ob


def refine_monitor_aura():
    removed = remove_prefixed("CATHODE_MonitorAura_")

    # Strengthen the real wall glow, then use only a very narrow neutral rim to
    # guarantee that the aura remains readable without becoming a solid panel.
    back = bpy.data.objects.get("LIGHT_MonitorAuraBack_v113")
    if back is not None and back.type == "LIGHT":
        back.data.energy = 235.0
        back.data.color = (0.78, 0.82, 0.91)
        limit_distance(back.data, 0.48)
    halo_points = []
    for suffix in ("TL", "TR", "BL", "BR"):
        light = bpy.data.objects.get(f"LIGHT_MonitorHalo_{suffix}_v114")
        if light is not None and light.type == "LIGHT":
            light.data.energy = 48.0
            light.data.color = (0.78, 0.82, 0.91)
            light.data.shadow_soft_size = 0.24
            limit_distance(light.data, 0.50)
            halo_points.append(light.name)

    aura_material = emission_material(
        "CATHODE_MonitorAura_SubtleEmission_v116",
        (0.34, 0.37, 0.43),
        0.34,
    )
    y = 2.568
    depth = 0.006
    parts = [
        create_box("CATHODE_MonitorAura_Top_v116", (0.0, y, 1.4625), (1.41, depth, 0.025), aura_material),
        create_box("CATHODE_MonitorAura_Bottom_v116", (0.0, y, 0.8575), (1.41, depth, 0.025), aura_material),
        create_box("CATHODE_MonitorAura_Left_v116", (-0.6925, y, 1.16), (0.025, depth, 0.58), aura_material),
        create_box("CATHODE_MonitorAura_Right_v116", (0.6925, y, 1.16), (0.025, depth, 0.58), aura_material),
    ]
    return {
        "removed": removed,
        "backlight": back.name if back else None,
        "backlight_energy": back.data.energy if back else None,
        "halo_points": halo_points,
        "rim_parts": [part.name for part in parts],
        "style": "narrow_neutral_rim_plus_soft_wall_glow",
    }


def aim(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


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

    pattern = build_soft_desk_pattern()
    aura = refine_monitor_aura()
    scene["cathode_soft_desk_pattern_v116"] = True
    scene["cathode_monitor_aura_v116"] = True
    scene["cathode_restyle_version"] = "v116"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "desk_pattern": qa_camera(
            "CAM_QA_SoftDeskPattern_v116",
            (-2.45, -0.15, 2.82),
            (-0.18, 1.92, 0.87),
            48.0,
        ),
        "monitor_aura": qa_camera(
            "CAM_QA_SubtleMonitorAura_v116",
            (-1.55, 0.82, 1.75),
            (0.0, 2.50, 1.18),
            60.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v116-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v116-refined-light-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "pattern": pattern,
        "aura": aura,
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V116_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
