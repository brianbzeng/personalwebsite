"""Create a grayscale, fog-softened Bay Bridge-inspired nighttime window view."""

from pathlib import Path
import bpy, json, math, random, sys
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121

src = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v131-high-floor-night-skyline.blend'
out = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v132-foggy-bay-bridge-night-view.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene = bpy.context.scene
original_camera = scene.camera


def material(name, color, rough=.8, metallic=0.0, emission=None, strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.roughness = rough
    mat.metallic = metallic
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metallic
        if emission is not None:
            socket = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
            if socket:
                socket.default_value = (*emission, 1)
            power = bsdf.inputs.get('Emission Strength')
            if power:
                power.default_value = strength
    return mat


def box(name, center, dimensions, mat, collection):
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
    obj.data.materials.append(mat)
    return obj


def beam_between(name, start, end, thickness, mat, collection):
    start = Vector(start)
    end = Vector(end)
    midpoint = (start + end) / 2
    direction = end - start
    obj = box(name, midpoint, (thickness, thickness, direction.length), mat, collection)
    obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    return obj


def curve_polyline(name, points, bevel, mat, collection):
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
    obj.data.materials.append(mat)
    return obj


def fog_material(name, density):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    volume = nodes.new('ShaderNodeVolumePrincipled')
    volume.inputs['Density'].default_value = density
    volume.inputs['Color'].default_value = (.24, .27, .32, 1)
    volume.inputs['Anisotropy'].default_value = .08
    links.new(volume.outputs['Volume'], output.inputs['Volume'])
    return mat


old = bpy.data.collections.get('CATHODE_URBAN_WINDOW_VIEW')
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
for obj in list(bpy.data.objects):
    if obj.name.startswith(('CITY_VIEW_', 'BAY_VIEW_', 'LIGHT_CityView_', 'LIGHT_BayView_')):
        bpy.data.objects.remove(obj, do_unlink=True)

collection = bpy.data.collections.new('CATHODE_BAY_BRIDGE_WINDOW_VIEW')
scene.collection.children.link(collection)

materials = {
    'sky': material('BAY_VIEW_Sky', (.012, .017, .026), .99, emission=(.022, .029, .043), strength=.13),
    'water': material('BAY_VIEW_Water', (.030, .040, .055), .24, metallic=.30),
    'glass': material('BAY_VIEW_GlassFacade', (.045, .055, .070), .18, metallic=.42),
    'glass2': material('BAY_VIEW_GlassFacadeAlt', (.068, .076, .090), .22, metallic=.34),
    'trim': material('BAY_VIEW_GrayWhiteTrim', (.220, .230, .245), .72, metallic=.10),
    'bridge': material('BAY_VIEW_BridgeSteel', (.105, .115, .130), .68, metallic=.26),
    'bridge_light': material('BAY_VIEW_BridgeLight', (.34, .35, .37), .54, emission=(.68, .70, .74), strength=.82),
    'dark_window': material('BAY_VIEW_WindowDark', (.010, .015, .024), .30, metallic=.18, emission=(.012, .018, .028), strength=.04),
    'dim_window': material('BAY_VIEW_WindowDim', (.092, .102, .120), .34, metallic=.14, emission=(.15, .17, .20), strength=.28),
    'lit_window': material('BAY_VIEW_WindowLit', (.33, .34, .36), .44, emission=(.74, .76, .80), strength=1.18),
    'moon': material('BAY_VIEW_Moon', (.45, .46, .49), .82, emission=(.58, .60, .64), strength=.48),
}

# The water and atmosphere start outside the room and stretch beyond the bridge.
box('BAY_VIEW_SkyBackdrop', (0, 18.0, 3.0), (18.0, .10, 11.0), materials['sky'], collection)
box('BAY_VIEW_WaterPlane', (0, 10.0, -.46), (14.0, 11.0, .10), materials['water'], collection)

# Layered exterior fog creates a natural fade rather than a hard opaque endpoint.
box('BAY_VIEW_FogVolume', (0, 12.5, 2.0), (14.0, 13.5, 8.0), fog_material('BAY_VIEW_FogVolumeMaterial', .020), collection)

rng = random.Random(13208)

# Modern glass apartment towers cluster on the left, echoing the supplied reference.
buildings = [
    (-3.55, 7.0, 1.48, 1.15, -4.2, 3.45, 'glass', 4),
    (-2.35, 8.2, 1.20, 1.02, -4.3, 2.65, 'glass2', 3),
    (-1.28, 9.2, 1.02, .94, -4.4, 2.10, 'glass', 3),
]
window_count = 0
lit_count = 0
for index, (cx, y, width, depth, base, top, key, columns) in enumerate(buildings):
    height = top - base
    front = y - depth / 2
    box(f'BAY_VIEW_GlassTower_{index:02d}', (cx, y, base + height / 2),
        (width, depth, height), materials[key], collection)
    # Bright structural bands and vertical mullions maintain the existing outline aesthetic.
    rows = max(10, int(height / .40))
    x_spacing = width / columns
    z_spacing = height / rows
    for row in range(1, rows):
        z = base + row * z_spacing
        box(f'BAY_VIEW_TowerBand_{index:02d}_{row:02d}',
            (cx, front - .020, z), (width + .025, .035, .018), materials['trim'], collection)
    for column_index in range(columns + 1):
        x = cx - width / 2 + column_index * x_spacing
        box(f'BAY_VIEW_TowerMullion_{index:02d}_{column_index:02d}',
            (x, front - .021, base + height / 2), (.020, .036, height), materials['trim'], collection)
    for row in range(rows):
        z = base + (row + .5) * z_spacing
        for column_index in range(columns):
            x = cx - width / 2 + (column_index + .5) * x_spacing
            roll = rng.random()
            if roll < .16:
                window_mat = materials['lit_window']
                lit_count += 1
            elif roll < .35:
                window_mat = materials['dim_window']
            else:
                window_mat = materials['dark_window']
            box(f'BAY_VIEW_TowerWindow_{index:02d}_{row:02d}_{column_index:02d}',
                (x, front - .024, z), (x_spacing * .82, .026, z_spacing * .78), window_mat, collection)
            window_count += 1
    box(f'BAY_VIEW_TowerRoof_{index:02d}', (cx, y, top + .08),
        (width + .05, depth + .04, .16), materials['bridge'], collection)

# Suspension bridge: the deck recedes rightward across the bay.
deck_start = Vector((-.35, 7.9, .34))
deck_end = Vector((5.40, 12.5, .34))
beam_between('BAY_VIEW_BridgeDeck', deck_start, deck_end, .105, materials['bridge'], collection)
beam_between('BAY_VIEW_BridgeDeckEdge', deck_start + Vector((0, 0, .10)),
             deck_end + Vector((0, 0, .10)), .026, materials['trim'], collection)

# Three towers shrink with distance, reinforcing perspective and atmospheric depth.
tower_specs = [
    (Vector((1.05, 9.02, .34)), 1.98, .46),
    (Vector((2.75, 10.38, .34)), 1.65, .39),
    (Vector((4.25, 11.58, .34)), 1.33, .32),
]
tower_tops = []
for index, (base_center, height, half_width) in enumerate(tower_specs):
    left = base_center + Vector((-half_width, 0, 0))
    right = base_center + Vector((half_width, 0, 0))
    beam_between(f'BAY_VIEW_TowerLeft_{index:02d}', left, left + Vector((0, 0, height)), .055, materials['bridge'], collection)
    beam_between(f'BAY_VIEW_TowerRight_{index:02d}', right, right + Vector((0, 0, height)), .055, materials['bridge'], collection)
    for level in (.38, .72):
        z = base_center.z + height * level
        beam_between(f'BAY_VIEW_TowerCross_{index:02d}_{int(level*100)}',
                     (left.x, left.y, z), (right.x, right.y, z), .040, materials['trim'], collection)
    # X braces make the silhouette unmistakably suspension-bridge architecture.
    beam_between(f'BAY_VIEW_TowerBraceA_{index:02d}',
                 left + Vector((0, 0, height * .10)), right + Vector((0, 0, height * .68)), .030, materials['trim'], collection)
    beam_between(f'BAY_VIEW_TowerBraceB_{index:02d}',
                 right + Vector((0, 0, height * .10)), left + Vector((0, 0, height * .68)), .030, materials['trim'], collection)
    tower_tops.append((left + Vector((0, 0, height)), right + Vector((0, 0, height))))

# Main suspension cables sag between towers and fall toward the approach decks.
def sag_points(start, end, sag, steps=18):
    points = []
    for step in range(steps + 1):
        t = step / steps
        point = start.lerp(end, t)
        point.z -= sag * 4 * t * (1 - t)
        points.append(point)
    return points

for side_index in range(2):
    near_anchor = deck_start + Vector((0, 0, .18))
    far_anchor = deck_end + Vector((0, 0, .14))
    first_top = tower_tops[0][side_index]
    last_top = tower_tops[-1][side_index]
    curve_polyline(f'BAY_VIEW_MainCable_Near_{side_index}', [near_anchor, first_top], .016, materials['trim'], collection)
    for span in range(len(tower_tops) - 1):
        curve_polyline(f'BAY_VIEW_MainCable_{side_index}_{span}',
                       sag_points(tower_tops[span][side_index], tower_tops[span + 1][side_index], .48 - span * .08),
                       .016, materials['trim'], collection)
    curve_polyline(f'BAY_VIEW_MainCable_Far_{side_index}', [last_top, far_anchor], .014, materials['trim'], collection)

# Vertical suspenders connect the cable language back to the deck without visual clutter.
for index, (base_center, height, half_width) in enumerate(tower_specs):
    for offset in (-.34, -.17, .17, .34):
        x = base_center.x + offset
        y = base_center.y + offset * .80
        cable_z = base_center.z + height * (.62 + .18 * (abs(offset) / .34))
        beam_between(f'BAY_VIEW_Suspender_{index:02d}_{offset:+.2f}',
                     (x, y, .48), (x, y, cable_z), .012, materials['trim'], collection)

# Small deck lamps provide scattered white points without changing the palette.
for index in range(16):
    t = (index + .5) / 16
    point = deck_start.lerp(deck_end, t)
    box(f'BAY_VIEW_DeckLamp_{index:02d}', (point.x, point.y, point.z + .18),
        (.035, .035, .055), materials['bridge_light'], collection)

# Decorative moon: visible upper-left, deliberately too weak to drive the room lighting.
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=.34, location=(-2.72, 13.2, 3.48))
moon = bpy.context.object
moon.name = 'BAY_VIEW_DecorativeMoon'
for owner in list(moon.users_collection):
    owner.objects.unlink(moon)
