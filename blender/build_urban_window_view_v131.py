"""Refine the window exterior into a high-floor grayscale nighttime skyline."""

from pathlib import Path
import bpy, json, random, sys
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121

src = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v130-urban-skyline-window-view.blend'
out = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v131-high-floor-night-skyline.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene = bpy.context.scene
original_camera = scene.camera


def mat(name, color, rough=.86, emit=None, power=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.roughness = rough
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = rough
        if emit is not None:
            emission = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
            if emission:
                emission.default_value = (*emit, 1)
            strength = bsdf.inputs.get('Emission Strength')
            if strength:
                strength.default_value = power
    return material


def box(name, center, dimensions, material, collection):
    x, y, z = (value / 2 for value in dimensions)
    vertices = [
        (-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
        (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name + '_Mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = center
    obj.data.materials.append(material)
    return obj


old = bpy.data.collections.get('CATHODE_URBAN_WINDOW_VIEW')
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
for obj in list(bpy.data.objects):
    if obj.name.startswith(('CITY_VIEW_', 'LIGHT_CityView_')):
        bpy.data.objects.remove(obj, do_unlink=True)

collection = bpy.data.collections.new('CATHODE_URBAN_WINDOW_VIEW')
scene.collection.children.link(collection)

materials = {
    'sky': mat('CITY_VIEW_Sky_v131', (0.010, 0.014, 0.022), .99, (0.018, 0.024, 0.036), .12),
    'near': mat('CITY_VIEW_NearFacade_v131', (0.048, 0.053, 0.063), .91),
    'mid': mat('CITY_VIEW_MidFacade_v131', (0.065, 0.070, 0.082), .90),
    'far': mat('CITY_VIEW_FarFacade_v131', (0.038, 0.043, 0.053), .94),
    'trim': mat('CITY_VIEW_OutlineTrim_v131', (0.185, 0.192, 0.205), .82),
    'roof': mat('CITY_VIEW_Roof_v131', (0.027, 0.031, 0.039), .95),
    'dark': mat('CITY_VIEW_WindowDark_v131', (0.008, 0.012, 0.019), .66, (0.012, 0.018, 0.028), .04),
    'dim': mat('CITY_VIEW_WindowDim_v131', (0.090, 0.098, 0.112), .60, (0.14, 0.15, 0.18), .26),
    'lit': mat('CITY_VIEW_WindowLit_v131', (0.34, 0.35, 0.37), .52, (0.72, 0.74, 0.78), 1.30),
}

# Deep backdrop gives the apertures a true night value without a pitch-black void.
box('CITY_VIEW_SkyBackdrop_v131', (0, 15.0, 2.7), (15.0, .12, 10.0), materials['sky'], collection)

rng = random.Random(13108)

# Buildings are deliberately lowered so the room reads as a high-floor apartment.
# Their rooflines cross the two window apertures at different heights, while taller
# distant towers preserve an urban skyline behind them.
buildings = [
    # x, y, width, depth, base, top, material, facade columns
    (-3.10, 7.4, 1.95, 1.20, -4.10, 1.32, 'near', 4),
    (-1.25, 8.3, 1.55, 1.05, -4.25, 2.02, 'mid', 3),
    ( 0.18, 9.4, 1.20, 1.00, -4.35, 2.72, 'far', 3),
    ( 1.46, 7.8, 1.62, 1.18, -4.10, 1.60, 'near', 4),
    ( 3.10, 8.7, 1.72, 1.06, -4.30, 2.34, 'mid', 4),
]

window_count = 0
lit_count = 0
for index, (cx, y, width, depth, base, top, key, columns) in enumerate(buildings):
    height = top - base
    front_y = y - depth / 2
    box(f'CITY_VIEW_Building_{index:02d}_v131', (cx, y, base + height / 2),
        (width, depth, height), materials[key], collection)

    # Thin gray-white corner and roof trim carry the room's outlined visual language.
    strip = .025
    box(f'CITY_VIEW_Roofline_{index:02d}_v131', (cx, front_y - .018, top + .025),
        (width + .06, .035, .055), materials['trim'], collection)
    box(f'CITY_VIEW_LeftEdge_{index:02d}_v131', (cx - width / 2 + strip, front_y - .017, base + height / 2),
        (strip, .034, height), materials['trim'], collection)
    box(f'CITY_VIEW_RightEdge_{index:02d}_v131', (cx + width / 2 - strip, front_y - .017, base + height / 2),
        (strip, .034, height), materials['trim'], collection)

    rows = max(8, int(height / .43))
    x_spacing = width / (columns + 1)
    z_spacing = (height - .36) / (rows + 1)
    for row in range(rows):
        z = base + .18 + (row + 1) * z_spacing
        for column_index in range(columns):
            x = cx - width / 2 + (column_index + 1) * x_spacing
            roll = rng.random()
            if roll < .18:
                window_material = materials['lit']
                lit_count += 1
            elif roll < .39:
                window_material = materials['dim']
            else:
                window_material = materials['dark']
            box(f'CITY_VIEW_Window_{index:02d}_{row:02d}_{column_index:02d}_v131',
                (x, front_y - .020, z), (x_spacing * .52, .028, z_spacing * .47),
                window_material, collection)
            window_count += 1
        if row < rows - 1:
            box(f'CITY_VIEW_FloorLine_{index:02d}_{row:02d}_v131',
                (cx, front_y - .019, z + z_spacing * .50),
                (width - .08, .030, .016), materials['trim'], collection)

    # Roof details appear as quiet silhouettes rather than bright props.
    box(f'CITY_VIEW_Parapet_{index:02d}_v131', (cx, y, top + .09),
        (width + .06, depth + .04, .18), materials['roof'], collection)
    if index in (0, 2, 4):
        utility_width = width * (.25 if index != 2 else .34)
        box(f'CITY_VIEW_RoofUtility_{index:02d}_v131',
            (cx + width * .16, y + depth * .06, top + .28),
            (utility_width, depth * .42, .38), materials['roof'], collection)

# Slender back towers break up the skyline without obscuring the nearer rooftops.
rear_towers = [
    (-3.80, 11.6, 1.18, -4.7, 2.82),
    (-2.05, 12.0, .92, -4.7, 3.28),
    ( 1.02, 11.8, 1.00, -4.7, 3.12),
    ( 2.58, 12.2, 1.14, -4.7, 2.92),
    ( 4.05, 11.6, .92, -4.7, 3.38),
]
for index, (cx, y, width, base, top) in enumerate(rear_towers):
    height = top - base
    box(f'CITY_VIEW_BackTower_{index:02d}_v131', (cx, y, base + height / 2),
        (width, .82, height), materials['far'], collection)
    front_y = y - .41
    box(f'CITY_VIEW_BackRoofline_{index:02d}_v131', (cx, front_y - .016, top + .018),
        (width + .04, .030, .040), materials['trim'], collection)
    for row in range(9):
        z = base + .55 + row * .58
        if z > top - .22:
            continue
        for column_index in range(2):
            x = cx + (-.22 if column_index == 0 else .22) * width
            window_material = materials['dim'] if rng.random() < .28 else materials['dark']
            box(f'CITY_VIEW_BackWindow_{index:02d}_{row:02d}_{column_index:02d}_v131',
                (x, front_y - .018, z), (width * .27, .024, .22), window_material, collection)

# A restrained cool area light lets the geometry read while preserving nighttime contrast.
light_data = bpy.data.lights.new('LIGHT_CityView_Moon_v131_Data', 'AREA')
light_data.energy = 72
light_data.shape = 'RECTANGLE'
light_data.size = 8
light_data.size_y = 4
light_data.color = (.56, .61, .70)
light = bpy.data.objects.new('LIGHT_CityView_Moon_v131', light_data)
collection.objects.link(light)
light.location = (-3.4, 4.5, 5.1)
light.rotation_euler = (Vector((0, 8.4, .9)) - light.location).to_track_quat('-Z', 'Y').to_euler()

for candidate_collection in bpy.data.collections:
    if 'RAIN' in candidate_collection.name.upper():
        candidate_collection.hide_render = True
        candidate_collection.hide_viewport = True
for obj in bpy.data.objects:
    if 'RAIN' in obj.name.upper():
        obj.hide_render = True
        obj.hide_viewport = True

scene['cathode_restyle_version'] = 'v131'
scene['cathode_urban_window_view_v131'] = True
scene['cathode_exterior_setting'] = 'high-floor nighttime apartment skyline; street intentionally omitted'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

renders = {}
camera = V121.qa_camera('CAM_QA_UrbanRoomView_v131', (-2.70, .20, 2.35), (0, 7.8, 1.20), 48)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v131-high-floor-room-view.png'
V121.render(scene, camera, image, (1200, 800))
renders['room'] = str(image)
camera = V121.qa_camera('CAM_QA_UrbanExterior_v131', (0, 2.78, 1.82), (0, 9.0, 1.35), 48)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v131-high-floor-exterior.png'
V121.render(scene, camera, image, (1200, 800))
renders['exterior'] = str(image)
if original_camera:
    scene.camera = original_camera
bpy.ops.wm.save_as_mainfile(filepath=str(out))

report = {
    'source': str(src),
    'output': str(out),
    'street_objects': 0,
    'foreground_buildings': len(buildings),
    'rear_towers': len(rear_towers),
    'facade_windows': window_count,
    'lit_windows': lit_count,
    'rain_hidden': True,
    'renders': renders,
}
out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V131_REPORT=' + json.dumps(report))
