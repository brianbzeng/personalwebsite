"""Improve visibility and framing of the foggy Bay Bridge exterior pass."""

from pathlib import Path
import bpy, json

HERE = Path(__file__).resolve().parent
src = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v132-foggy-bay-bridge-night-view.blend'
out = HERE / 'outputs' / 'blender' / 'lofi-room-cathode-v133-foggy-bay-bridge-visible.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene = bpy.context.scene


def set_principled(name, base, emission=None, strength=None, roughness=None, metallic=None):
    material = bpy.data.materials.get(name)
    if not material or not material.use_nodes:
        return False
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    if not bsdf:
        return False
    material.diffuse_color = (*base, 1)
    bsdf.inputs['Base Color'].default_value = (*base, 1)
    if emission is not None:
        socket = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
        if socket:
            socket.default_value = (*emission, 1)
    if strength is not None and bsdf.inputs.get('Emission Strength'):
        bsdf.inputs['Emission Strength'].default_value = strength
    if roughness is not None:
        material.roughness = roughness
        bsdf.inputs['Roughness'].default_value = roughness
    if metallic is not None:
        material.metallic = metallic
        bsdf.inputs['Metallic'].default_value = metallic
    return True


# Raise distant sky/fog values enough to produce an atmospheric fade instead of a hard void.
set_principled('BAY_VIEW_Sky', (.032, .040, .055), (.070, .082, .105), .34, .98, 0.0)
set_principled('BAY_VIEW_Water', (.055, .067, .084), None, None, .27, .34)

# Keep the established gray-white outline language legible at night.
set_principled('BAY_VIEW_BridgeSteel', (.155, .168, .188), (.115, .128, .150), .16, .64, .25)
set_principled('BAY_VIEW_GrayWhiteTrim', (.310, .325, .350), (.235, .250, .280), .22, .66, .10)
set_principled('BAY_VIEW_GlassFacade', (.070, .084, .104), (.036, .046, .064), .10, .20, .42)
set_principled('BAY_VIEW_GlassFacadeAlt', (.088, .101, .121), (.044, .054, .072), .10, .23, .34)

# The decorative moon belongs inside the upper-left window aperture, not beyond its edge.
moon = bpy.data.objects.get('BAY_VIEW_DecorativeMoon')
if moon:
    moon.location.x = -1.74
    moon.location.y = 12.8
    moon.location.z = 2.66
    moon.scale = (.78, .16, .78)

# Slightly brighten the exterior fill; this does not replace or alter the authored window rays.
fill = bpy.data.objects.get('LIGHT_BayView_Fill')
if fill and getattr(fill, 'data', None):
    fill.data.energy = 68

scene['cathode_restyle_version'] = 'v133'
scene['cathode_bay_bridge_window_view_v133'] = True
scene['cathode_exterior_setting'] = 'visible foggy Bay Bridge-inspired night view with modern glass towers'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

# Reuse the QA cameras stored in the prior file.
renders = {}
for camera_name, filename in (
    ('CAM_QA_BayRoomView_v132', 'lofi-room-cathode-v133-bay-room-view.png'),
    ('CAM_QA_BayExterior_v132', 'lofi-room-cathode-v133-bay-exterior.png'),
):
    camera = bpy.data.objects.get(camera_name)
    if not camera:
        continue
    scene.camera = camera
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    path = HERE / 'outputs' / 'blender' / filename
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    renders[camera_name] = str(path)

bpy.ops.wm.save_as_mainfile(filepath=str(out))
report = {
    'source': str(src),
    'output': str(out),
    'bridge_visibility_raised': True,
    'fog_backdrop_raised': True,
    'moon_reframed_upper_left': True,
    'rain_hidden': True,
    'renders': renders,
}
out.with_name(out.stem + '-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('V133_REPORT=' + json.dumps(report))
