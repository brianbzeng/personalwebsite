import importlib.util
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(r"C:\Users\Brian Zeng\Documents\Codex\2026-08-07\c-users-brian-zeng-documents-codex-3")
SOURCE = ROOT / "outputs" / "blender" / "lofi-room-rebuild-v06-rainy-neighborhood.blend"
OUT = ROOT / "outputs" / "blender" / "lofi-room-rebuild-v08-rainy-suburb.blend"
HERO = ROOT / "outputs" / "blender" / "rebuild-v08-rainy-suburb-hero.png"
NORMAL = ROOT / "outputs" / "blender" / "rebuild-v08-rainy-suburb-normal.png"
LIGHTNING = ROOT / "outputs" / "blender" / "rebuild-v08-rainy-suburb-lightning.png"
LEFT_WINDOW = ROOT / "outputs" / "blender" / "rebuild-v08-left-window.png"
RIGHT_WINDOW = ROOT / "outputs" / "blender" / "rebuild-v08-right-window.png"
REPORT = ROOT / "outputs" / "blender" / "rebuild-v08-rainy-suburb-report.json"
HELPERS = ROOT / "work" / "create_gardener_style_test.py"
FPS = 24
FULL_END = 240


def load_helpers():
    spec = importlib.util.spec_from_file_location("gardener_helpers_v07", HELPERS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_helpers()


def material(name, color, roughness=0.78, emission=None, emission_strength=0.0):
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.roughness = roughness
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission is not None:
        socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if socket:
            socket.default_value = (*emission, 1.0)
        strength = bsdf.inputs.get("Emission Strength")
        if strength:
            strength.default_value = emission_strength
    return mat


def remove_v06_exterior():
    for obj in list(bpy.data.objects):
        if obj.name.startswith(("NEIGHBOR_", "SUBURB_")) or obj.name.startswith("CAM_QA_Suburb"):
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.name in {"NEIGHBORHOOD_RAIN_V06", "RAINY_SUBURB_V07"}:
            bpy.data.collections.remove(collection)


def collection():
    coll = bpy.data.collections.new("RAINY_SUBURB_V07")
    bpy.context.scene.collection.children.link(coll)
    return coll


def relocate_new(before, coll):
    for obj in list(set(bpy.data.objects) - before):
        if coll not in obj.users_collection:
            coll.objects.link(obj)
        for old in list(obj.users_collection):
            if old != coll:
                old.objects.unlink(obj)


def mesh_object(name, vertices, faces, mat, coll):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    H.finish_mesh(obj, mat, True)
    return obj


def gable_roof(name, cx, front_y, width, depth, eave_z, ridge_z, mat, coll):
    x0, x1 = cx - width * 0.5, cx + width * 0.5
    y0, y1 = front_y - 0.14, front_y + depth
    verts = [
        (x0 - 0.12, y0, eave_z), (x1 + 0.12, y0, eave_z), (cx, y0, ridge_z),
        (x0 - 0.12, y1, eave_z), (x1 + 0.12, y1, eave_z), (cx, y1, ridge_z),
    ]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (0, 2, 5, 3), (2, 1, 4, 5)]
    return mesh_object(name, verts, faces, mat, coll)


def window(name, x, y, z, width, height, lit, mats):
    panel = mats["window_lit"] if lit else mats["window_dark"]
    H.xy_cut_box(name + "_Panel", (x, y - 0.032, z), width, 0.028, height, 0.035, panel)
    frame = 0.045
    H.cohesive_box_assembly(name + "_Frame", [
        ((x - width * 0.5 - frame * 0.5, y - 0.052, z), (frame, 0.03, height + frame * 2)),
        ((x + width * 0.5 + frame * 0.5, y - 0.052, z), (frame, 0.03, height + frame * 2)),
        ((x, y - 0.052, z - height * 0.5 - frame * 0.5), (width, 0.03, frame)),
        ((x, y - 0.052, z + height * 0.5 + frame * 0.5), (width, 0.03, frame)),
        ((x, y - 0.055, z), (frame * 0.55, 0.03, height)),
        ((x, y - 0.055, z), (width, 0.03, frame * 0.55)),
    ], mats["trim"])
    return frame


