"""Non-destructive lighting study. Run against v127; never updates web media."""
import bpy, bmesh, os, math, json, sys
from mathutils import Vector, Matrix

s = bpy.context.scene
root = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(root, 'outputs/lighting-v129')
os.makedirs(out, exist_ok=True)
target = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v129-lamp-lighting-preview.blend')
assert 'v127-calm-room' in bpy.data.filepath, 'Start from the latest approved source.'
assert not os.path.exists(target) or '--refine-own-preview' in sys.argv, 'Never overwrite a previous study.'

lamp_names = ['DESK_LampBase', 'DESK_LampArm', 'DESK_LampShade', 'DESK_LampBulb', 'CATHODE_ASSEMBLY_OUTLINE_DeskLamp']
new_lamp = []
for name in lamp_names:
    src = bpy.data.objects[name]
    o = src.copy(); o.data = src.data.copy(); o.animation_data_clear()
    o.name = 'FLOOR_LAMP_V129_' + name
    s.collection.objects.link(o)
    assert o.type == 'MESH', (name, o.type)
    for v in o.data.vertices:
        p = src.matrix_world @ v.co
        z = .06 + (p.z-.82)*1.2 if p.z <= .875 else (1.98+(p.z-1.4)*1.35 if p.z >= 1.255 else .126+(p.z-.875)*(1.78425-.126)/.38)
        v.co = ((p.x-1.43)*1.30+2.30, (p.y-2.45)*1.30+2.35, z)
    o.matrix_world = Matrix.Identity(4)
    new_lamp.append(o)

delta = Vector((-2.73, .03, 0))
moved = []
for o in s.objects:
    if o.name in lamp_names or o.name == 'LIGHT_DeskLamp':
        o.location += delta; moved.append(o.name)
    elif o.name.startswith(('DESK_Plant', 'CATHODE_WIREFRAME_DESK_Plant')):
        o.location -= delta; moved.append(o.name)

# Open the shades; their side walls still cast shadows and shape the light.
for o in [bpy.data.objects['DESK_LampShade'], bpy.data.objects['FLOOR_LAMP_V129_DESK_LampShade']]:
    o.data = o.data.copy()
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z)>.95], context='FACES')
    bm.to_mesh(o.data); bm.free()

# Clone only indoor fills. Retain a dim graphic base plus real diffuse lighting.
changed = {}; indoor = []
for o in s.objects:
    if o.type not in {'MESH','CURVE'} or o.hide_render or not o.data.materials: continue
    if o.name.startswith(('GLM_', 'CATHODE_', 'INTERACT_', 'PROJECT_')): continue
    for slot in o.material_slots:
        m = slot.material
        if not m or not m.name.startswith('CATH_ROOM') or not m.use_nodes: continue
        if m.name not in changed:
            copy = m.copy(); copy.name = m.name+'_LAMP_FILL_V129'
            nodes=copy.node_tree.nodes; links=copy.node_tree.links
            emission=next((n for n in nodes if n.type=='EMISSION'),None)
            output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
            if emission:
                emission.inputs['Strength'].default_value *= .55
                diffuse=nodes.new('ShaderNodeBsdfDiffuse'); diffuse.name='Soft real lamp response'
                diffuse.inputs['Color'].default_value=(.28,.28,.28,1)
                diffuse.inputs['Roughness'].default_value=1
                add=nodes.new('ShaderNodeAddShader')
                links.new(emission.outputs[0],add.inputs[0]); links.new(diffuse.outputs[0],add.inputs[1]); links.new(add.outputs[0],output.inputs['Surface'])
            changed[m.name]=copy
        slot.link='OBJECT'; slot.material=changed[m.name]; indoor.append(o.name)

def soft_spot(name, position, up, energy, angle):
    data=bpy.data.lights.new(name,'SPOT'); data.energy=energy
    data.color=(1,.89,.74); data.spot_size=math.radians(angle); data.spot_blend=.85; data.shadow_soft_size=.11
    o=bpy.data.objects.new(name,data); s.collection.objects.link(o); o.location=position
    if up: o.rotation_euler=(math.pi,0,0)
    return o

