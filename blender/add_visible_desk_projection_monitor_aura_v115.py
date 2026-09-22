"""Add visible blind-band projection on the desk and a monitor aura rim."""

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
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v114-blind-gap-patterns.blend"),
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "outputs" / "blender" / "lofi-room-cathode-v115-visible-light-pattern.blend"),
    )
    parser.add_argument("--render-dir", default=str(HERE / "outputs" / "blender"))
    return parser.parse_args(argv)


def remove_object(name):
    ob = bpy.data.objects.get(name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)


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


def create_plane_quad(name, corners, material):
    remove_object(name)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(corners, [], [(0, 1, 2, 3)])
    mesh.materials.append(material)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    ob["cathode_projected_light_surface_v115"] = True
    return ob


def build_desk_projection():
    material = emission_material(
        "CATHODE_BlindProjection_Emission_v115",
        (0.40, 0.48, 0.62),
        0.72,
    )
    center = Vector((-0.10, 1.93, 0.83145))
    direction = Vector((0.753, -0.658, 0.0)).normalized()
    perpendicular = Vector((0.658, 0.753, 0.0)).normalized()
    length = 0.70
    width = 0.013
    offsets = (-0.09, -0.06, -0.03, 0.0, 0.03, 0.06, 0.09)
    bands = []
    for index, offset in enumerate(offsets):
        band_center = center + perpendicular * offset
        along = direction * (length * 0.5)
        across = perpendicular * (width * 0.5)
        corners = [
            band_center - along - across,
            band_center + along - across,
            band_center + along + across,
            band_center - along + across,
        ]
        name = f"CATHODE_DeskBlindProjection_{index:02d}_v115"
        ob = create_plane_quad(name, [tuple(corner) for corner in corners], material)
        bands.append(ob.name)
    return {
        "bands": bands,
        "count": len(bands),
        "direction": "top_left_to_bottom_right_on_desk",
        "surface_z": center.z,
        "mousepad_top_z": 0.8305,
        "keyboard_bottom_z": 0.8325,
        "clear_above_mousepad": center.z - 0.8305,
        "clear_below_keyboard": 0.8325 - center.z,
    }


def create_box(name, location, dimensions, material):
    remove_object(name)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    ob["cathode_monitor_visible_aura_rim_v115"] = True
    return ob


def build_monitor_aura_rim():
    material = emission_material(
        "CATHODE_MonitorAura_Emission_v115",
        (0.32, 0.39, 0.56),
        0.90,
    )
    y = 2.568
    depth = 0.010
    parts = [
        create_box("CATHODE_MonitorAura_Top_v115", (0.0, y, 1.485), (1.52, depth, 0.070), material),
        create_box("CATHODE_MonitorAura_Bottom_v115", (0.0, y, 0.835), (1.52, depth, 0.070), material),
        create_box("CATHODE_MonitorAura_Left_v115", (-0.725, y, 1.16), (0.070, depth, 0.650), material),
        create_box("CATHODE_MonitorAura_Right_v115", (0.725, y, 1.16), (0.070, depth, 0.650), material),
    ]
    return {
        "parts": [part.name for part in parts],
        "behind_monitor_y": y,
        "monitor_front_y": 2.43,
        "monitor_back_y": 2.555,
        "status": "visible_rim_behind_casing",
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

    projection = build_desk_projection()
    aura = build_monitor_aura_rim()
    scene["cathode_visible_desk_projection_v115"] = True
    scene["cathode_monitor_aura_rim_v115"] = True
    scene["cathode_restyle_version"] = "v115"
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    cameras = {
        "desk_pattern": qa_camera(
            "CAM_QA_VisibleDeskPattern_v115",
            (-2.45, -0.15, 2.82),
            (-0.20, 1.94, 0.87),
            48.0,
        ),
        "monitor_aura": qa_camera(
            "CAM_QA_VisibleMonitorAura_v115",
            (-1.55, 0.82, 1.75),
            (0.0, 2.50, 1.18),
            60.0,
        ),
    }
    renders = {}
    for label, camera in cameras.items():
        path = render_dir / f"lofi-room-cathode-v115-{label}-closeup.png"
        render(scene, camera, path, (1100, 760))
        renders[label] = str(path)
    if original_camera is not None:
        overview = render_dir / "lofi-room-cathode-v115-light-pattern-overview.png"
        render(scene, original_camera, overview, (1280, 720))
        renders["overview"] = str(overview)
        scene.camera = original_camera
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))

    report = {
        "source": str(input_path),
        "output": str(output_path),
        "projection": projection,
        "aura": aura,
        "renders": renders,
    }
    output_path.with_name(output_path.stem + "-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("V115_REPORT=" + json.dumps(report))


if __name__ == "__main__":
    main()