def suburban_house(index, cx, front_y, width, depth, base_z, wall_h, mats, coll, variant):
    prefix = f"SUBURB_House_{index:02d}"
    # One broad, coherent main mass per window, plus an inset garage/porch wing.
    H.box(prefix + "_Body", (cx, front_y + depth * 0.5, base_z + wall_h * 0.5), (width, depth, wall_h), mats[f"wall_{variant}"])
    eave = base_z + wall_h
    ridge = eave + 0.58
    gable_roof(prefix + "_Roof", cx, front_y, width, depth, eave, ridge, mats[f"roof_{variant}"], coll)

    if index == 0:
        garage_x = cx - width * 0.28
        entry_x = cx + width * 0.29
        garage_w = width * 0.38
    else:
        garage_x = cx + width * 0.27
        entry_x = cx - width * 0.31
        garage_w = width * 0.42

    # Paneled garage door and shallow driveway establish suburban scale.
    H.xy_cut_box(prefix + "_GarageDoor", (garage_x, front_y - 0.035, base_z + 0.38), garage_w, 0.03, 0.65, 0.045, mats["garage"])
    for row in range(3):
        H.box(prefix + f"_GaragePanel_{row}", (garage_x, front_y - 0.055, base_z + 0.18 + row * 0.20), (garage_w * 0.86, 0.022, 0.032), mats["garage_trim"])
    H.box(prefix + "_Driveway", (garage_x, front_y - 0.62, 0.125), (garage_w * 1.14, 1.16, 0.05), mats["driveway"])

    H.xy_cut_box(prefix + "_Door", (entry_x, front_y - 0.038, base_z + 0.36), 0.31, 0.03, 0.68, 0.04, mats["door"])
    H.box(prefix + "_Porch", (entry_x, front_y - 0.20, base_z + 0.06), (0.58, 0.35, 0.10), mats["porch"])
    H.cylinder(prefix + "_PorchLight", (entry_x + 0.23, front_y - 0.064, base_z + 0.66), 0.035, 0.055, mats["porch_light"], vertices=8, rotation=(math.pi / 2, 0, 0))

    # Asymmetrical windows avoid the repeated glued-façade look.
    positions = [cx - width * 0.27, cx + width * 0.04, cx + width * 0.31]
    patterns = ((True, False, True), (False, True, False))[index]
    for wi, wx in enumerate(positions):
        if abs(wx - garage_x) < garage_w * 0.55:
            continue
        window(prefix + f"_Window_{wi}", wx, front_y, base_z + 0.72, 0.33, 0.40, patterns[wi], mats)
    window(prefix + "_UpperWindow", cx + (-0.12 if index == 0 else 0.13) * width, front_y, base_z + 1.20, 0.38, 0.35, index == 1, mats)

    # Front lawn, walkway, hedge and one clearly visible side gate.
    H.box(prefix + "_Lawn", (cx, front_y - 0.53, 0.095), (width + 0.36, 0.92, 0.055), mats["lawn"])
    H.box(prefix + "_Walk", (entry_x, front_y - 0.55, 0.132), (0.28, 0.90, 0.035), mats["walk"])
    # Only one gate occupies the large center-side setback; the second is on
    # the far edge of the right property, so the homes never form a joined row.
    side = 1
    gate_x = cx + side * (width * 0.5 + 0.18)
    gate_pieces = [
        ((gate_x - 0.17, front_y + 0.04, 0.41), (0.055, 0.07, 0.74)),
        ((gate_x + 0.17, front_y + 0.04, 0.41), (0.055, 0.07, 0.74)),
        ((gate_x, front_y + 0.04, 0.23), (0.34, 0.055, 0.045)),
        ((gate_x, front_y + 0.04, 0.57), (0.34, 0.055, 0.045)),
    ]
    for si, dx in enumerate((-0.125, -0.0625, 0.0, 0.0625, 0.125)):
        gate_pieces.append(((gate_x + dx, front_y + 0.035, 0.40), (0.045, 0.045, 0.62)))
    H.cohesive_box_assembly(prefix + "_SideGate", gate_pieces, mats["fence"])
    return {"cx": cx, "front_y": front_y, "width": width, "garage_x": garage_x, "gate_x": gate_x, "ridge": ridge}


