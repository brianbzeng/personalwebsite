"""Re-render the approved greeting with the same player materials as v156 pans.

Never changes the saved scene or existing media. --probes renders one frame.
"""
import bpy, json, os, runpy, sys

root = os.path.dirname(os.path.abspath(__file__))
source = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v149-approved-project-covers.blend')
bpy.ops.wm.open_mainfile(filepath=source)
s = bpy.context.scene
s.frame_set(1)
bpy.context.view_layer.update()
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

with open(os.path.join(root, '../public/review/v138/player.json')) as handle:
    player = json.load(handle)
changed = []
for part in player['meshes']:
    if not part['name'].startswith(('V138_', 'V148_LabelMark', 'INTERACT_RecordPlayer_Base')):
        continue
    if (part.get('rig') or '').startswith('V138_Playback_'):
        continue
    obj = bpy.data.objects.get(part['name'])
    if not obj:
        continue
    for index, item in enumerate(part['materials']):
        if item.get('sweep'):
            continue
        mat = bpy.data.materials.new('V161_' + part['name'] + '_' + str(index))
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        emit = nodes.new('ShaderNodeEmission')
        emit.inputs['Color'].default_value = (*item['color'], 1)
        emit.inputs['Strength'].default_value = 2**.3
        output = nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(emit.outputs[0], output.inputs['Surface'])
        mat.diffuse_color = (*item['color'], 1)
        mat.use_backface_culling = bool(item.get('frontSide'))
        obj.material_slots[index].link = 'OBJECT'
        obj.material_slots[index].material = mat
        changed.append({'object': obj.name, 'slot': index, 'color': item['color']})

out = os.path.join(root, 'outputs/web-room-v161')
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'material-audit.json'), 'w') as handle:
    json.dump({'source': os.path.basename(source), 'recipe': 'restore_playback_v156', 'changed': changed}, handle, indent=2)
sys.argv += ['--v149', '--greeting-consistency']
runpy.run_path(os.path.join(root, 'render_shelf_v137.py'), init_globals={'OUTPUT_DIR': out})
