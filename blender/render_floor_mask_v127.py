"""Occluded floor-only mask; loaded from v127, never saved over the scene."""
import bpy,os
s=bpy.context.scene
def emission(name,value):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission')
    e.inputs[0].default_value=(value,value,value,1);m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
    return m
black=emission('MASK_BLACK',0);white=emission('MASK_WHITE',1)
grid=bpy.data.objects['CATHODE_WIREFRAME_ARCH_FloorGrid_Cohesive_v10']
for o in s.objects:
    if o.hide_render:continue
    mats=getattr(o.data,'materials',[])
    volume=any(n.inputs['Volume'].is_linked and not n.inputs['Surface'].is_linked for m in mats if m and m.use_nodes for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
    if o.type in {'LIGHT','VOLUME'} or volume or o.name.startswith('FX_'):
        o.hide_render=True;continue
    if hasattr(o.data,'materials'):
        o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(white if o==grid else black)
world=bpy.data.worlds.new('MASK_WORLD');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(0,0,0,1);s.world=world
s.render.use_compositing=False;s.render.film_transparent=False
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119'];s.frame_set(1)
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.render.filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs/web-room-v127/floor-visible.png')
bpy.ops.render.render(write_still=True)
print('FLOOR_MASK_COMPLETE',flush=True)
