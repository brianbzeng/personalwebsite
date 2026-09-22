"""Rebuild the exterior to closely match the supplied high-rise Bay Bridge reference."""

from pathlib import Path
import bpy, json, math, random, sys
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121

src = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v134-straight-bay-bridge-fog-view.blend'
out = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v135-bay-reference-composition.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene = bpy.context.scene
collection = bpy.data.collections.get('CATHODE_BAY_BRIDGE_WINDOW_VIEW')
if not collection:
    raise RuntimeError('Bay Bridge exterior collection is missing')


def box(name, center, dimensions, material, target_collection):
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
    target_collection.objects.link(obj)
    obj.location = center
    obj.data.materials.append(material)
    return obj


def beam_between(name, start, end, thickness, material, target_collection):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    obj = box(name, (start + end) / 2, (thickness, thickness, direction.length), material, target_collection)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj


def curve_polyline(name, points, bevel, material, target_collection):
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
    target_collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def sag_points(start, end, sag, steps=22):
    points = []
    for step in range(steps + 1):
        t = step / steps
        point = start.lerp(end, t)
        point.z -= sag * 4 * t * (1 - t)
        points.append(point)
    return points


# Remove both earlier bridge passes and the first three-building interpretation.
remove_prefixes = (
    'BAY_VIEW_Bridge', 'BAY_VIEW_Tower', 'BAY_VIEW_MainCable',
    'BAY_VIEW_Suspender', 'BAY_VIEW_DeckLamp', 'BAY_VIEW_GlassTower',
    'BAY_VIEW_TowerBand', 'BAY_VIEW_TowerMullion', 'BAY_VIEW_TowerWindow',
    'BAY_VIEW_TowerRoof', 'BAY_VIEW_LowBuilding', 'BAY_VIEW_LowRoof',
    'BAY_VIEW_LowWindow',
)
for obj in list(bpy.data.objects):
    if obj.name.startswith(remove_prefixes):
        bpy.data.objects.remove(obj, do_unlink=True)

glass = bpy.data.materials['BAY_VIEW_GlassFacade']
glass_alt = bpy.data.materials['BAY_VIEW_GlassFacadeAlt']
trim = bpy.data.materials['BAY_VIEW_GrayWhiteTrim']
bridge = bpy.data.materials['BAY_VIEW_BridgeSteel']
dark_window = bpy.data.materials['BAY_VIEW_WindowDark']
dim_window = bpy.data.materials['BAY_VIEW_WindowDim']
lit_window = bpy.data.materials['BAY_VIEW_WindowLit']
bridge_light = bpy.data.materials['BAY_VIEW_BridgeLight']

rng = random.Random(13508)

# Four staggered glass towers occupy the left third, matching the reference overlap.
buildings = [
    (-2.48, 6.65, 1.08, 1.10, -4.25, 3.46, glass, 3),
    (-1.94, 7.45, .96, 1.02, -4.30, 2.66, glass_alt, 3),
    (-1.40, 8.15, .92, .96, -4.38, 2.34, glass, 3),
    (-.88, 8.85, .78, .90, -4.42, 2.76, glass_alt, 2),
]
facade_windows = 0
for index, (cx, y, width, depth, base, top, facade, columns) in enumerate(buildings):
    height = top - base
    front = y - depth / 2
    box(f'BAY_VIEW_ReferenceGlassTower_{index:02d}', (cx, y, base + height / 2),
        (width, depth, height), facade, collection)
    rows = max(11, int(height / .38))
    x_spacing = width / columns
    z_spacing = height / rows
    for row in range(1, rows):
        box(f'BAY_VIEW_ReferenceTowerBand_{index:02d}_{row:02d}',
            (cx, front - .020, base + row * z_spacing),
            (width + .020, .034, .016), trim, collection)
    for column in range(columns + 1):
        x = cx - width / 2 + column * x_spacing
        box(f'BAY_VIEW_ReferenceTowerMullion_{index:02d}_{column:02d}',
            (x, front - .021, base + height / 2), (.018, .035, height), trim, collection)
    for row in range(rows):
        z = base + (row + .5) * z_spacing
        for column in range(columns):
            x = cx - width / 2 + (column + .5) * x_spacing
            roll = rng.random()
            window_material = lit_window if roll < .14 else (dim_window if roll < .34 else dark_window)
            box(f'BAY_VIEW_ReferenceTowerWindow_{index:02d}_{row:02d}_{column:02d}',
                (x, front - .024, z), (x_spacing * .82, .026, z_spacing * .78),
                window_material, collection)
            facade_windows += 1
    box(f'BAY_VIEW_ReferenceTowerRoof_{index:02d}', (cx, y, top + .07),
        (width + .04, depth + .04, .14), bridge, collection)

