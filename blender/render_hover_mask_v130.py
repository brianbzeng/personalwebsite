"""Effective material-slot mask for v130, including shorter lamp. Never save."""
import bpy,os,json,sys
s=bpy.context.scene
def ink(name,value):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear()
    e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(value,value,value,1)
    o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],o.inputs['Surface']);return m
black=ink('V130_MASK_BLACK',0);white=ink('V130_MASK_WHITE',1)
black_culled=black.copy();black_culled.use_backface_culling=True
white_culled=white.copy();white_culled.use_backface_culling=True
outlined=[]
for o in s.objects:
    if o.hide_render:continue
    mats=[slot.material for slot in o.material_slots]
    volume=any(n.inputs['Volume'].is_linked and not n.inputs['Surface'].is_linked for m in mats if m and m.use_nodes for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
    glass='glass' in o.name.lower() or any(m and 'glass' in m.name.lower() for m in mats)
    if o.type in {'LIGHT','VOLUME'} or volume or o.name.startswith('FX_') or glass:o.hide_render=True;continue
    if not hasattr(o.data,'materials'):continue
    wire=any(mod.type=='WIREFRAME' for mod in o.modifiers)
    replacements=[]
    for m in mats:
        amber=m and ('Amber' in m.name or (m.use_nodes and m.node_tree.nodes.get('Selected target fades to black')))
        flowing=m and ('FLOWING_INK' in m.name or m.name.startswith(('CATHODE_V129_QuickFlash_','CATHODE_V131_Travel_')) or m.name.startswith('BRIDGE_') and ('Outline' in m.name or 'Outside_Only' in m.name))
        contour=any(t in o.name.lower() for t in ['outline','alignededges','contour'])
        replacement=white if (wire or flowing or contour) and not amber else black
        if m and m.use_backface_culling:
            replacement=white_culled if replacement==white else black_culled
        replacements.append(replacement)
    if white in replacements or white_culled in replacements:outlined.append(o.name)
    o.data=o.data.copy()
    for slot in o.material_slots:slot.link='DATA'
    o.data.materials.clear()
    for m in replacements or [black]:o.data.materials.append(m)
world=bpy.data.worlds.new('V130_MASK_WORLD');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1);s.world=world
s.render.use_compositing=False;s.render.film_transparent=False
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119'];s.frame_set(1)
s.render.resolution_percentage=100;s.render.resolution_x=1920;s.render.resolution_y=1080
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
folder=os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs/web-room-v149' if '--v149' in sys.argv else 'outputs/web-room-v136' if '--v136' in sys.argv else 'outputs/web-room-v132' if '--v132' in sys.argv else 'outputs/web-room-v130')
s.render.filepath=os.path.join(folder,'room-visible.png');bpy.ops.render.render(write_still=True)
with open(os.path.join(folder,'mask-audit.json'),'w') as f:json.dump({'outlined':outlined},f)
print('V130_MASK_COMPLETE',len(outlined),flush=True)
