"""Separate the four glass towers and push bridge structure farther into the bay."""

from pathlib import Path
import bpy, json, random
from mathutils import Vector

HERE = Path(__file__).resolve().parent
src = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v136-deep-bay-parallel-bridge.blend'
out = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v137-deep-bay-separated-towers.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene = bpy.context.scene
collection = bpy.data.collections['CATHODE_BAY_BRIDGE_WINDOW_VIEW']


def box(name, center, dimensions, material):
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


def beam_between(name, start, end, thickness, material):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    obj = box(name, (start + end) / 2, (thickness, thickness, direction.length), material)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj


def curve_polyline(name, points, bevel, material):
    curve = bpy.data.curves.new(name + '_Curve', 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = bevel
    curve.bevel_resolution = 1
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, coordinate in zip(spline.points, points):
        point.co = (*coordinate, 1)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def sag_points(start, end, sag, steps=30):
    result = []
    for step in range(steps + 1):
        t = step / steps
        point = start.lerp(end, t)
        point.z -= sag * 4 * t * (1 - t)
        result.append(point)
    return result


for obj in list(bpy.data.objects):
    if obj.name.startswith((
        'BAY_VIEW_FinalGlassTower', 'BAY_VIEW_FinalTowerBand',
        'BAY_VIEW_FinalTowerMullion', 'BAY_VIEW_FinalTowerWindow',
        'BAY_VIEW_FinalTowerRoof', 'BAY_VIEW_FinalBridgeTower',
        'BAY_VIEW_FinalMainCable', 'BAY_VIEW_FinalSuspender',
        'BAY_VIEW_FinalDeckLamp',
    )):
        bpy.data.objects.remove(obj, do_unlink=True)

glass = bpy.data.materials['BAY_VIEW_GlassFacade']
glass_alt = bpy.data.materials['BAY_VIEW_GlassFacadeAlt']
trim = bpy.data.materials['BAY_VIEW_GrayWhiteTrim']
bridge = bpy.data.materials['BAY_VIEW_BridgeSteel']
dark_window = bpy.data.materials['BAY_VIEW_WindowDark']
dim_window = bpy.data.materials['BAY_VIEW_WindowDim']
lit_window = bpy.data.materials['BAY_VIEW_WindowLit']
bridge_light = bpy.data.materials['BAY_VIEW_BridgeLight']

rng = random.Random(13708)

# Narrow gaps, alternating depths, and distinct heights prevent the four towers merging.
buildings = [
    (-2.11, 7.0, .39, 1.06, -4.25, 2.90, glass, 2),
    (-1.69, 7.9, .37, .98, -4.32, 2.54, glass_alt, 2),
    (-1.28, 8.8, .36, .92, -4.38, 2.23, glass, 2),
    (-.88, 9.7, .35, .86, -4.44, 2.68, glass_alt, 2),
]
for index, (cx, y, width, depth, base, top, facade, columns) in enumerate(buildings):
    height = top - base
    front = y - depth / 2
    box(f'BAY_VIEW_FinalGlassTower_{index:02d}', (cx, y, base + height / 2), (width, depth, height), facade)
    rows = max(13, int(height / .34))
    x_spacing = width / columns
    z_spacing = height / rows
    for row in range(1, rows):
        box(f'BAY_VIEW_FinalTowerBand_{index:02d}_{row:02d}',
            (cx, front - .018, base + row * z_spacing), (width + .016, .032, .014), trim)
    for column in range(columns + 1):
        x = cx - width / 2 + column * x_spacing
        box(f'BAY_VIEW_FinalTowerMullion_{index:02d}_{column:02d}',
            (x, front - .019, base + height / 2), (.015, .033, height), trim)
    for row in range(rows):
        z = base + (row + .5) * z_spacing
        for column in range(columns):
            x = cx - width / 2 + (column + .5) * x_spacing
            roll = rng.random()
            material = lit_window if roll < .13 else (dim_window if roll < .33 else dark_window)
            box(f'BAY_VIEW_FinalTowerWindow_{index:02d}_{row:02d}_{column:02d}',
                (x, front - .022, z), (x_spacing * .78, .025, z_spacing * .76), material)
    box(f'BAY_VIEW_FinalTowerRoof_{index:02d}', (cx, y, top + .06),
        (width + .035, depth + .035, .12), bridge)

# All major bridge structure starts farther out; the near deck remains outside frame and continuous.
bridge_x = 2.76
near_y = 4.20
far_y = 35.0
tower_specs = [
    (12.4, 1.88, .56),
    (18.6, 1.80, .54),
    (24.7, 1.70, .51),
    (30.6, 1.60, .48),
]
tower_pairs = []
for index, (y, height, half_width) in enumerate(tower_specs):
    center = Vector((bridge_x, y, .34))
    left = Vector((bridge_x - half_width, y, .34))
    right = Vector((bridge_x + half_width, y, .34))
    beam_between(f'BAY_VIEW_FinalBridgeTowerLeft_{index:02d}', left, left + Vector((0, 0, height)), .050, bridge)
    beam_between(f'BAY_VIEW_FinalBridgeTowerRight_{index:02d}', right, right + Vector((0, 0, height)), .050, bridge)
    for level in (.34, .67):
        z = center.z + height * level
        beam_between(f'BAY_VIEW_FinalBridgeTowerCross_{index:02d}_{int(level*100)}',
                     (left.x, y, z), (right.x, y, z), .034, trim)
    beam_between(f'BAY_VIEW_FinalBridgeTowerBraceA_{index:02d}',
                 left + Vector((0, 0, height * .08)), right + Vector((0, 0, height * .66)), .024, trim)
    beam_between(f'BAY_VIEW_FinalBridgeTowerBraceB_{index:02d}',
                 right + Vector((0, 0, height * .08)), left + Vector((0, 0, height * .66)), .024, trim)
    tower_pairs.append((left + Vector((0, 0, height)), right + Vector((0, 0, height))))

for side in range(2):
    side_x = bridge_x - .39 if side == 0 else bridge_x + .39
    near_anchor = Vector((side_x, near_y, .44))
    far_anchor = Vector((bridge_x + (-.30 if side == 0 else .30), far_y, .40))
    curve_polyline(f'BAY_VIEW_FinalMainCableNear_{side}', [near_anchor, tower_pairs[0][side]], .013, trim)
    for span in range(len(tower_pairs) - 1):
        curve_polyline(f'BAY_VIEW_FinalMainCable_{side}_{span}',
                       sag_points(tower_pairs[span][side], tower_pairs[span + 1][side], .50), .013, trim)
    curve_polyline(f'BAY_VIEW_FinalMainCableFar_{side}', [tower_pairs[-1][side], far_anchor], .009, trim)

for index in range(36):
    t = (index + .5) / 36
    y = 8.0 + (far_y - 8.0) * t
    half_width = .38 - .08 * t
    for side, x in enumerate((bridge_x - half_width, bridge_x + half_width)):
        beam_between(f'BAY_VIEW_FinalSuspender_{index:02d}_{side}',
                     (x, y, .44), (x, y, .92), .0075, trim)
    if index % 3 == 0:
        box(f'BAY_VIEW_FinalDeckLamp_{index:02d}', (bridge_x, y, .49),
            (.032, .032, .050), bridge_light)

scene['cathode_restyle_version'] = 'v137'
scene['cathode_deep_bay_spacing_v137'] = True
scene['cathode_exterior_setting'] = 'deep bay with four separated glass silhouettes and bridge structure starting farther out'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

# Final verification views.
import sys
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121

renders = {}
original = scene.camera
for camera_name, location, target, lens, filename in (
    ('CAM_QA_DeepBayBothWindows_v137', (0.0, -.85, 1.82), (0.0, 3.65, 1.90), 58, 'lofi-room-cathode-v137-both-windows.png'),
    ('CAM_QA_DeepBayExterior_v137', (-.05, 3.15, 1.76), (.10, 15.0, .92), 51, 'lofi-room-cathode-v137-deep-bay-exterior.png'),
):
    camera = V121.qa_camera(camera_name, location, target, lens)
    path = HERE / 'outputs' / 'blender' / filename
    V121.render(scene, camera, path, (1500, 900))
    renders[camera_name] = str(path)
if original:
    scene.camera = original
bpy.ops.wm.save_as_mainfile(filepath=str(out))

report = {
    'source': str(src),
    'output': str(out),
    'separated_glass_towers': len(buildings),
    'first_bridge_tower_y': tower_specs[0][0],
    'parallel_bridge': True,
    'continuous_deck_to_fog': True,
    'visible_water': True,
    'renders': renders,
}
out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V137_REPORT=' + json.dumps(report))
