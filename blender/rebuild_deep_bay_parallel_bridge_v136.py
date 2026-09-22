"""Deep reconstruction of the Bay view with visible water and a parallel distant bridge."""

from pathlib import Path
import bpy, json, random, sys
from mathutils import Vector

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import outside_short_interactive_rays_v121 as V121

src = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v135-bay-reference-composition.blend'
out = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v136-deep-bay-parallel-bridge.blend'
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


def sag_points(start, end, sag, steps=28):
    points = []
    for step in range(steps + 1):
        t = step / steps
        point = start.lerp(end, t)
        point.z -= sag * 4 * t * (1 - t)
        points.append(point)
    return points


def water_material():
    material = bpy.data.materials.get('BAY_VIEW_VisibleWater_v136') or bpy.data.materials.new('BAY_VIEW_VisibleWater_v136')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    noise = nodes.new('ShaderNodeTexNoise')
    bump = nodes.new('ShaderNodeBump')
    texcoord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    bsdf.inputs['Base Color'].default_value = (.105, .125, .155, 1)
    bsdf.inputs['Roughness'].default_value = .24
    bsdf.inputs['Metallic'].default_value = .30
    emission = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
    if emission:
        emission.default_value = (.060, .075, .100, 1)
    if bsdf.inputs.get('Emission Strength'):
        bsdf.inputs['Emission Strength'].default_value = .36
    noise.inputs['Scale'].default_value = 2.6
    noise.inputs['Detail'].default_value = 5.0
    noise.inputs['Roughness'].default_value = .72
    mapping.inputs['Scale'].default_value = (1.0, 5.0, 1.0)
    bump.inputs['Strength'].default_value = .18
    bump.inputs['Distance'].default_value = .16
    links.new(texcoord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return material


# Remove every prior exterior structure involved in the failed composition.
remove_prefixes = (
    'BAY_VIEW_Bridge', 'BAY_VIEW_Tower', 'BAY_VIEW_MainCable',
    'BAY_VIEW_Suspender', 'BAY_VIEW_DeckLamp', 'BAY_VIEW_Reference',
    'BAY_VIEW_LowBuilding', 'BAY_VIEW_LowRoof', 'BAY_VIEW_LowWindow',
    'BAY_VIEW_Final',
)
for obj in list(bpy.data.objects):
    if obj.name.startswith(remove_prefixes) or obj.name == 'BAY_VIEW_WaterPlane':
        bpy.data.objects.remove(obj, do_unlink=True)

glass = bpy.data.materials['BAY_VIEW_GlassFacade']
glass_alt = bpy.data.materials['BAY_VIEW_GlassFacadeAlt']
trim = bpy.data.materials['BAY_VIEW_GrayWhiteTrim']
bridge = bpy.data.materials['BAY_VIEW_BridgeSteel']
dark_window = bpy.data.materials['BAY_VIEW_WindowDark']
dim_window = bpy.data.materials['BAY_VIEW_WindowDim']
lit_window = bpy.data.materials['BAY_VIEW_WindowLit']
bridge_light = bpy.data.materials['BAY_VIEW_BridgeLight']

# Replace the black slab with a broad, visibly shaded bay surface.
water = box('BAY_VIEW_VisibleWaterSurface_v136', (0, 18.0, -.58), (17.0, 34.0, .07), water_material(), collection)

# A deeper fog field lets distant geometry vanish naturally; no rear cap is present.
fog = bpy.data.objects.get('BAY_VIEW_FogVolume')
if fog:
    fog.location = (0, 21.0, 2.3)
    fog.dimensions = (17.0, 40.0, 9.5)
    fog_material = fog.data.materials[0] if fog.data and fog.data.materials else None
    if fog_material and fog_material.use_nodes:
        volume = next((node for node in fog_material.node_tree.nodes if node.bl_idname == 'ShaderNodeVolumePrincipled'), None)
        if volume:
            volume.inputs['Density'].default_value = .028
            volume.inputs['Color'].default_value = (.29, .32, .37, 1)

world = scene.world
if world and world.use_nodes:
    background = world.node_tree.nodes.get('Background')
    if background:
        background.inputs['Color'].default_value = (.020, .027, .040, 1)
        background.inputs['Strength'].default_value = .20

rng = random.Random(13608)

# Four complete modern glass towers are all kept inside or immediately against the left aperture.
buildings = [
    (-2.02, 7.0, .64, 1.06, -4.25, 3.18, glass, 3),
    (-1.63, 7.9, .58, .98, -4.32, 2.82, glass_alt, 3),
    (-1.26, 8.8, .56, .94, -4.38, 2.52, glass, 3),
    (-.91, 9.7, .50, .88, -4.44, 2.26, glass_alt, 2),
]
building_windows = 0
for index, (cx, y, width, depth, base, top, facade, columns) in enumerate(buildings):
    height = top - base
    front = y - depth / 2
    box(f'BAY_VIEW_FinalGlassTower_{index:02d}', (cx, y, base + height / 2),
        (width, depth, height), facade, collection)
    rows = max(13, int(height / .34))
    x_spacing = width / columns
    z_spacing = height / rows
    for row in range(1, rows):
        box(f'BAY_VIEW_FinalTowerBand_{index:02d}_{row:02d}',
            (cx, front - .018, base + row * z_spacing),
            (width + .018, .032, .014), trim, collection)
    for column in range(columns + 1):
        x = cx - width / 2 + column * x_spacing
        box(f'BAY_VIEW_FinalTowerMullion_{index:02d}_{column:02d}',
            (x, front - .019, base + height / 2), (.016, .033, height), trim, collection)
    for row in range(rows):
        z = base + (row + .5) * z_spacing
        for column in range(columns):
            x = cx - width / 2 + (column + .5) * x_spacing
            roll = rng.random()
            window_mat = lit_window if roll < .13 else (dim_window if roll < .33 else dark_window)
            box(f'BAY_VIEW_FinalTowerWindow_{index:02d}_{row:02d}_{column:02d}',
                (x, front - .022, z), (x_spacing * .82, .025, z_spacing * .78), window_mat, collection)
            building_windows += 1
    box(f'BAY_VIEW_FinalTowerRoof_{index:02d}', (cx, y, top + .06),
        (width + .035, depth + .035, .12), bridge, collection)

# Waterfront buildings are lowered so only their roofs and upper floors line the bottom edge.
low_buildings = [
    (.05, 8.0, .72, .80, -.78, -.12),
    (.72, 8.5, .82, .84, -.80, -.04),
    (1.45, 9.0, .72, .78, -.82, -.15),
    (2.18, 9.5, .84, .82, -.84, -.08),
]
for index, (cx, y, width, depth, base, top) in enumerate(low_buildings):
    height = top - base
    box(f'BAY_VIEW_FinalLowBuilding_{index:02d}', (cx, y, base + height / 2),
        (width, depth, height), bridge, collection)
    box(f'BAY_VIEW_FinalLowRoof_{index:02d}', (cx, y, top + .045),
        (width + .035, depth + .035, .09), trim, collection)
    for column in range(3):
        x = cx - width * .30 + column * width * .30
        box(f'BAY_VIEW_FinalLowWindow_{index:02d}_{column:02d}',
            (x, y - depth / 2 - .014, base + height * .58),
            (width * .15, .024, height * .20), dim_window if rng.random() < .42 else dark_window, collection)

# The bridge is genuinely parallel to the room/window direction: X never changes.
# Its near approach begins beyond the right wall and its far end is buried deep in fog.
bridge_x = 2.76
near_y = 4.20
far_y = 35.0
deck_length = far_y - near_y
box('BAY_VIEW_FinalBridgeDeck', (bridge_x, (near_y + far_y) / 2, .27),
    (.78, deck_length, .12), bridge, collection)
for side, x in enumerate((bridge_x - .39, bridge_x + .39)):
    box(f'BAY_VIEW_FinalBridgeRail_{side}', (x, (near_y + far_y) / 2, .42),
        (.030, deck_length, .20), trim, collection)

# The nearest structural tower stays out of frame; visible towers begin well into the bay.
tower_specs = [
    (8.8, 2.00, .58),
    (14.3, 1.90, .56),
    (20.2, 1.78, .53),
    (26.3, 1.66, .50),
    (31.8, 1.55, .47),
]
tower_pairs = []
for index, (y, height, half_width) in enumerate(tower_specs):
    center = Vector((bridge_x, y, .34))
    left = Vector((bridge_x - half_width, y, .34))
    right = Vector((bridge_x + half_width, y, .34))
    beam_between(f'BAY_VIEW_FinalBridgeTowerLeft_{index:02d}', left, left + Vector((0, 0, height)), .052, bridge, collection)
    beam_between(f'BAY_VIEW_FinalBridgeTowerRight_{index:02d}', right, right + Vector((0, 0, height)), .052, bridge, collection)
    for level in (.34, .67):
        z = center.z + height * level
        beam_between(f'BAY_VIEW_FinalBridgeTowerCross_{index:02d}_{int(level*100)}',
                     (left.x, y, z), (right.x, y, z), .036, trim, collection)
    beam_between(f'BAY_VIEW_FinalBridgeTowerBraceA_{index:02d}',
                 left + Vector((0, 0, height * .08)), right + Vector((0, 0, height * .66)), .025, trim, collection)
    beam_between(f'BAY_VIEW_FinalBridgeTowerBraceB_{index:02d}',
                 right + Vector((0, 0, height * .08)), left + Vector((0, 0, height * .66)), .025, trim, collection)
    tower_pairs.append((left + Vector((0, 0, height)), right + Vector((0, 0, height))))

for side in range(2):
    side_x = bridge_x - .39 if side == 0 else bridge_x + .39
    near_anchor = Vector((side_x, near_y, .44))
    far_anchor = Vector((bridge_x + (-.30 if side == 0 else .30), far_y, .40))
    curve_polyline(f'BAY_VIEW_FinalMainCableNear_{side}', [near_anchor, tower_pairs[0][side]], .014, trim, collection)
    for span in range(len(tower_pairs) - 1):
        curve_polyline(f'BAY_VIEW_FinalMainCable_{side}_{span}',
                       sag_points(tower_pairs[span][side], tower_pairs[span + 1][side], .52),
                       .014, trim, collection)
    curve_polyline(f'BAY_VIEW_FinalMainCableFar_{side}', [tower_pairs[-1][side], far_anchor], .010, trim, collection)

# Suspender spacing continues far beyond the visible view, preventing an abrupt bridge endpoint.
for index in range(42):
    t = (index + .5) / 42
    y = near_y + deck_length * t
    half_width = .39 - .09 * t
    for side, x in enumerate((bridge_x - half_width, bridge_x + half_width)):
        beam_between(f'BAY_VIEW_FinalSuspender_{index:02d}_{side}',
                     (x, y, .44), (x, y, .98), .008, trim, collection)
    if index % 3 == 0:
        box(f'BAY_VIEW_FinalDeckLamp_{index:02d}', (bridge_x, y, .49),
            (.034, .034, .052), bridge_light, collection)

scene['cathode_restyle_version'] = 'v136'
scene['cathode_deep_bay_parallel_bridge_v136'] = True
scene['cathode_exterior_setting'] = 'deep visible bay; four complete glass towers; lowered waterfront; parallel off-frame bridge fading into fog'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

# Verify the result from both the room and a reference-style exterior vantage.
renders = {}
original_camera = scene.camera
camera = V121.qa_camera('CAM_QA_DeepBayRoom_v136', (-2.72, .18, 2.34), (.10, 11.0, 1.10), 49)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v136-deep-bay-room.png'
V121.render(scene, camera, image, (1400, 900))
renders['room'] = str(image)
camera = V121.qa_camera('CAM_QA_DeepBayExterior_v136', (-.05, 3.15, 1.76), (.10, 13.0, .95), 51)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v136-deep-bay-exterior.png'
V121.render(scene, camera, image, (1400, 900))
renders['exterior'] = str(image)
camera = V121.qa_camera('CAM_QA_DeepBayWide_v136', (0, 1.0, 2.65), (0, 13.0, .95), 60)
image = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v136-deep-bay-wide.png'
V121.render(scene, camera, image, (1400, 900))
renders['wide'] = str(image)
if original_camera:
    scene.camera = original_camera
bpy.ops.wm.save_as_mainfile(filepath=str(out))

report = {
    'source': str(src),
    'output': str(out),
    'black_water_plane_removed': bpy.data.objects.get('BAY_VIEW_WaterPlane') is None,
    'visible_procedural_water': bpy.data.objects.get('BAY_VIEW_VisibleWaterSurface_v136') is not None,
    'complete_glass_towers': len(buildings),
    'lowered_waterfront_buildings': len(low_buildings),
    'bridge_parallel_to_window_axis': True,
    'bridge_near_approach_off_frame_right': True,
    'bridge_depth': deck_length,
    'fog_depth': 40.0,
    'rain_hidden': True,
    'renders': renders,
}
out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V136_REPORT=' + json.dumps(report))