def tree(index, x, y, scale, mats):
    H.cylinder(f"SUBURB_Tree_{index:02d}_Trunk", (x, y, 0.32 * scale), 0.065 * scale, 0.64 * scale, mats["trunk"], vertices=7)
    for ci, (dx, dz, size) in enumerate(((0.0, 0.86, 0.32), (-0.20, 0.70, 0.25), (0.20, 0.72, 0.27), (0.02, 1.07, 0.24))):
        H.ico_ellipsoid(f"SUBURB_Tree_{index:02d}_Canopy_{ci}", (x + dx * scale, y, dz * scale), (size * 1.10 * scale, size * 0.82 * scale, size * scale), mats["leaf"] if ci % 2 == 0 else mats["leaf_dark"], subdivisions=1)


def car(index, x, y, scale, color, mats, facing=1, base_z=0.0):
    prefix = f"SUBURB_Car_{index:02d}"
    H.xy_cut_box(prefix + "_Lower", (x, y, base_z + 0.22 * scale), 0.94 * scale, 0.38 * scale, 0.22 * scale, 0.075 * scale, color)
    H.xy_cut_box(prefix + "_Cabin", (x - 0.04 * facing * scale, y, base_z + 0.40 * scale), 0.50 * scale, 0.32 * scale, 0.21 * scale, 0.06 * scale, color)
    H.xy_cut_box(prefix + "_Windshield", (x + 0.13 * facing * scale, y - 0.003, base_z + 0.42 * scale), 0.15 * scale, 0.326 * scale, 0.12 * scale, 0.025 * scale, mats["car_glass"])
    for wi, (dx, dy) in enumerate(((-0.29, -0.19), (-0.29, 0.19), (0.29, -0.19), (0.29, 0.19))):
        H.cylinder(prefix + f"_Wheel_{wi}", (x + dx * scale, y + dy * scale, base_z + 0.16 * scale), 0.082 * scale, 0.06 * scale, mats["tire"], vertices=8, rotation=(math.pi / 2, 0, 0))


def rain_streak(index, x, y, z, length, thickness, mat, phase):
    obj = H.beam(f"SUBURB_Rain_{index:03d}", Vector((x, y, z + length * 0.5)), Vector((x - 0.07, y, z - length * 0.5)), thickness, mat)
    base_z = obj.location.z
    for start_frame in range(1 - phase - 24, FULL_END + 25, 24):
        for frame, offset in ((start_frame, 0.0), (start_frame + 23, -3.35), (start_frame + 24, 0.0)):
            obj.location.z = base_z + offset
            obj.keyframe_insert(data_path="location", frame=frame)
    obj.location.z = base_z
    return obj


def animate_energy(data, events):
    for frame, energy in events:
        data.energy = energy
        data.keyframe_insert(data_path="energy", frame=frame)


def animate_emission(mat, events):
    strength = mat.node_tree.nodes["Principled BSDF"].inputs.get("Emission Strength")
    if strength:
        for frame, value in events:
            strength.default_value = value
            strength.keyframe_insert(data_path="default_value", frame=frame)


def make_camera(name, location, target, lens):
    data = bpy.data.cameras.new(name + "_Data")
    data.type = "PERSP"
    data.lens = lens
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam


