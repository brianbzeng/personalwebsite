"""Render the existing visible contours as a web hover mask; never save the scene."""
import bpy,os,json
s=bpy.context.scene
def emission(name,value):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission')
    e.inputs[0].default_value=(value,value,value,1);m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
    return m
black=emission('HOVER_MASK_BLACK',0);white=emission('HOVER_MASK_WHITE',1)
outlined=[];hidden=[]
for o in s.objects:
    if o.hide_render:continue
    mats=list(getattr(o.data,'materials',[]))
    volume=any(n.inputs['Volume'].is_linked and not n.inputs['Surface'].is_linked for m in mats if m and m.use_nodes for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
    glass='glass' in o.name.lower() or any(m and 'glass' in m.name.lower() for m in mats)
    if o.type in {'LIGHT','VOLUME'} or volume or o.name.startswith('FX_') or glass:
        o.hide_render=True;hidden.append(o.name);continue
    if not hasattr(o.data,'materials'):continue
    # Only existing contour geometry/materials, never all polygon edges or fills.
    wire=any(m.type=='WIREFRAME' for m in o.modifiers)
    replacements=[]
    for m in mats:
        amber=m and ('Amber' in m.name or (m.use_nodes and m.node_tree.nodes.get('Selected target fades to black')))
        ink=m and (('FLOWING_INK' in m.name) or m.name.startswith('BRIDGE_') and ('Outline' in m.name or 'Outside_Only' in m.name))
        contour=any(t in o.name.lower() for t in ['outline','alignededges','contour'])
        light=(wire or ink or contour) and not amber
        replacements.append(white if light else black)
    if white in replacements:outlined.append(o.name)
    o.data=o.data.copy();o.data.materials.clear()
    for m in replacements or [black]:o.data.materials.append(m)
world=bpy.data.worlds.new('HOVER_MASK_WORLD');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1);s.world=world
s.render.use_compositing=False;s.render.film_transparent=False
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119'];s.frame_set(1)
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
root=os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs/web-room-v128');os.makedirs(root,exist_ok=True)
s.render.filepath=os.path.join(root,'room-visible.png');bpy.ops.render.render(write_still=True)
with open(os.path.join(root,'mask-audit.json'),'w') as f:json.dump({'outlined':outlined,'hidden':hidden},f,indent=2)
print('ROOM_HOVER_MASK_COMPLETE',len(outlined),flush=True)
