"""Preserve v154; seat every sleeve and render plates for one live player."""
import bpy, os, json, runpy, sys
from mathutils import Matrix
root=os.path.dirname(os.path.abspath(__file__))
s=bpy.context.scene
assert bpy.data.filepath.endswith('v154-seated-first-photo.blend')
target=bpy.data.filepath.replace('v154-seated-first-photo','v155-seamless-player')
assert not os.path.exists(target), 'Preserve previous authoring versions'
s.frame_set(1)
# Move whole independent sleeve assemblies, never a child a second time.
for slot in range(7):
    for name in (f'INTERACT_Vinyl_{slot}',f'PROJECT_VINYL_V126_Outline_{slot}',f'PROJECT_VINYL_V126_Record_{slot}'):
        obj=bpy.data.objects.get(name)
        if obj:obj.matrix_world=Matrix.Translation((-.01,0,0))@obj.matrix_world
with open(os.path.join(root,'../public/review/v138/player.json')) as f:model=json.load(f)
parts=[p for p in model['meshes'] if p['name'].startswith(('V138_','V148_LabelMark','INTERACT_RecordPlayer_Base')) and not (p.get('rig') or '').startswith('V138_Playback_')]
# A readable flat base matches the site's gray treatment. Keep the authored
# animated contour materials; only formerly unlit-black surfaces change.
for part in parts:
    obj=bpy.data.objects.get(part['name'])
    if not obj:continue
    for index,item in enumerate(part['materials']):
        if item.get('sweep'):continue
        mat=bpy.data.materials.new('V155_'+part['name']+'_'+str(index));mat.use_nodes=True
        nodes=mat.node_tree.nodes;nodes.clear()
        emit=nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(*item['color'],1)
        # Match Standard/sRGB exposure -0.3 used by the room renderer.
        emit.inputs['Strength'].default_value=2**.3
        output=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(emit.outputs[0],output.inputs['Surface'])
        mat.diffuse_color=(*item['color'],1);mat.use_backface_culling=bool(item.get('frontSide'))
        obj.material_slots[index].link='OBJECT';obj.material_slots[index].material=mat
bpy.ops.wm.save_as_mainfile(filepath=target)
# Release-only staging: park the arm; no duplicate floating playback props.
for name in ('V138_Playback_Record_Rig','V138_Playback_Sleeve_Rig'):
    for obj in bpy.data.objects[name].children_recursive:obj.hide_render=True
for name in ('V138_Tonearm_Rig','V138_Pivot_YawRig'):
    obj=bpy.data.objects[name];basis=obj.matrix_basis.copy();obj.animation_data_clear();obj.matrix_basis=basis
for name in ('INTERACT_Vinyl_6','PROJECT_VINYL_V126_Outline_6','PROJECT_VINYL_V126_Record_6'):bpy.data.objects[name].hide_render=False
sys.argv += ['--vinyl-only','--live-player']
runpy.run_path(os.path.join(root,'render_shelf_v137.py'),init_globals={'OUTPUT_DIR':os.path.join(root,'outputs/web-room-v155'),'LIVE_PLAYER_NAMES':[p['name'] for p in parts]})
