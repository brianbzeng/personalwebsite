"""Expand moonlight across both complete windows and fade every ray smoothly."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v119-contained-window-rays.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v120-full-window-faded-rays.blend"),
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


def faded_volume_material(name, direction, length, density, emission_strength):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (0.64, 0.71, 0.84, 1.0)
    volume.inputs["Anisotropy"].default_value = 0.48
    volume.inputs["Absorption Color"].default_value = (0.82, 0.87, 0.98, 1.0)
    volume.inputs["Emission Color"].default_value = (0.55, 0.64, 0.80, 1.0)

    texcoord = nodes.new("ShaderNodeTexCoord")
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = tuple(Vector(direction).normalized())
    divide = nodes.new("ShaderNodeMath")
    divide.operation = "DIVIDE"
    divide.inputs[1].default_value = length
    fade = nodes.new("ShaderNodeMapRange")
    fade.clamp = True
    fade.interpolation_type = "SMOOTHERSTEP"
    fade.inputs["From Min"].default_value = 0.34
    fade.inputs["From Max"].default_value = 1.0
    fade.inputs["To Min"].default_value = 1.0
    fade.inputs["To Max"].default_value = 0.0
    density_mult = nodes.new("ShaderNodeMath")
    density_mult.operation = "MULTIPLY"
    density_mult.inputs[1].default_value = density
    emission_mult = nodes.new("ShaderNodeMath")
    emission_mult.operation = "MULTIPLY"
    emission_mult.inputs[1].default_value = emission_strength

    links.new(texcoord.outputs["Object"], dot.inputs[0])
    links.new(dot.outputs["Value"], divide.inputs[0])
    links.new(divide.outputs[0], fade.inputs["Value"])
    links.new(fade.outputs["Result"], density_mult.inputs[0])
    links.new(fade.outputs["Result"], emission_mult.inputs[0])
    links.new(density_mult.outputs[0], volume.inputs["Density"])
    links.new(emission_mult.outputs[0], volume.inputs["Emission Strength"])
    links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return material


def beam_frame(direction):
    d = Vector(direction).normalized()
    side = Vector((1.0, 0.0, 0.0))
    side = (side - d * side.dot(d)).normalized()
    up = d.cross(side).normalized()
    return d, side, up


def create_tapered_volume(name, source, direction, length, start_width, end_width, start_height, end_height, material, tag):
    d, side, up = beam_frame(direction)
    start = Vector((0.0, 0.0, 0.0))
    end = d * length
    vertices = []
    for center, width, height in (
        (start, start_width, start_height),
        (end, end_width, end_height),
    ):
        half_side = side * (width * 0.5)
        half_up = up * (height * 0.5)
        vertices.extend([
            center - half_side - half_up,
            center + half_side - half_up,
            center + half_side + half_up,
            center - half_side + half_up,
        ])
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = source
    ob[tag] = True
    return ob, Vector(source) + end


def lighting_collection():
    collection = bpy.data.collections.get("LIGHTING")
    if collection is None:
        collection = bpy.data.collections.new("LIGHTING")
        bpy.context.scene.collection.children.link(collection)
    return collection


def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def limit_distance(data, distance):
    if hasattr(data, "use_custom_distance"):
        data.use_custom_distance = True
        data.cutoff_distance = distance


def create_area_light(name, location, direction, size, size_y, energy, cutoff):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.lights.new(name + "_Data", "AREA")
    ob = bpy.data.objects.new(name, data)
    lighting_collection().objects.link(ob)
    ob.location = location
    aim(ob, Vector(location) + Vector(direction))
    data.energy = energy
    data.color = (0.80, 0.86, 1.0)
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size_y
    data.spread = math.radians(18.0)
    data.diffuse_factor = 1.0
    data.specular_factor = 0.06
    data.volume_factor = 1.0
    data.use_shadow = True
    limit_distance(data, cutoff)
    ob["cathode_full_window_ray_light_v120"] = True
    return ob


def rebuild_full_window_rays():
    removed_volumes = remove_prefixed("CATHODE_WindowRayVolume_")
    removed_lights = remove_prefixed("LIGHT_WindowGapBand_")
    removed_lower = remove_prefixed("LIGHT_WindowLowerPane_")

    direction = Vector((0.65, -1.0, -0.48)).normalized()
    length = 1.48
    blind_material = faded_volume_material(
        "CATHODE_BlindRay_FadedVolume_v120",
        direction,
        length,
        density=0.015,
        emission_strength=0.62,
    )
    lower_material = faded_volume_material(
        "CATHODE_LowerPaneRay_FadedVolume_v120",
        direction,
        length,
        density=0.010,
        emission_strength=0.34,
    )

    gap_z = tuple(1.9875 + 0.055 * index for index in range(10))
    created_blinds = []
    created_lower = []
    lights = []
    endpoints = []
    for window, x in ((1, -1.40), (2, 1.40)):
        for index, z in enumerate(gap_z):
            name = f"CATHODE_WindowRayVolume_W{window}_Blind_{index:02d}_v120"
            ray, end = create_tapered_volume(
                name,
                (x, 2.675, z),
                direction,
                length,
                1.18,
                1.30,
                0.012,
                0.036,
                blind_material,
                "cathode_full_blind_ray_v120",
            )
            created_blinds.append(ray.name)
            endpoints.append([round(v, 4) for v in end])
            lights.append(create_area_light(
                f"LIGHT_WindowGapBand_W{window}_{index:02d}_v120",
                (x, 2.69, z),
                direction,
                1.16,
                0.012,
                105.0,
                1.60,
            ).name)

        lower_name = f"CATHODE_WindowRayVolume_W{window}_LowerPane_v120"
        lower, end = create_tapered_volume(
            lower_name,
            (x, 2.675, 1.43),
            direction,
            length,
            1.18,
            1.34,
            0.84,
            0.98,
            lower_material,
            "cathode_lower_pane_ray_v120",
        )
        created_lower.append(lower.name)
        endpoints.append([round(v, 4) for v in end])
        lights.append(create_area_light(
            f"LIGHT_WindowLowerPane_W{window}_v120",
            (x, 2.69, 1.43),
            direction,
            1.16,
            0.82,
            52.0,
            1.65,
        ).name)

    return {
        "removed_volumes": removed_volumes,
        "removed_gap_lights": removed_lights,
        "removed_lower_lights": removed_lower,
        "blind_rays": created_blinds,
        "lower_pane_rays": created_lower,
        "light_sources": lights,
        "blind_ray_count": len(created_blinds),
        "lower_pane_ray_count": len(created_lower),
        "window_centers": [-1.40, 1.40],
        "gap_z": [round(z, 4) for z in gap_z],
        "direction": [round(v, 4) for v in direction],
        "fade": "smootherstep density and emission from 34% to 100% of ray length",
        "endpoints": endpoints,
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

    rays = rebuild_full_window_rays()
    scene["cathode_full_window_faded_rays_v120"] = True
    scene["cathode_restyle_version"] = "v120"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "full_windows": qa_camera(
            "CAM_QA_FullWindowRays_v120",
            (-2.65, -0.20, 2.44),
            (0.0, 2.18, 1.72),
            46.0,
        ),
        "ray_taper": qa_camera(
            "CAM_QA_RayTaper_v120",
            (-2.75, 0.72, 2.15),
            (0.25, 1.95, 1.56),
            52.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v120-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v120-full-window-rays-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "rays": rays,
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V120_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
