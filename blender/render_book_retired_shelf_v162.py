"""Re-render the original v155 vinyl pans with the book outline retired.

Run with Blender --background --python <this file>. Source scenes and existing
published media are never overwritten. Completed frames resume in the private
web-room-v162-shelf output directory. Requires the render_shelf_v137.py
RENDER_SEQUENCES filter hook; camera paths and timing remain in that renderer.
"""
import bpy
import json
import os
import runpy
import sys

root = os.path.dirname(os.path.abspath(__file__))
renderer = os.path.join(root, 'render_shelf_v137.py')
with open(renderer, encoding='utf-8') as handle:
    assert 'RENDER_SEQUENCES' in handle.read(), 'Install the sequence filter before rendering'

source = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v155-seamless-player.blend')
bpy.ops.wm.open_mainfile(filepath=source)
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()

# Match seamless_player_v155.py's post-save render-only state exactly. Do not
# repeat its material setup or sleeve translations: those are already saved.
for name in ('V138_Playback_Record_Rig', 'V138_Playback_Sleeve_Rig'):
    for obj in bpy.data.objects[name].children_recursive:
        obj.hide_render = True
for name in ('V138_Tonearm_Rig', 'V138_Pivot_YawRig'):
    obj = bpy.data.objects[name]
    basis = obj.matrix_basis.copy()
    obj.animation_data_clear()
    obj.matrix_basis = basis
for name in ('INTERACT_Vinyl_6', 'PROJECT_VINYL_V126_Outline_6', 'PROJECT_VINYL_V126_Record_6'):
    bpy.data.objects[name].hide_render = False

# Only this book becomes decorative. The shared pulse material remains intact
# on the monitor, vinyls, diploma and every other active object.
wire = bpy.data.objects['CATHODE_WIREFRAME_BOOK_Mid_9']
neighbor = bpy.data.objects['CATHODE_WIREFRAME_BOOK_Mid_8']
assert neighbor.active_material and neighbor.active_material != wire.active_material
before = [slot.material.name if slot.material else None for slot in wire.material_slots]
for slot in wire.material_slots:
    slot.link = 'OBJECT'
    slot.material = neighbor.active_material

out = os.path.join(root, 'outputs/web-room-v162-shelf')
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'material-audit.json'), 'w', encoding='utf-8') as handle:
    json.dump({
        'source': os.path.basename(source),
        'object': wire.name,
        'previousMaterials': before,
        'replacementMaterial': neighbor.active_material.name,
        'sequences': ['vinyl-in', 'vinyl-out'],
        'framesPerSequence': 73,
        'savedSource': False,
    }, handle, indent=2)

sys.argv += ['--vinyl-only']
helper = runpy.run_path(os.path.join(root, 'render_book_outline_patch.py'))
runpy.run_path(renderer, init_globals={
    'OUTPUT_DIR': out,
    'RENDER_SEQUENCES': {'vinyl-in', 'vinyl-out'},
    'RENDER_FRAME': helper['patch_renderer'](os.path.join(root, 'outputs/web-room-v155')),
})
