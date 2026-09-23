"""Coherent camera/interactive plates, with evaluated poses and fixed decorations."""
import bpy, os, sys
from mathutils import Vector
s=bpy.context.scene;root=os.path.dirname(os.path.abspath(__file__));out=os.path.join(root,'outputs/web-room-v149' if '--v149' in sys.argv else 'outputs/web-room-v137')
out=globals().get('OUTPUT_DIR',out)
pan=bpy.data.objects['CAM_Website_Pans_v119'];home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119'];monitor=bpy.data.objects['CAM_MonitorRounded_v133']
cubbies=[bpy.data.objects['CAM_Shelf_'+n+'_v137'] for n in ('books','records','photos')]
capture=bpy.data.objects.new('V137_RENDER_CAMERA',pan.data.copy());s.collection.objects.link(capture);capture.data.animation_data_clear()
targets={key:{slot.material.name for o in s.objects if key in o.name for slot in o.material_slots if slot.material} for key in ('Monitor','Vinyl','Diploma')}
def ease(t):return t*t*(3-2*t)
def selected(key,amount):
    for m in bpy.data.materials:
        if m.use_nodes:
            fade=m.node_tree.nodes.get('Selected target fades to black')
            if fade:fade.inputs[0].default_value=amount if m.name in targets.get(key,set()) else 0
def pose(c):return (c.matrix_world.translation.copy(),c.matrix_world.to_quaternion(),c.data.lens,c.data.shift_y)
def blend(a,b,t):return (a[0].lerp(b[0],t),a[1].slerp(b[1],t),a[2]*(1-t)+b[2]*t,a[3]*(1-t)+b[3]*t)
def paint(name,index,p,ambient=73,key='Vinyl',amount=1):
    s.frame_set(ambient);capture.location=p[0];capture.rotation_mode='QUATERNION';capture.rotation_quaternion=p[1];capture.data.lens=p[2];capture.data.shift_y=p[3];s.camera=capture
    selected(key,amount);folder=os.path.join(out,name);os.makedirs(folder,exist_ok=True);s.render.filepath=os.path.join(folder,f'{index:04d}.png')
    refresh_probe='--refresh-probes' in sys.argv and (name.endswith(('-still','-background')) or name=='greeting-probe')
    refresh_greeting='--refresh-greeting' in sys.argv and name in ('greeting-probe','idle')
    if refresh_probe or refresh_greeting or not os.path.exists(s.render.filepath):bpy.ops.render.render(write_still=True)
    print('V137_FRAME',name,index,flush=True)
def authored(name,frames,c,key=None,reverse=False):
    for i,f in enumerate(frames):
        s.frame_set(f);p=pose(c);t=i/max(1,len(frames)-1)
        paint(name,i,p,f if c==monitor or c==home else (73 if reverse else 1)+i,key,min(1,ease(1-t if reverse else t)*2))
def shelfpan(name,reverse=False):
    for i in range(73):
        f=301+i if reverse else 205+i;s.frame_set(f);t=ease(i/72);old=pose(pan)
        s.frame_set(277);oldend=pose(pan);newend=pose(cubbies[1]);weight=1-t if reverse else t
        p=(old[0]+(newend[0]-oldend[0])*weight,old[1].slerp(newend[1],weight),old[2],old[3]*(1-weight))
        paint(name,i,p,(73 if reverse else 1)+i,'Vinyl',min(1,ease(1-i/72 if reverse else i/72)*2))
def hide_active(cubby):
    names=[]
    if cubby==1:
        for slot in range(2,7):names += [f'INTERACT_Vinyl_{slot}',f'PROJECT_VINYL_V126_Outline_{slot}',f'PROJECT_VINYL_V126_Record_{slot}']
        if '--live-player' in sys.argv:names += globals().get('LIVE_PLAYER_NAMES',[])
    elif cubby==0:names=['BOOK_Mid_9','CATHODE_WIREFRAME_BOOK_Mid_9']
    obs=[bpy.data.objects[n] for n in names if not bpy.data.objects[n].hide_render]
    for o in obs:o.hide_render=True
    return obs
s.render.resolution_percentage=100;s.render.resolution_x=1920;s.render.resolution_y=1080;s.eevee.taa_render_samples=16;s.eevee.volumetric_samples=16
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
if '--greeting-consistency' in sys.argv:
    s.frame_set(1);paint('greeting-probe',0,pose(home),1,None,0)
    if '--probes' not in sys.argv:
        authored('idle',list(range(1,241)),home)
        authored('monitor-in',list(range(1,122)),monitor,'Monitor')
        authored('monitor-out',list(range(121,242)),monitor,'Monitor',True)
        authored('diploma-in',list(range(397,470)),pan,'Diploma')
        authored('diploma-out',list(range(493,566)),pan,'Diploma',True)
    print('V161_GREETING_RENDER_COMPLETE',flush=True);sys.exit(0)
if '--greeting-only' in sys.argv:
    s.frame_set(1);paint('greeting-probe',0,pose(home),1,None,0)
    if '--probes' not in sys.argv:authored('idle',list(range(1,241)),home)
    print('V149_GREETING_RENDER_COMPLETE',flush=True);sys.exit(0)
for j,name in enumerate(('books','vinyl','photos')):
    if '--vinyl-only' in sys.argv and j!=1:continue
    s.frame_set(73);p=pose(cubbies[j]);paint(name+'-still',0,p)
    hidden=hide_active(j);paint(name+'-background',0,p)
    for o in hidden:o.hide_render=False
if '--vinyl-only' not in sys.argv:paint('greeting-probe',0,pose(home),1,None,0)
if '--probes' in sys.argv:sys.exit(0)
# Small shelf moves first: front-facing, only vertical travel between cubbies.
for a,b in ((1,0),(0,1),(1,2),(2,1)):
    for i in range(37):paint(f'shelf-{a}-{b}',i,blend(pose(cubbies[a]),pose(cubbies[b]),ease(i/36)))
shelfpan('vinyl-in');shelfpan('vinyl-out',True)
if '--vinyl-only' in sys.argv:sys.exit(0)
authored('idle',list(range(1,241)),home)
authored('monitor-in',list(range(1,122)),monitor,'Monitor')
authored('monitor-out',list(range(121,242)),monitor,'Monitor',True)
authored('diploma-in',list(range(397,470)),pan,'Diploma')
authored('diploma-out',list(range(493,566)),pan,'Diploma',True)
print('V137_RENDER_COMPLETE',flush=True)
