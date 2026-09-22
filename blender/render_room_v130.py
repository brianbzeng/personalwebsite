"""Render coherent v130 media, keeping existing website assets untouched."""
import bpy,os,json,sys
s=bpy.context.scene
revision='136' if '--v136' in sys.argv else '134' if '--v134' in sys.argv else '133' if '--v133' in sys.argv else '132' if '--v132' in sys.argv else '131' if '--v131' in sys.argv else '130'
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),f'outputs/web-room-v{revision}')
home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
monitor=bpy.data.objects['CAM_MonitorRounded_v133' if revision in ('133','134','136') else 'CAM_MonitorCubby_v130'];pan=bpy.data.objects['CAM_Website_Pans_v119']
# A non-animated camera preserves the sampled pose when the ambient clock changes.
# Rendering reevaluates animation, so overriding the animated source is insufficient.
capture=bpy.data.objects.new('V130_RENDER_CAMERA',pan.data.copy());s.collection.objects.link(capture)
capture.data.animation_data_clear()
targets={target:{slot.material.name for o in s.objects if target in o.name for slot in o.material_slots if slot.material} for target in ['Monitor','Vinyl','Diploma']}
def ease(t):return t*t*(3-2*t)
def selected(name,t):
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        fade=m.node_tree.nodes.get('Selected target fades to black')
        if not fade:continue
        fade.inputs[0].default_value=min(1,ease(t)*2) if name in targets and m.name in targets[name] else 0
def render(name,frames,cam,target=None,reverse=False,world_start=None):
    folder=os.path.join(out,name);os.makedirs(folder,exist_ok=True);s.camera=capture
    for index,frame in enumerate(frames):
        t=index/max(1,len(frames)-1)
        s.frame_set(frame)
        pose=cam.matrix_world.copy();lens=cam.data.lens;shift=cam.data.shift_y
        if world_start is not None:s.frame_set(world_start+index)
        capture.matrix_world=pose;capture.data.lens=lens;capture.data.shift_y=shift
        s.camera=capture
        selected(target,1-t if reverse else t)
        s.render.filepath=os.path.join(folder,f'{index:04d}.png')
        if not os.path.exists(s.render.filepath):bpy.ops.render.render(write_still=True)
        print('V130_FRAME',name,index,flush=True)
s.render.resolution_percentage=100;s.render.resolution_x=1920;s.render.resolution_y=1080
s.eevee.taa_render_samples=16;s.eevee.volumetric_samples=16
if '--verify-closeup' in sys.argv:
    render('verify-closeup',[277],pan,'Vinyl',True,73)
    sys.exit(0)
if revision not in ('130','133'):render('idle',list(range(1,241)),home)
render('monitor-in',list(range(1,122)),monitor,'Monitor')
render('monitor-out',list(range(121,242)),monitor,'Monitor',True)
if revision=='133':
    print('V133_MONITOR_RENDER_COMPLETE',flush=True)
    sys.exit(0)
if revision=='130':render('idle',list(range(1,241)),home)
render('vinyl-still',[277],pan,'Vinyl',True,73)
hidden=[]
for o in s.objects:
    if o.name.startswith(('INTERACT_Vinyl_','PROJECT_VINYL_V126_')) and not o.hide_render:
        hidden.append(o);o.hide_render=True
render('vinyl-background',[277],pan,'Vinyl',True,73)
for o in hidden:o.hide_render=False
for name,frames,key,reverse in [('vinyl-in',range(205,278),'Vinyl',False),('vinyl-out',range(301,374),'Vinyl',True),('diploma-in',range(397,470),'Diploma',False),('diploma-out',range(493,566),'Diploma',True)]:
    render(name,list(frames),pan,key,reverse,73 if reverse else 1)
print('V130_MEDIA_RENDER_COMPLETE',flush=True)
