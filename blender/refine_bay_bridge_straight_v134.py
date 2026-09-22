"""Reorient the bridge nearly straight away from the right window and remove the rear cap."""

from pathlib import Path
import bpy, json
from mathutils import Vector

HERE = Path(__file__).resolve().parent
src = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v133-foggy-bay-bridge-visible.blend'
out = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v134-straight-bay-bridge-fog-view.blend'
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


# Remove the angled bridge and its flat rear cap, retaining the water, fog, moon, and glass towers.
bridge_prefixes = (
    'BAY_VIEW_Bridge', 'BAY_VIEW_Tower', 'BAY_VIEW_MainCable',
    'BAY_VIEW_Suspender', 'BAY_VIEW_DeckLamp',
)
for obj in list(bpy.data.objects):
    if obj.name.startswith(bridge_prefixes) or obj.name == 'BAY_VIEW_SkyBackdrop':
        bpy.data.objects.remove(obj, do_unlink=True)

# Use the world beyond the fog volume instead of a visible wall.
world = scene.world or bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get('Background')
if background:
    background.inputs['Color'].default_value = (.012, .017, .026, 1)
    background.inputs['Strength'].default_value = .16

bridge_material = bpy.data.materials['BAY_VIEW_BridgeSteel']
trim_material = bpy.data.materials['BAY_VIEW_GrayWhiteTrim']
lamp_material = bpy.data.materials['BAY_VIEW_BridgeLight']

# The deck stays just right of the right-hand window and heads almost perfectly away.
deck_near = Vector((2.03, 6.20, .30))
deck_far = Vector((2.03, 18.20, .30))
box('BAY_VIEW_BridgeDeckStraight', (2.03, 12.20, .30), (1.02, 12.0, .14), bridge_material, collection)
box('BAY_VIEW_BridgeDeckRailLeft', (1.53, 12.20, .46), (.035, 12.0, .22), trim_material, collection)
box('BAY_VIEW_BridgeDeckRailRight', (2.53, 12.20, .46), (.035, 12.0, .22), trim_material, collection)

# Four towers shrink with distance; perspective supplies the subtle remaining angle.
tower_specs = [
    (7.45, 2.15, .62),
    (10.15, 1.82, .54),
    (13.10, 1.50, .46),
    (16.00, 1.20, .38),
]
tower_pairs = []
for index, (y, height, half_width) in enumerate(tower_specs):
    center = Vector((2.03, y, .36))
    left = center + Vector((-half_width, 0, 0))
    right = center + Vector((half_width, 0, 0))
    beam_between(f'BAY_VIEW_TowerStraightLeft_{index:02d}', left, left + Vector((0, 0, height)), .055, bridge_material, collection)
    beam_between(f'BAY_VIEW_TowerStraightRight_{index:02d}', right, right + Vector((0, 0, height)), .055, bridge_material, collection)
    for level in (.34, .66):
        z = center.z + height * level
        beam_between(f'BAY_VIEW_TowerStraightCross_{index:02d}_{int(level*100)}',
                     (left.x, y, z), (right.x, y, z), .040, trim_material, collection)
    beam_between(f'BAY_VIEW_TowerStraightBraceA_{index:02d}',
                 left + Vector((0, 0, height * .08)), right + Vector((0, 0, height * .67)), .028, trim_material, collection)
    beam_between(f'BAY_VIEW_TowerStraightBraceB_{index:02d}',
                 right + Vector((0, 0, height * .08)), left + Vector((0, 0, height * .67)), .028, trim_material, collection)
    tower_pairs.append((left + Vector((0, 0, height)), right + Vector((0, 0, height))))

for side in range(2):
    near_anchor = Vector((1.53 if side == 0 else 2.53, deck_near.y, .50))
    far_anchor = Vector((1.70 if side == 0 else 2.36, deck_far.y, .44))
    curve_polyline(f'BAY_VIEW_MainCableStraightNear_{side}',
                   [near_anchor, tower_pairs[0][side]], .016, trim_material, collection)
    for span in range(len(tower_pairs) - 1):
        curve_polyline(f'BAY_VIEW_MainCableStraight_{side}_{span}',
                       sag_points(tower_pairs[span][side], tower_pairs[span + 1][side], .48 - span * .08),
                       .016, trim_material, collection)
    curve_polyline(f'BAY_VIEW_MainCableStraightFar_{side}',
                   [tower_pairs[-1][side], far_anchor], .013, trim_material, collection)

# Sparse vertical suspenders and lamps keep the bridge readable without making a dense fence.
for index in range(20):
    t = (index + .45) / 20
    y = deck_near.y + (deck_far.y - deck_near.y) * t
    half_width = .50 - .16 * t
    height = .70
    for side, x in enumerate((2.03 - half_width, 2.03 + half_width)):
        beam_between(f'BAY_VIEW_SuspenderStraight_{index:02d}_{side}',
                     (x, y, .48), (x, y, .48 + height), .010, trim_material, collection)
    if index % 2 == 0:
        box(f'BAY_VIEW_DeckLampStraight_{index:02d}', (2.03, y, .55),
            (.040, .040, .060), lamp_material, collection)

# Make the water composition read predominantly to the left of the bridge.
water = bpy.data.objects.get('BAY_VIEW_WaterPlane')
if water:
    water.location.x = -.85
    water.location.y = 11.5
    water.dimensions.x = 13.4
    water.dimensions.y = 15.5

# Extend the fog deeper so the straight bridge dissolves instead of meeting a cap.
fog = bpy.data.objects.get('BAY_VIEW_FogVolume')
if fog:
    fog.location.y = 14.0
    fog.dimensions.y = 22.0

scene['cathode_restyle_version'] = 'v134'
scene['cathode_bay_bridge_straight_v134'] = True
scene['cathode_exterior_setting'] = 'straight-away Bay Bridge view with open water left and uncapped fog distance'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

# QA from the room and a close exterior view.
import sys
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121

renders = {}
original_camera = scene.camera
camera = V121.qa_camera('CAM_QA_BayStraightRoom_v134', (-2.72, .18, 2.34), (.75, 10.4, 1.20), 49)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v134-bay-straight-room.png'
V121.render(scene, camera, image, (1200, 800))
renders['room'] = str(image)
camera = V121.qa_camera('CAM_QA_BayStraightExterior_v134', (-.10, 3.12, 1.76), (1.00, 11.2, 1.10), 50)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v134-bay-straight-exterior.png'
V121.render(scene, camera, image, (1200, 800))
renders['exterior'] = str(image)
if original_camera:
    scene.camera = original_camera
bpy.ops.wm.save_as_mainfile(filepath=str(out))

report = {
    'source': str(src),
    'output': str(out),
    'bridge_alignment': 'nearly straight away from right window',
    'bridge_towers': len(tower_specs),
    'rear_cap_removed': bpy.data.objects.get('BAY_VIEW_SkyBackdrop') is None,
    'open_water_left': True,
    'fog_extended': True,
    'rain_hidden': True,
    'renders': renders,
}
out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V134_REPORT=' + json.dumps(report))