def render(path, cam, frame, resolution):
    scene = bpy.context.scene
    scene.camera = cam
    scene.frame_set(frame)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    remove_v06_exterior()
    coll = collection()
    before = set(bpy.data.objects)

    mats = {
        "sky": material("SUBURB_Sky", (0.008, 0.018, 0.045), 0.95, (0.025, 0.06, 0.14), 0.10),
        "ground": material("SUBURB_Ground", (0.018, 0.040, 0.043), 0.94),
        "road": material("SUBURB_Road", (0.014, 0.020, 0.028), 0.90),
        "curb": material("SUBURB_Curb", (0.16, 0.18, 0.19), 0.85),
        "walk": material("SUBURB_Walk", (0.24, 0.25, 0.24), 0.86),
        "driveway": material("SUBURB_Driveway", (0.19, 0.20, 0.20), 0.88),
        "lawn": material("SUBURB_Lawn", (0.045, 0.105, 0.075), 0.92),
        "wall_a": material("SUBURB_Wall_A", (0.17, 0.26, 0.28), 0.80),
        "wall_b": material("SUBURB_Wall_B", (0.25, 0.20, 0.22), 0.80),
        "roof_a": material("SUBURB_Roof_A", (0.075, 0.095, 0.105), 0.88),
        "roof_b": material("SUBURB_Roof_B", (0.12, 0.065, 0.070), 0.88),
        "trim": material("SUBURB_Trim", (0.43, 0.40, 0.34), 0.82),
        "door": material("SUBURB_Door", (0.11, 0.060, 0.045), 0.84),
        "garage": material("SUBURB_Garage", (0.30, 0.30, 0.27), 0.86),
        "garage_trim": material("SUBURB_GarageTrim", (0.18, 0.18, 0.17), 0.88),
        "porch": material("SUBURB_Porch", (0.18, 0.19, 0.18), 0.90),
        "porch_light": material("SUBURB_PorchLight", (0.50, 0.28, 0.10), 0.55, (1.0, 0.42, 0.10), 1.8),
        "window_lit": material("SUBURB_Window_Lit", (0.44, 0.25, 0.10), 0.70, (1.0, 0.46, 0.13), 3.0),
        "window_dark": material("SUBURB_Window_Dark", (0.010, 0.030, 0.050), 0.62, (0.012, 0.035, 0.070), 0.08),
        "fence": material("SUBURB_Fence", (0.20, 0.14, 0.095), 0.88),
        "trunk": material("SUBURB_Trunk", (0.08, 0.050, 0.035), 0.92),
        "leaf": material("SUBURB_Leaf", (0.040, 0.13, 0.11), 0.90),
        "leaf_dark": material("SUBURB_LeafDark", (0.020, 0.070, 0.070), 0.92),
        "car_blue": material("SUBURB_CarBlue", (0.035, 0.13, 0.21), 0.72),
        "car_red": material("SUBURB_CarRed", (0.27, 0.050, 0.055), 0.72),
        "car_glass": material("SUBURB_CarGlass", (0.010, 0.045, 0.070), 0.48),
        "tire": material("SUBURB_Tire", (0.006, 0.008, 0.010), 0.92),
        "rain": material("SUBURB_Rain", (0.16, 0.34, 0.55), 0.32, (0.26, 0.56, 0.90), 1.15),
        "bolt": material("SUBURB_Bolt", (0.58, 0.75, 1.0), 0.30, (0.64, 0.80, 1.0), 7.0),
        "occluder": material("SUBURB_Occluder", (0.0, 0.0, 0.0), 1.0),
    }

    # Street and setback are shared, but the two houses remain separate scenes.
    H.box("SUBURB_SkyBackdrop", (0.0, 9.30, 2.0), (5.40, 0.08, 2.05), mats["sky"])
    H.box("SUBURB_Ground", (0.0, 6.15, 0.02), (5.60, 6.2, 0.07), mats["ground"])
    H.box("SUBURB_Road", (0.0, 4.15, 0.08), (5.55, 1.50, 0.09), mats["road"])
    H.box("SUBURB_CurbNear", (0.0, 3.35, 0.13), (5.55, 0.20, 0.11), mats["curb"])
    H.box("SUBURB_CurbFar", (0.0, 4.96, 0.13), (5.55, 0.24, 0.11), mats["curb"])
    H.box("SUBURB_WestOccluder", (-2.76, 5.8, 1.65), (0.08, 6.2, 3.30), mats["occluder"])
    H.box("SUBURB_TopOccluder", (0.0, 5.8, 3.27), (5.60, 6.2, 0.08), mats["occluder"])

    left = suburban_house(0, -1.72, 6.48, 2.34, 1.05, 0.15, 1.45, mats, coll, "a")
    right = suburban_house(1, 1.72, 6.62, 2.36, 1.08, 0.15, 1.48, mats, coll, "b")

    # More than one house-width of readable breathing space between façades.
    for idx, (x, y, s) in enumerate(((-2.47, 5.70, 0.66), (-0.57, 5.86, 0.52), (0.50, 5.78, 0.58), (2.48, 5.76, 0.70))):
        tree(idx, x, y, s, mats)
    # Right car is purposefully aligned to the right room window.
    car(0, 1.34, 4.44, 0.88, mats["car_red"], mats, facing=1, base_z=0.24)
    # A secondary car is parked farther away and only partly visible at left.
    car(1, -2.24, 4.58, 0.67, mats["car_blue"], mats, facing=-1, base_z=0.10)

    # A restrained streetlamp gives the right-window car one readable warm
    # highlight without lifting the entire neighborhood out of its night state.
    H.cylinder("SUBURB_Streetlamp_Pole", (2.05, 4.78, 0.72), 0.035, 1.38, mats["fence"], vertices=8)
    H.xy_cut_box("SUBURB_Streetlamp_Head", (2.05, 4.78, 1.42), 0.22, 0.15, 0.12, 0.025, mats["porch_light"])
    street_data = bpy.data.lights.new("SUBURB_Streetlamp_Data", "POINT")
    street_data.color = (1.0, 0.42, 0.16)
    street_data.energy = 82.0
    street_data.shadow_soft_size = 0.55
    street = bpy.data.objects.new("SUBURB_Streetlamp", street_data)
    coll.objects.link(street)
    street.location = (2.05, 4.72, 1.38)

    random.seed(70321)
    rain = []
    for index in range(82):
        layer = index % 3
        y = (3.05, 4.30, 5.65)[layer] + random.uniform(-0.16, 0.16)
        side = -1 if index % 2 == 0 else 1
        x = side * random.uniform(0.76, 2.04)
        z = random.uniform(1.25, 2.58)
        rain.append(rain_streak(index, x, y, z, random.uniform(0.18, 0.40) * (1.10 - layer * 0.13), (0.0055, 0.0042, 0.0032)[layer], mats["rain"], random.randrange(24)))

    bolt_points = [Vector((1.50, 9.20, 2.72)), Vector((1.34, 9.18, 2.43)), Vector((1.47, 9.16, 2.27)), Vector((1.20, 9.14, 1.88)), Vector((1.31, 9.12, 1.74)), Vector((1.10, 9.10, 1.36))]
    bolt_parts = [H.beam(f"SUBURB_LightningBolt_{i}", bolt_points[i], bolt_points[i + 1], 0.018, mats["bolt"]) for i in range(len(bolt_points) - 1)]
    for obj in bolt_parts:
        for frame, scale in ((1, 0.001), (46, 0.001), (48, 1.0), (50, 0.001), (240, 0.001)):
            obj.scale = (scale,) * 3
            obj.keyframe_insert(data_path="scale", frame=frame)

    outside_data = bpy.data.lights.new("SUBURB_LightningOutside_Data", "POINT")
    outside_data.color = (0.48, 0.68, 1.0)
    outside_data.shadow_soft_size = 3.2
    outside = bpy.data.objects.new("SUBURB_LightningOutside", outside_data)
    coll.objects.link(outside)
    outside.location = (0.0, 4.20, 2.90)

    room_data = bpy.data.lights.new("SUBURB_LightningRoom_Data", "AREA")
    room_data.color = (0.46, 0.67, 1.0)
    room_data.shape = "RECTANGLE"
    room_data.size, room_data.size_y = 4.8, 1.8
    room = bpy.data.objects.new("SUBURB_LightningRoom", room_data)
    coll.objects.link(room)
    room.location = (0.0, 2.74, 2.05)
    room.rotation_euler = (Vector((0.0, 0.0, 1.15)) - room.location).to_track_quat("-Z", "Y").to_euler()

    moon_data = bpy.data.lights.new("SUBURB_MoonFill_Data", "AREA")
    moon_data.color = (0.18, 0.31, 0.48)
    moon_data.energy = 430.0
    moon_data.shape = "RECTANGLE"
    moon_data.size, moon_data.size_y = 4.5, 2.3
    moon = bpy.data.objects.new("SUBURB_MoonFill", moon_data)
    coll.objects.link(moon)
    moon.location = (0.0, 5.35, 3.35)
    moon.rotation_euler = (Vector((0.0, 6.6, 0.72)) - moon.location).to_track_quat("-Z", "Y").to_euler()

    events = [(1, 0.0), (44, 0.0), (47, 260.0), (48, 1050.0), (49, 380.0), (52, 0.0), (168, 0.0), (171, 190.0), (172, 820.0), (173, 260.0), (176, 0.0), (240, 0.0)]
    animate_energy(outside_data, events)
    animate_energy(room_data, [(f, e * 0.62) for f, e in events])
    animate_emission(mats["sky"], [(1, 0.10), (44, 0.10), (48, 0.80), (52, 0.10), (168, 0.10), (172, 0.62), (176, 0.10), (240, 0.10)])

    relocate_new(before, coll)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end, scene.render.fps = 1, FULL_END, FPS
    scene["exterior_revision"] = "v08 detached rainy suburban houses, one composition per window"
    scene["website_loop_plan"] = "10s/240f master; 1s rain cycles; lightning near 2s and 7.2s"
    scene["suburban_layout"] = "two detached houses with yards, gates, driveway and right-window street car"

    exterior_cam = make_camera("CAM_QA_Suburb_v08", (0.0, 2.86, 1.78), (0.0, 5.95, 0.83), 35.0)
    left_cam = make_camera("CAM_QA_LeftWindow_v08", (-1.40, 1.48, 2.02), (-1.52, 6.35, 0.94), 48.0)
    right_cam = make_camera("CAM_QA_RightWindow_v08", (1.40, 1.48, 2.02), (1.46, 5.35, 0.82), 48.0)
    hero_cam = bpy.data.objects["CAM_HOME_Perspective"]
    render(NORMAL, exterior_cam, 24, (1280, 720))
    render(LIGHTNING, exterior_cam, 48, (1280, 720))
    render(LEFT_WINDOW, left_cam, 24, (900, 700))
    render(RIGHT_WINDOW, right_cam, 24, (900, 700))
    render(HERO, hero_cam, 24, (1400, 1148))

    scene.frame_set(1)
    scene.camera = hero_cam
    report = {
        "source": str(SOURCE), "output": str(OUT),
        "houses": 2, "detached": True, "trees": 4, "cars": 2, "rain_streaks": len(rain),
        "master_timeline": [1, FULL_END], "fps": FPS, "lightning_peaks": [48, 172],
        "design": "One broad suburban home per room window, independent front yards, visible side gates, broad driveways, and a right-window parked car.",
        "renders": [str(HERO), str(NORMAL), str(LIGHTNING), str(LEFT_WINDOW), str(RIGHT_WINDOW)],
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    print("V07_BLEND", OUT)
    print("V07_REPORT", REPORT)


if __name__ == "__main__":
    main()