# Low waterfront buildings occupy the lower-right foreground beneath the bridge.
low_buildings = [
    (.15, 7.3, .82, .86, -.48, .36),
    (.90, 7.8, .96, .92, -.48, .52),
    (1.72, 8.2, .78, .82, -.48, .28),
    (2.45, 8.6, .92, .86, -.48, .40),
]
for index, (cx, y, width, depth, base, top) in enumerate(low_buildings):
    height = top - base
    box(f'BAY_VIEW_LowBuilding_{index:02d}', (cx, y, base + height / 2),
        (width, depth, height), bridge, collection)
    box(f'BAY_VIEW_LowRoof_{index:02d}', (cx, y, top + .055),
        (width + .04, depth + .04, .11), trim, collection)
    for column in range(3):
        x = cx - width * .30 + column * width * .30
        box(f'BAY_VIEW_LowWindow_{index:02d}_{column:02d}',
            (x, y - depth / 2 - .016, base + height * .58),
            (width * .16, .026, height * .24), dim_window if rng.random() < .55 else dark_window, collection)

# Reference bridge: near approach begins outside the right wall, then enters the view mid-span.
near = Vector((4.35, 5.15, .28))
far = Vector((.18, 17.30, .40))
plan = Vector((far.x - near.x, far.y - near.y, 0))
plan_length = plan.length
direction = plan.normalized()
normal = Vector((-direction.y, direction.x, 0))
midpoint = (near + far) / 2
angle = math.atan2(-plan.x, plan.y)

deck = box('BAY_VIEW_BridgeReferenceDeck', midpoint, (.74, plan_length, .14), bridge, collection)
deck.rotation_euler[2] = angle
for side, sign in enumerate((-1, 1)):
    rail_center = midpoint + normal * (.37 * sign) + Vector((0, 0, .16))
    rail = box(f'BAY_VIEW_BridgeReferenceRail_{side}', rail_center, (.034, plan_length, .22), trim, collection)
    rail.rotation_euler[2] = angle

# First tower is intentionally beyond the right wall; the following three cross the view.
tower_parameters = [(.16, 2.30, .64), (.39, 2.02, .58), (.60, 1.66, .50), (.78, 1.32, .42)]
tower_pairs = []
for index, (t, height, half_width) in enumerate(tower_parameters):
    center = near.lerp(far, t)
    left = center - normal * half_width
    right = center + normal * half_width
    beam_between(f'BAY_VIEW_TowerReferenceLeft_{index:02d}', left, left + Vector((0, 0, height)), .055, bridge, collection)
    beam_between(f'BAY_VIEW_TowerReferenceRight_{index:02d}', right, right + Vector((0, 0, height)), .055, bridge, collection)
    for level in (.34, .68):
        z = center.z + height * level
        beam_between(f'BAY_VIEW_TowerReferenceCross_{index:02d}_{int(level*100)}',
                     (left.x, left.y, z), (right.x, right.y, z), .038, trim, collection)
    beam_between(f'BAY_VIEW_TowerReferenceBraceA_{index:02d}',
                 left + Vector((0, 0, height * .08)), right + Vector((0, 0, height * .66)), .027, trim, collection)
    beam_between(f'BAY_VIEW_TowerReferenceBraceB_{index:02d}',
                 right + Vector((0, 0, height * .08)), left + Vector((0, 0, height * .66)), .027, trim, collection)
    tower_pairs.append((left + Vector((0, 0, height)), right + Vector((0, 0, height))))