soft_spot('LAMP_V129_Desk_Down',(-1.30,2.40,1.245),False,48,100)
soft_spot('LAMP_V129_Desk_Up',(-1.30,2.48,1.525),True,25,110)
soft_spot('LAMP_V129_Floor_Down',(2.30,2.25,1.775),False,125,100)
soft_spot('LAMP_V129_Floor_Up',(2.30,2.35,2.146),True,65,110)
# Legacy weather beams were authored for self-lit surfaces. Keep their fog
# illumination, but prevent the newly reactive furniture from blowing out.
for o in s.objects:
    if o.type=='LIGHT' and any(k in o.name for k in ['Lightning','StormFlash']):
        o.data.diffuse_factor=.015
bulb=bpy.data.materials.new('LAMP_V129_WarmDiffuser'); bulb.use_nodes=True
n=bulb.node_tree.nodes; n.clear(); e=n.new('ShaderNodeEmission'); e.inputs['Color'].default_value=(1,.87,.68,1); e.inputs['Strength'].default_value=1.4
output=n.new('ShaderNodeOutputMaterial'); bulb.node_tree.links.new(e.outputs[0],output.inputs['Surface'])
for name in ['DESK_LampBulb','FLOOR_LAMP_V129_DESK_LampBulb']:
    bpy.data.objects[name].data.materials.clear(); bpy.data.objects[name].data.materials.append(bulb)

# Keep ordinary edges black at rest, then briefly flash whole logical objects.
# Five-frame falloffs at 24 fps replace the slow spatial travelling stripe.
groups={}; assigned=[]
def group_for(name):
    name=name.lower()
    for key in ['plant','lamp','shelf','bed','chair','floor','wall','cubby']:
        if key in name: return key
    if any(key in name for key in ['desk','keyboard','speaker','mouse','trackpad']): return 'desk'
    if 'book' in name: return 'shelf'
    return 'architecture'
for o in s.objects:
    if o.hide_render or not hasattr(o.data,'materials'): continue
    for slot in o.material_slots:
        m=slot.material
        if not m or not m.use_nodes or not m.node_tree.nodes.get('FLOW_TIME'): continue
        if any(x in o.name for x in ['Vinyl','Diploma','Monitor']) or o.name.startswith('GLM_'): continue
        group=group_for(o.name)
        if group not in groups:
            mat=bpy.data.materials.new('CATHODE_V129_QuickFlash_'+group); mat.use_nodes=True
            nodes=mat.node_tree.nodes; nodes.clear(); e=nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value=(.83,.89,1,1)
            output=nodes.new('ShaderNodeOutputMaterial'); mat.node_tree.links.new(e.outputs[0],output.inputs['Surface'])
            offset=[8,43,80,160,199,224,61,179,103,145,29,212][len(groups)%12]
            # Baked keys work even when Blender's script auto-execution is disabled.
            for frame, value in [(1,0),(offset-2,0),(offset+1,.65),(offset+4,0),(241,0)]:
                e.inputs['Strength'].default_value=value
                e.inputs['Strength'].keyframe_insert('default_value',frame=frame)
            action=mat.node_tree.animation_data.action
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fc in bag.fcurves:
                            fc.modifiers.new('CYCLES')
            groups[group]=mat
        slot.link='OBJECT'; slot.material=groups[group]; assigned.append(o.name)

# This saved study is an idle preview, not a playback of the pan timeline.
# Keep approach controllers in v127; per-clip exporters set this factor themselves.
for m in bpy.data.materials:
    if not m.use_nodes: continue
    fade=m.node_tree.nodes.get('Selected target fades to black')
    if fade:
        fade.inputs[0].driver_remove('default_value')
        fade.inputs[0].default_value=0
s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']; s.frame_set(1)
s.render.resolution_x=1920; s.render.resolution_y=1080; s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
s.eevee.taa_render_samples=32; s.eevee.volumetric_samples=32
with open(os.path.join(out,'audit.json'),'w') as f: json.dump({'moved':moved,'floorLamp':[o.name for o in new_lamp],'reactiveObjects':sorted(set(indoor)),'flashGroups':list(groups),'flashObjects':len(assigned),'source':bpy.data.filepath},f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=target)
s.render.filepath=os.path.join(out,'greeting.png'); bpy.ops.render.render(write_still=True)
print('LAMP_PREVIEW_READY',flush=True)
