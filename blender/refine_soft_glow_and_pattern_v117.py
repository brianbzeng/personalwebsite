"""Final visual refinement for down-right desk bands and a fading monitor aura."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v116-refined-rays-aura.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v117-soft-downright-light.blend"),
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
        "cathode_downright_desk_pattern_v117",
    )


def rebuild_desk_pattern():
    removed = remove_prefixed("CATHODE_DeskBlindProjection_")
    core_material = emission_material(
        "CATHODE_BlindProjection_NeutralCore_v117",
        (0.58, 0.61, 0.67),
        0.50,
    )
    feather_material = emission_material(
        "CATHODE_BlindProjection_NeutralFeather_v117",
        (0.36, 0.39, 0.44),
        0.18,
    )

    # This world-space angle projects as upper-left to lower-right in the desk
    # review camera, so the visible streaks travel visually down and right.
    angle = math.radians(120.0)
    direction = Vector((math.cos(angle), math.sin(angle), 0.0)).normalized()
    perpendicular = Vector((-direction.y, direction.x, 0.0)).normalized()
    center = Vector((0.18, 1.92, 0.83145))
    length = 0.62
    offsets = (-0.060, -0.030, 0.0, 0.030, 0.060)
    created = []
    for index, offset in enumerate(offsets):
        band_center = center + perpendicular * offset
        feather = create_band(
            f"CATHODE_DeskBlindProjection_Feather_{index:02d}_v117",
            Vector((band_center.x, band_center.y, 0.83142)),
            direction,
            perpendicular,
            length,
            0.040,
            feather_material,
        )
        core = create_band(
            f"CATHODE_DeskBlindProjection_Core_{index:02d}_v117",
            Vector((band_center.x, band_center.y, 0.83147)),
            direction,
            perpendicular,
            length,
            0.012,
            core_material,
        )
        created.extend((feather.name, core.name))
    return {
        "removed": removed,
        "created": created,
        "band_count": len(offsets),
        "visual_direction": "upper_left_to_lower_right",
        "source_intent": "top_right_window_light_focused_down_and_right",
    }


def soft_aura_material():
    material = bpy.data.materials.get("CATHODE_MonitorAura_SoftFade_v117")
    if material is None:
        material = bpy.data.materials.new("CATHODE_MonitorAura_SoftFade_v117")
    material.use_nodes = True
    material.diffuse_color = (0.30, 0.33, 0.40, 0.0)
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.38, 0.41, 0.48, 1.0)
    emission.inputs["Strength"].default_value = 0.85

    texcoord = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    x_sub = nodes.new("ShaderNodeMath")
    x_sub.operation = "SUBTRACT"
    x_sub.inputs[1].default_value = 0.5
    x_abs = nodes.new("ShaderNodeMath")
    x_abs.operation = "ABSOLUTE"
    x_scale = nodes.new("ShaderNodeMath")
    x_scale.operation = "MULTIPLY"
    x_scale.inputs[1].default_value = 2.0
    z_sub = nodes.new("ShaderNodeMath")
    z_sub.operation = "SUBTRACT"
    z_sub.inputs[1].default_value = 0.5
    z_abs = nodes.new("ShaderNodeMath")
    z_abs.operation = "ABSOLUTE"
    z_scale = nodes.new("ShaderNodeMath")
    z_scale.operation = "MULTIPLY"
    z_scale.inputs[1].default_value = 2.0
    maximum = nodes.new("ShaderNodeMath")
    maximum.operation = "MAXIMUM"
    fade = nodes.new("ShaderNodeMapRange")
    fade.clamp = True
    fade.interpolation_type = "SMOOTHERSTEP"
    fade.inputs["From Min"].default_value = 0.66
    fade.inputs["From Max"].default_value = 1.0
    fade.inputs["To Min"].default_value = 1.0
    fade.inputs["To Max"].default_value = 0.0

    links.new(texcoord.outputs["Generated"], separate.inputs["Vector"])
    links.new(separate.outputs["X"], x_sub.inputs[0])
    links.new(x_sub.outputs[0], x_abs.inputs[0])
    links.new(x_abs.outputs[0], x_scale.inputs[0])
    links.new(separate.outputs["Z"], z_sub.inputs[0])
    links.new(z_sub.outputs[0], z_abs.inputs[0])
    links.new(z_abs.outputs[0], z_scale.inputs[0])
    links.new(x_scale.outputs[0], maximum.inputs[0])
    links.new(z_scale.outputs[0], maximum.inputs[1])
    links.new(maximum.outputs[0], fade.inputs["Value"])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    links.new(fade.outputs["Result"], mix.inputs[0])
    links.new(mix.outputs[0], output.inputs["Surface"])
    return material


def rebuild_monitor_aura():
    removed = remove_prefixed("CATHODE_MonitorAura_")
    material = soft_aura_material()
    x0, x1 = -0.82, 0.82
    y = 2.568
    z0, z1 = 0.76, 1.56
    aura = create_quad(
        "CATHODE_MonitorAura_SoftPlane_v117",
        [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)],
        material,
        "cathode_monitor_soft_aura_v117",
    )
    return {
        "removed": removed,
        "created": aura.name,
        "style": "transparent_fading_neutral_backglow",
        "behind_monitor_y": y,
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

    pattern = rebuild_desk_pattern()
    aura = rebuild_monitor_aura()
    scene["cathode_soft_downright_pattern_v117"] = True
    scene["cathode_monitor_soft_aura_v117"] = True
    scene["cathode_restyle_version"] = "v117"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "desk_pattern": qa_camera(
            "CAM_QA_DownRightDeskPattern_v117",
            (-2.45, -0.15, 2.82),
            (-0.12, 1.92, 0.87),
            48.0,
        ),
        "monitor_aura": qa_camera(
            "CAM_QA_SoftMonitorAura_v117",
            (-1.55, 0.82, 1.75),
            (0.0, 2.50, 1.18),
            60.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v117-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v117-soft-downright-overview.png"
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
    print("V117_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