collection.objects.link(moon)
moon.scale = (1.0, .18, 1.0)
moon.data.materials.append(materials['moon'])

# Cool, low-energy exterior fill only; existing window rays remain the authored interior light.
light_data = bpy.data.lights.new('LIGHT_BayView_Fill_Data', 'AREA')
light_data.energy = 42
light_data.shape = 'RECTANGLE'
light_data.size = 9
light_data.size_y = 5
light_data.color = (.57, .61, .69)
light = bpy.data.objects.new('LIGHT_BayView_Fill', light_data)
collection.objects.link(light)
light.location = (-3.4, 5.2, 5.4)
light.rotation_euler = (Vector((0, 10.2, .8)) - light.location).to_track_quat('-Z', 'Y').to_euler()

for candidate_collection in bpy.data.collections:
    if 'RAIN' in candidate_collection.name.upper():
        candidate_collection.hide_render = True
        candidate_collection.hide_viewport = True
for obj in bpy.data.objects:
    if 'RAIN' in obj.name.upper():
        obj.hide_render = True
        obj.hide_viewport = True

scene['cathode_restyle_version'] = 'v132'
scene['cathode_bay_bridge_window_view_v132'] = True
scene['cathode_exterior_setting'] = 'foggy high-floor Bay Bridge-inspired nighttime view'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

renders = {}
camera = V121.qa_camera('CAM_QA_BayRoomView_v132', (-2.72, .18, 2.34), (.15, 9.4, 1.25), 50)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v132-bay-room-view.png'
V121.render(scene, camera, image, (1200, 800))
renders['room'] = str(image)
camera = V121.qa_camera('CAM_QA_BayExterior_v132', (-.20, 3.05, 1.72), (.40, 10.0, 1.15), 51)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v132-bay-exterior.png'
V121.render(scene, camera, image, (1200, 800))
renders['exterior'] = str(image)
if original_camera:
    scene.camera = original_camera
bpy.ops.wm.save_as_mainfile(filepath=str(out))

report = {
    'source': str(src),
    'output': str(out),
    'modern_glass_towers': len(buildings),
    'bridge_towers': len(tower_specs),
    'facade_windows': window_count,
    'lit_windows': lit_count,
    'water': True,
    'fog_volume': True,
    'decorative_moon': True,
    'rain_hidden': True,
    'renders': renders,
}
out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V132_REPORT=' + json.dumps(report))
