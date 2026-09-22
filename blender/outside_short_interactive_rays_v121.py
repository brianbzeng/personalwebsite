"""Move moon rays outside, soften/shorten them, and add a lightning controller."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v120-full-window-faded-rays.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v121-outside-short-interactive-rays.blend"),
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


def lightning_controller():
    name = "CTRL_LightningSync"
    ctrl = bpy.data.objects.get(name)
    if ctrl is None:
        ctrl = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(ctrl)
    ctrl.empty_display_type = "PLAIN_AXES"
    ctrl.empty_display_size = 0.22
    ctrl.location = (0.0, 2.95, 3.05)
    ctrl.hide_render = True
    ctrl["lightning_strength"] = 1.0
    ctrl["cathode_lightning_ready_v121"] = True
    ui = ctrl.id_properties_ui("lightning_strength")
    ui.update(
        min=0.0,
        max=8.0,
        soft_min=0.0,
        soft_max=5.0,
        description="Keyframe this value to synchronize the window rays with lightning flashes.",
    )
    return ctrl


def add_controller_driver(target, data_path, controller, base_value):
    try:
        target.driver_remove(data_path)
    except (TypeError, RuntimeError):
        pass
    curve = target.driver_add(data_path)
    driver = curve.driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = "flash"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = controller
    variable.targets[0].data_path = '["lightning_strength"]'
    driver.expression = f"{base_value:.8f} * flash"
    return driver.expression


def faded_volume_material(name, direction, length, density, emission_strength, controller):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (0.61, 0.68, 0.80, 1.0)
    volume.inputs["Anisotropy"].default_value = 0.44
    volume.inputs["Absorption Color"].default_value = (0.84, 0.89, 1.0, 1.0)
    volume.inputs["Emission Color"].default_value = (0.52, 0.60, 0.74, 1.0)

    texcoord = nodes.new("ShaderNodeTexCoord")
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = tuple(Vector(direction).normalized())
    divide = nodes.new("ShaderNodeMath")
    divide.operation = "DIVIDE"
    divide.inputs[1].default_value = length
    fade = nodes.new("ShaderNodeMapRange")
    fade.name = "CATHODE_FadeImmediatelyInside"
    fade.clamp = True
    fade.interpolation_type = "SMOOTHERSTEP"
    # The exterior source reaches the blind plane at about 36% of the ray.
    fade.inputs["From Min"].default_value = 0.36
    fade.inputs["From Max"].default_value = 1.0
    fade.inputs["To Min"].default_value = 1.0
    fade.inputs["To Max"].default_value = 0.0
    density_mult = nodes.new("ShaderNodeMath")
    density_mult.name = "CATHODE_RayDensityBase"
    density_mult.operation = "MULTIPLY"
    density_mult.inputs[1].default_value = density
    emission_mult = nodes.new("ShaderNodeMath")
    emission_mult.name = "CATHODE_RayEmissionLightningDriven"
    emission_mult.operation = "MULTIPLY"
    emission_mult.inputs[1].default_value = emission_strength
    emission_driver = add_controller_driver(
        emission_mult.inputs[1], "default_value", controller, emission_strength
    )

    links.new(texcoord.outputs["Object"], dot.inputs[0])
    links.new(dot.outputs["Value"], divide.inputs[0])
    links.new(divide.outputs[0], fade.inputs["Value"])
    links.new(fade.outputs["Result"], density_mult.inputs[0])
    links.new(fade.outputs["Result"], emission_mult.inputs[0])
    links.new(density_mult.outputs[0], volume.inputs["Density"])
    links.new(emission_mult.outputs[0], volume.inputs["Emission Strength"])
    links.new(volume.outputs["Volume"], output.inputs["Volume"])
    material["cathode_lightning_driver_expression"] = emission_driver
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


def create_driven_area_light(name, location, direction, size, size_y, energy, cutoff, controller):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    data = bpy.data.lights.new(name + "_Data", "AREA")
    ob = bpy.data.objects.new(name, data)
    lighting_collection().objects.link(ob)
    ob.location = location
    aim(ob, Vector(location) + Vector(direction))
    data.energy = energy
    data.color = (0.78, 0.84, 0.96)
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size_y
    data.spread = math.radians(15.0)
    data.diffuse_factor = 1.0
    data.specular_factor = 0.05
    data.volume_factor = 1.0
    data.use_shadow = True
    limit_distance(data, cutoff)
    expression = add_controller_driver(data, "energy", controller, energy)
    ob["cathode_lightning_driven_v121"] = True
    ob["cathode_lightning_driver_expression"] = expression
    return ob


def rebuild_outside_short_rays(controller):
    removed_volumes = remove_prefixed("CATHODE_WindowRayVolume_")
    removed_gap_lights = remove_prefixed("LIGHT_WindowGapBand_")
    removed_lower_lights = remove_prefixed("LIGHT_WindowLowerPane_")

    direction = Vector((0.65, -1.0, -0.48)).normalized()
    length = 0.95
    exterior_y = 2.88
    blind_material = faded_volume_material(
        "CATHODE_BlindRay_OutsideShort_v121",
        direction,
        length,
        density=0.0060,
        emission_strength=0.18,
        controller=controller,
    )
    lower_material = faded_volume_material(
        "CATHODE_LowerRay_OutsideShort_v121",
        direction,
        length,
        density=0.0040,
        emission_strength=0.095,
        controller=controller,
    )
    gap_z = tuple(1.9875 + 0.055 * index for index in range(10))
    blind_rays = []
    lower_rays = []
    lights = []
    endpoints = []
    for window, x in ((1, -1.40), (2, 1.40)):
        for index, z in enumerate(gap_z):
            name = f"CATHODE_WindowRayVolume_W{window}_Blind_{index:02d}_v121"
            ray, end = create_tapered_volume(
                name,
                (x, exterior_y, z),
                direction,
                length,
                1.16,
                1.22,
                0.010,
                0.026,
                blind_material,
                "cathode_outside_short_blind_ray_v121",
            )
            blind_rays.append(ray.name)
            endpoints.append([round(v, 4) for v in end])
            lights.append(create_driven_area_light(
                f"LIGHT_WindowGapBand_W{window}_{index:02d}_v121",
                (x, 2.90, z),
                direction,
                1.14,
                0.010,
                34.0,
                1.02,
                controller,
            ).name)

        name = f"CATHODE_WindowRayVolume_W{window}_LowerPane_v121"
        lower, end = create_tapered_volume(
            name,
            (x, exterior_y, 1.43),
            direction,
            length,
            1.16,
            1.24,
            0.82,
            0.88,
            lower_material,
            "cathode_outside_short_lower_ray_v121",
        )
        lower_rays.append(lower.name)
        endpoints.append([round(v, 4) for v in end])
        lights.append(create_driven_area_light(
            f"LIGHT_WindowLowerPane_W{window}_v121",
            (x, 2.90, 1.43),
            direction,
            1.14,
            0.80,
            16.0,
            1.05,
            controller,
        ).name)

    return {
        "removed_volumes": removed_volumes,
        "removed_gap_lights": removed_gap_lights,
        "removed_lower_lights": removed_lower_lights,
        "blind_rays": blind_rays,
        "lower_pane_rays": lower_rays,
        "lights": lights,
        "exterior_source_y": exterior_y,
        "blind_plane_y": 2.60,
        "ray_length": length,
        "direction": [round(v, 4) for v in direction],
        "fade_begins_normalized": 0.36,
        "fade_begins_at_blinds": True,
        "endpoints": endpoints,
        "controller": controller.name,
        "controller_property": "lightning_strength",
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

    controller = lightning_controller()
    rays = rebuild_outside_short_rays(controller)
    scene["cathode_outside_short_interactive_rays_v121"] = True
    scene["cathode_lightning_controller"] = controller.name
    scene["cathode_restyle_version"] = "v121"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "outside_origin": qa_camera(
            "CAM_QA_OutsideOriginRays_v121",
            (-2.62, -0.12, 2.42),
            (0.0, 2.46, 1.74),
            47.0,
        ),
        "short_fade": qa_camera(
            "CAM_QA_ShortRayFade_v121",
            (-2.70, 0.85, 2.17),
            (0.30, 2.35, 1.58),
            54.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v121-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v121-outside-short-rays-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "rays": rays,
        "controller": {
            "name": controller.name,
            "property": "lightning_strength",
            "default": controller["lightning_strength"],
            "range": [0.0, 8.0],
            "usage": "Keyframe one property to drive every ray light and volumetric emission.",
        },
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V121_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
