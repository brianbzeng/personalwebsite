"""Calmer room lighting and a lower-right monitor approach, based on v126."""
import bpy, math, os, json
from mathutils import Vector
s=bpy.context.scene
root=os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs','web-room-v127')
os.makedirs(root,exist_ok=True)
home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
pan=bpy.data.objects['CAM_Website_Pans_v119']

# Keep continuous black contours; soften only the traveling white glint.
changed_materials=[]
for material in bpy.data.materials:
    if not material.use_nodes:continue
    nodes=material.node_tree.nodes
    clock=nodes.get('FLOW_TIME')
    if not clock:continue
    gain=nodes.get('Math.005')
    if gain and gain.type=='MATH':gain.inputs[1].default_value=.52
    # One slow sweep per ten seconds rather than two harsh sweeps.
    if material.node_tree.animation_data and material.node_tree.animation_data.action:
        material.node_tree.animation_data.action=material.node_tree.animation_data.action.copy()
        for layer in material.node_tree.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in list(bag.fcurves):
                        if fc.data_path==clock.outputs[0].path_from_id('default_value'):bag.fcurves.remove(fc)
    driver=clock.outputs[0].driver_add('default_value').driver
    driver.expression='2*pi*(frame-1)/240'
    changed_materials.append(material.name)

# Refine room contours without undoing hand-cleaned bridge geometry or the
# physical vinyl outlines that were just matched to the browser.
changed_widths=[]
for o in s.objects:
    if o.name.startswith('CATHODE_') and not o.hide_render and not any(x in o.name for x in ['Vinyl','Diploma','Monitor']):
        for mod in o.modifiers:
            if mod.type=='WIREFRAME':
                old=mod.thickness;mod.thickness*=.6;changed_widths.append((o.name,old,mod.thickness))

# The original lightning action is intact: its primary flash is at frame 128.
# Preserve it and export the FULL 240-frame cycle this time.
lightning=bpy.data.objects['CTRL_LightningSync']
lightning['web_loop_frames']=240

camera=pan.copy();camera.data=pan.data.copy();camera.name='CAM_MonitorDive_v127';s.collection.objects.link(camera)
camera.animation_data_clear();camera.data.animation_data_clear();camera.rotation_mode='QUATERNION'
camera.data.lens=50
start=home.location.copy();startq=home.rotation_euler.to_quaternion()
end=Vector((0,.9710854888,1.4028000832))
screen=Vector((0,2.47590017,1.40280008))
waypoint=Vector((1.35,-1.6,2.85))
wayq=(Vector((0,3.8,1.8))-waypoint).to_track_quat('-Z','Y')
endq=(screen-end).to_track_quat('-Z','Y')
c1=start+(waypoint-start)*.67+Vector((2.2,-.7,-1.6))
c2=waypoint-(end-waypoint).normalized()*1.5
def ease(t):return t*t*(3-2*t)
def pose(t):
    if t<=.54:
        u=ease(t/.54);v=1-u
        position=v**3*start+3*v*v*u*c1+3*v*u*u*c2+u**3*waypoint
        rotation=startq.slerp(wayq,u)
    else:
        u=ease((t-.54)/.46)
        position=waypoint.lerp(end,u);rotation=wayq.slerp(endq,u)
    return position,rotation
for frame in range(1,242):
    t=(frame-1)/120 if frame<=121 else (241-frame)/120
    camera.location,camera.rotation_quaternion=pose(t)
    camera.data.shift_y=-.0175*(1-ease(t))
    camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_quaternion',frame=frame);camera.data.keyframe_insert('shift_y',frame=frame)
camera['approach_description']='Lower-right dive, then straight descending approach; no sideways window-look excursion.'
camera['waypoint']=list(waypoint);camera['approach_frames']=121

target_materials={target:{m.name for o in s.objects if target in o.name for m in getattr(o.data,'materials',[]) if m} for target in ['Monitor','Vinyl','Diploma']}

def selected_factor(name,frame):
    # Keep each selected target black on approach, amber in the greeting.
    for material in bpy.data.materials:
        if not material.use_nodes:continue
        n=material.node_tree.nodes.get('Selected target fades to black')
        if not n:continue
        n.inputs[0].driver_remove('default_value')
        factor=0
        if name.startswith('monitor') and material.name in target_materials['Monitor']:
            t=(241-frame)/120 if name=='monitor-out' else (frame-1)/120
            factor=min(1,ease(max(0,min(1,t)))*2)
        elif name.startswith('vinyl') and material.name in target_materials['Vinyl']:
            t=(373-frame)/72 if name=='vinyl-out' else (frame-205)/72
            factor=min(1,ease(max(0,min(1,t)))*2)
        elif name.startswith('diploma') and material.name in target_materials['Diploma']:
            t=(565-frame)/72 if name=='diploma-out' else (frame-397)/72
            factor=min(1,ease(max(0,min(1,t)))*2)
        n.inputs[0].default_value=factor

s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.eevee.taa_render_samples=32;s.eevee.volumetric_samples=32
def render(name,frames,cam):
    s.camera=cam;folder=os.path.join(root,name);os.makedirs(folder,exist_ok=True)
    for index,frame in enumerate(frames):
        s.frame_set(frame);selected_factor(name,frame)
        s.render.filepath=os.path.join(folder,f'{index:04d}.png')
        if not os.path.exists(s.render.filepath):bpy.ops.render.render(write_still=True)
        print('CALM_FRAME',name,index,flush=True)

with open(os.path.join(root,'changes.json'),'w') as f:json.dump({'materials':changed_materials,'widths':changed_widths,'lightningFrame':128,'loopFrames':240,'waypoint':list(waypoint)},f)
print('CALM_ROOM_PREPARED',flush=True)
