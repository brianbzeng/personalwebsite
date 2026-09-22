"""Replace v130's brief flashes with cohesive, slow traveling contour light."""
import bpy,os,json,hashlib,sys
from mathutils import Vector
s=bpy.context.scene;s.frame_set(1)
root=os.path.dirname(os.path.abspath(__file__));out=os.path.join(root,'outputs/web-room-v131');os.makedirs(out,exist_ok=True)
target=os.path.join(root,'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v131-traveling-pulses.blend')
assert 'v130-cubby-monitor-pan' in bpy.data.filepath
assert not os.path.exists(target) or '--refine-own-version' in sys.argv, 'Preserve previous versions.'
before={o.name:tuple(v for row in o.matrix_world for v in row) for o in s.objects}

def logical_model(name,old):
    n=name.lower()
    if n.startswith(('v102_','v103_','v104_','bridge_')):return 'bridge'
    if n.startswith(('bay_','rincon_')):return 'waterfront'
    if 'project_vinyl' in n:return 'project-records'
    if 'floor_lamp' in n:return 'floor-lamp'
    if 'lamp' in n:return 'desk-lamp'
    if 'floor_plant' in n:return 'floor-plant'
    if 'desk_plant' in n:return 'desk-plant'
    if 'floorgrid' in n:return 'floor'
    if 'chair' in n:return 'chair'
    if 'cubby' in n:return 'cubby'
    if 'bed' in n:return 'bed'
    if any(k in n for k in ('shelf','book','storagebin')):return 'bookshelf'
    if 'keyboard' in n:return 'keyboard'
    if 'speakerleft' in n:return 'speaker-left'
    if 'speakerright' in n:return 'speaker-right'
    if 'mug' in n:return 'mug'
    if 'mousepad' in n:return 'desk-pad'
    if 'mouse' in n:return 'mouse'
    if 'desk' in n:return 'desk'
    if 'goldenrecord' in n:return 'golden-record-art'
    if 'pulsar' in n:return 'pulsar-art'
    if 'recordplayer' in n:return 'record-player'
    if 'rug' in n:return 'rug'
    if any(k in n for k in ('arch_shell','neon_')):return 'room-shell'
    return old.removeprefix('CATHODE_V129_QuickFlash_')

groups={};render_objects=set()
def render_members(layer):
    if layer.exclude or layer.collection.hide_render:return
    render_objects.update(o.name for o in layer.collection.objects if not o.hide_render)
    for child in layer.children:render_members(child)
render_members(bpy.context.view_layer.layer_collection)
depsgraph=bpy.context.evaluated_depsgraph_get()
for o in s.objects:
    if o.name not in render_objects:continue
    for i,slot in enumerate(o.material_slots):
        if slot.material and slot.material.name.startswith('CATHODE_V129_QuickFlash_'):
            key=logical_model(o.name,slot.material.name)
            groups.setdefault(key,[]).append((o,i))

duration=96;cycle=240;peak=.65
starts={'bridge':8,'desk-lamp':43,'chair':80,'bookshelf':160,'cubby':199,'bed':224,'desk':61,'floor-plant':179,'floor':103,'waterfront':145}
report={}
for key,slots in groups.items():
    evaluated=[o.evaluated_get(depsgraph) for o,i in slots]
    points=[o.matrix_world@Vector(p) for o in evaluated for p in o.bound_box]
    extents=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
    axis=Vector((0,0,0));axis[max(range(3),key=lambda i:extents[i])]=1
    if key in {'chair','bookshelf','floor-lamp','desk-lamp','floor-plant','desk-plant'}:axis=Vector((0,0,1))
    if key=='floor':axis=Vector((1,.35,0)).normalized()
    if key=='room-shell':axis=Vector((1,.35,.5)).normalized()
    values=[p.dot(axis) for p in points];low=min(values);span=max(values)-low
    assert span>1e-6,key
    offset=starts.get(key,int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%cycle)
    mat=bpy.data.materials.new('CATHODE_V131_Travel_'+key);mat.use_nodes=True
    n=mat.node_tree.nodes;n.clear();links=mat.node_tree.links
    def mathnode(op,a=None,b=None):
        node=n.new('ShaderNodeMath');node.operation=op
        for i,v in enumerate((a,b)):
            if v is None:continue
            if isinstance(v,(int,float)):node.inputs[i].default_value=v
            else:links.new(v,node.inputs[i])
        return node.outputs[0]
    position=n.new('ShaderNodeNewGeometry');position.name='Shared world position for whole logical model'
    dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=axis;links.new(position.outputs['Position'],dot.inputs[0])
    u=mathnode('DIVIDE',mathnode('SUBTRACT',dot.outputs['Value'],low),span)
    clock=n.new('ShaderNodeValue');clock.name='SWEEP_CLOCK'
    for frame,value in [(1,0),(241,240)]:
        clock.outputs[0].default_value=value;clock.outputs[0].keyframe_insert('default_value',frame=frame)
    action=mat.node_tree.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
                    fc.modifiers.new('CYCLES')
    elapsed=mathnode('FLOORED_MODULO',mathnode('SUBTRACT',clock.outputs[0],offset),cycle)
    progress=mathnode('SUBTRACT',mathnode('MULTIPLY',mathnode('MINIMUM',mathnode('DIVIDE',elapsed,duration),1),1.83),.18)
    distance=mathnode('SUBTRACT',progress,u)
    def smooth(a,b):
        node=n.new('ShaderNodeMapRange');node.interpolation_type='SMOOTHSTEP';node.clamp=True
        links.new(distance,node.inputs['Value']);node.inputs['From Min'].default_value=a;node.inputs['From Max'].default_value=b
        return node.outputs['Result']
    front=smooth(-.16,0);tail=mathnode('SUBTRACT',1,smooth(.05,.65))
    light=mathnode('MULTIPLY',mathnode('MULTIPLY',front,tail),peak)
    emission=n.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(.83,.89,1,1);links.new(light,emission.inputs['Strength'])
    output=n.new('ShaderNodeOutputMaterial');links.new(emission.outputs[0],output.inputs['Surface'])
    for o,i in slots:o.material_slots[i].link='OBJECT';o.material_slots[i].material=mat
    mat['logical_model']=key;mat['sweep_frames']=duration;mat['cycle_frames']=cycle;mat['start_frame']=offset+1
    mat['world_axis']=list(axis);mat['bounds_min']=low;mat['bounds_span']=span
    report[key]={'objects':sorted(set(o.name for o,i in slots)),'start':offset,'axis':list(axis),'min':low,'span':span,'duration':duration}
assert before=={o.name:tuple(v for row in o.matrix_world for v in row) for o in s.objects},'No geometry or camera changes allowed'
s.frame_set(1);s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
bpy.ops.wm.save_as_mainfile(filepath=target)
with open(os.path.join(out,'sweep-groups.json'),'w') as f:json.dump(report,f,indent=2)
# A few reduced-size checks before the full media render.
s.render.resolution_percentage=50;s.eevee.taa_render_samples=16;s.eevee.volumetric_samples=16
for frame in [1,87,111,135,159,181]:
    s.frame_set(frame);s.render.filepath=os.path.join(out,f'probe-{frame:03d}.png');bpy.ops.render.render(write_still=True)
print('V131_PREPARED',len(groups),sum(len(v) for v in groups.values()),flush=True)