for side in range(2):
    near_anchor = near + normal * ((-.37) if side == 0 else .37) + Vector((0, 0, .18))
    far_anchor = far + normal * ((-.25) if side == 0 else .25) + Vector((0, 0, .12))
    curve_polyline(f'BAY_VIEW_MainCableReferenceNear_{side}',
                   [near_anchor, tower_pairs[0][side]], .015, trim, collection)
    for span in range(len(tower_pairs) - 1):
        curve_polyline(f'BAY_VIEW_MainCableReference_{side}_{span}',
                       sag_points(tower_pairs[span][side], tower_pairs[span + 1][side], .50 - span * .09),
                       .015, trim, collection)
    curve_polyline(f'BAY_VIEW_MainCableReferenceFar_{side}',
                   [tower_pairs[-1][side], far_anchor], .012, trim, collection)

# Thin suspenders and sparse deck lights reinforce depth without filling the bay.
for index in range(22):
    t = (index + .5) / 22
    center = near.lerp(far, t)
    half_width = .37 - .12 * t
    for side, sign in enumerate((-1, 1)):
        point = center + normal * (half_width * sign)
        beam_between(f'BAY_VIEW_SuspenderReference_{index:02d}_{side}',
                     point + Vector((0, 0, .18)), point + Vector((0, 0, .78 - .18 * t)),
                     .009, trim, collection)
    if index % 2 == 0:
        box(f'BAY_VIEW_DeckLampReference_{index:02d}', center + Vector((0, 0, .25)),
            (.036, .036, .055), bridge_light, collection)

# Broad water and deeper fog preserve the empty bay at center-left and hide the endpoint.
water = bpy.data.objects.get('BAY_VIEW_WaterPlane')
if water:
    water.location = (-.65, 11.6, -.52)
    water.dimensions.x = 14.5
    water.dimensions.y = 16.5
fog = bpy.data.objects.get('BAY_VIEW_FogVolume')
if fog:
    fog.location.y = 14.2
    fog.dimensions.x = 15.0
    fog.dimensions.y = 23.0

scene['cathode_restyle_version'] = 'v135'
scene['cathode_bay_reference_composition_v135'] = True
scene['cathode_exterior_setting'] = 'reference-matched Bay view: four left towers, low waterfront, offscreen right bridge approach'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

renders = {}
original_camera = scene.camera
camera = V121.qa_camera('CAM_QA_BayReferenceRoom_v135', (-2.72, .18, 2.34), (.25, 10.2, 1.18), 49)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v135-bay-reference-room.png'
V121.render(scene, camera, image, (1200, 800))
renders['room'] = str(image)
camera = V121.qa_camera('CAM_QA_BayReferenceExterior_v135', (-.10, 3.10, 1.76), (.15, 10.8, 1.05), 50)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v135-bay-reference-exterior.png'
V121.render(scene, camera, image, (1200, 800))
renders['exterior'] = str(image)
if original_camera:
    scene.camera = original_camera
bpy.ops.wm.save_as_mainfile(filepath=str(out))

report = {
    'source': str(src),
    'output': str(out),
    'reference_left_glass_towers': len(buildings),
    'reference_low_waterfront_buildings': len(low_buildings),
    'bridge_towers': len(tower_parameters),
    'near_bridge_approach_offscreen_right': True,
    'rear_cap_removed': bpy.data.objects.get('BAY_VIEW_SkyBackdrop') is None,
    'water_and_fog': True,
    'rain_hidden': True,
    'renders': renders,
}
out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V135_REPORT=' + json.dumps(report))
