"""Replace surface bands with contained volumetric window rays and boost screen light."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v118-visible-rays-screen-glow.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v119-contained-window-rays.blend"),
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


def volumetric_material():
    name = "CATHODE_ContainedMoonrayVolume_v119"
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (0.62, 0.69, 0.82, 1.0)
    volume.inputs["Density"].default_value = 0.018
    volume.inputs["Anisotropy"].default_value = 0.42
    volume.inputs["Absorption Color"].default_value = (0.78, 0.84, 0.96, 1.0)
    volume.inputs["Emission Strength"].default_value = 0.72
    volume.inputs["Emission Color"].default_value = (0.54, 0.62, 0.78, 1.0)
    links.new(volume.outputs["Volume"], output.inputs["Volume"])
    return material


def beam_frame(direction):
    d = Vector(direction).normalized()
    side = Vector((1.0, 0.0, 0.0))
    side = (side - d * side.dot(d)).normalized()
    up = d.cross(side).normalized()
    return d, side, up


def create_tapered_volume(name, source, direction, length, start_width, end_width, start_height, end_height, material):
    d, side, up = beam_frame(direction)
    start = Vector(source)
    end = start + d * length

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
    ob["cathode_contained_window_ray_v119"] = True
    return ob, end


def build_window_rays():
    removed_bands = remove_prefixed("CATHODE_DeskBlindProjection_")
    removed_old_rays = remove_prefixed("CATHODE_WindowRayVolume_")
    material = volumetric_material()
    direction = Vector((0.65, -1.0, -0.48)).normalized()
    gap_z = (2.065, 2.120, 2.175, 2.230, 2.285, 2.340)
    created = []
    endpoints = []
    for window, x in ((1, -1.12), (2, 1.68)):
        for index, z in enumerate(gap_z):
            name = f"CATHODE_WindowRayVolume_W{window}_{index:02d}_v119"
            ray, end = create_tapered_volume(
                name,
                (x, 2.675, z),
                direction,
                1.34,
                0.43,
                0.56,
                0.012,
                0.040,
                material,
            )
            created.append(ray.name)
            endpoints.append([round(v, 4) for v in end])

    physical_gap_lights = []
    for ob in bpy.data.objects:
        if ob.name.startswith("LIGHT_WindowGapBand_") and ob.type == "LIGHT":
            ob.data.energy = 190.0
            ob.data.volume_factor = 1.0
            ob.data.color = (0.78, 0.84, 0.96)
            physical_gap_lights.append(ob.name)
    return {
        "removed_surface_bands": removed_bands,
        "removed_old_rays": removed_old_rays,
        "created": created,
        "ray_count": len(created),
        "direction": [round(v, 4) for v in direction],
        "endpoints": endpoints,
        "physical_gap_lights": physical_gap_lights,
        "containment": "local tapered volumes beginning at blind gaps",
    }


def limit_distance(data, distance):
    if hasattr(data, "use_custom_distance"):
        data.use_custom_distance = True
        data.cutoff_distance = distance


def boost_monitor_screen():
    material = bpy.data.materials.get("CATHODE_MONITOR_WHITE_EMISSION_v111")
    emission_strength = None
    if material is not None and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "EMISSION":
                node.inputs["Strength"].default_value = 1.90
                emission_strength = 1.90

    front = bpy.data.objects.get("LIGHT_MonitorWhite_v111")
    if front is not None and front.type == "LIGHT":
        front.data.energy = 175.0
        front.data.color = (0.88, 0.93, 1.0)
        front.data.diffuse_factor = 1.0
        front.data.specular_factor = 0.15
        front.data.volume_factor = 0.15
        limit_distance(front.data, 1.65)

    points = []
    for suffix in ("TL", "TR", "BL", "BR"):
        point = bpy.data.objects.get(f"LIGHT_MonitorScreenFace_{suffix}_v118")
        if point is not None and point.type == "LIGHT":
            point.data.energy = 34.0
            point.data.color = (0.86, 0.92, 1.0)
            point.data.shadow_soft_size = 0.15
            point.data.diffuse_factor = 1.0
            point.data.specular_factor = 0.10
            point.data.volume_factor = 0.0
            limit_distance(point.data, 0.68)
            points.append(point.name)
    return {
        "screen_emission_strength": emission_strength,
        "front_area_energy": front.data.energy if front else None,
        "screen_face_point_energy": 34.0,
        "screen_face_points": points,
        "rear_glow_remains_disabled": True,
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

    rays = build_window_rays()
    monitor = boost_monitor_screen()
    scene["cathode_contained_window_rays_v119"] = True
    scene["cathode_monitor_screen_boost_v119"] = True
    scene["cathode_restyle_version"] = "v119"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "window_rays": qa_camera(
            "CAM_QA_ContainedWindowRays_v119",
            (-2.75, -0.05, 2.36),
            (0.30, 2.18, 1.72),
            47.0,
        ),
        "monitor": qa_camera(
            "CAM_QA_MonitorIllumination_v119",
            (-1.55, 0.82, 1.75),
            (0.0, 2.30, 1.08),
            60.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v119-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v119-contained-rays-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "rays": rays,
        "monitor": monitor,
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V119_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
