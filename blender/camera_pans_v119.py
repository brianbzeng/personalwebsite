import bpy, math, os
from mathutils import Vector

s=bpy.context.scene
home=s.camera
assert not bpy.data.objects.get('CAM_Website_Pans_v119')
camera=home.copy();camera.data=home.data.copy();camera.name='CAM_Website_Pans_v119';s.collection.objects.link(camera)
camera.rotation_mode='QUATERNION';camera.data.lens=50
start=home.matrix_world.translation.copy();start_q=home.matrix_world.to_quaternion()
screen=bpy.data.objects['INTERACT_Monitor_Screen']
center=screen.matrix_world.translation.copy()
distance=screen.dimensions.x*.94*50/36
monitor_end=Vector((center.x,center.y-screen.dimensions.y/2-distance,center.z))
paths=[
 ('Monitor',Vector((-1.6,-.2,3.6)),Vector((0,.25,1.9)),monitor_end,center),
 ('Vinyls',Vector((-.8,-.1,3.5)),Vector((.7,1.65,1.65)),Vector((1.25,1.65,1.54)),Vector((2.4,1.65,1.52))),
 ('Diploma',Vector((-2,-3,3.6)),Vector((-.1,-2.28,2.7)),Vector((.35,-2.28,2.46)),Vector((2.65,-2.28,2.46))),
]
def smooth(t): return t*t*(3-2*t)
def progress(f):
    if f<12:return 0
    if f<=84:return smooth((f-12)/72)
    if f<=108:return 1
    if f<=180:return 1-smooth((f-108)/72)
    return 0
for index,(label,p1,p2,end,target) in enumerate(paths):
    base=index*192
    end_q=(target-end).to_track_quat('-Z','Y')
    for f in range(192):
        t=progress(f);u=1-t
        camera.location=u**3*start+3*u*u*t*p1+3*u*t*t*p2+t**3*end
        camera.rotation_quaternion=start_q.slerp(end_q,t)
        camera.keyframe_insert('location',frame=base+f+1)
        camera.keyframe_insert('rotation_quaternion',frame=base+f+1)
    for offset,text in [(1,'Start'),(85,'Closeup'),(109,'Return'),(181,'Home')]:
        s.timeline_markers.new(label+' '+text,frame=base+offset)

# Fade only the selected target to black, restoring amber on the return.
groups=[
 ['INTERACT_Monitor_UniformAmberOutline_v117','INTERACT_Monitor_AmberInnerBorder_v115'],
 ['CATHODE_WIREFRAME_SHELF_VinylRack_Left','CATHODE_WIREFRAME_SHELF_VinylRack_Right']+['CATHODE_WIREFRAME_INTERACT_Vinyl_'+str(i) for i in range(7)],
 ['CATHODE_CLEAN_OUTLINE_DiplomaFrame_v109'],
]
for index,names in enumerate(groups):
    copies={}
    for name in names:
        obj=bpy.data.objects[name]
        original=obj.data.materials[0]
        if original.name not in copies:
            mat=original.copy();mat.name=original.name+'_Selected_v119';nt=mat.node_tree
            out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');link=out.inputs['Surface'].links[0];socket=link.from_socket
            mix=nt.nodes.new('ShaderNodeMixShader');mix.name='Selected target fades to black'
            black=nt.nodes.new('ShaderNodeEmission');black.inputs['Color'].default_value=(0,0,0,1)
            nt.links.remove(link);nt.links.new(socket,mix.inputs[1]);nt.links.new(black.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs['Surface'])
            for frame in range(1,577):
                local=frame-1-index*192
                value=min(1,progress(local)*2) if 0<=local<192 else 0
                mix.inputs[0].default_value=value;mix.inputs[0].keyframe_insert('default_value',frame=frame)
            copies[original.name]=mat
        obj.data.materials[0]=copies[original.name]
s.camera=camera;s.frame_start=1;s.frame_end=576;s.frame_set(1)
print('Three eight-second camera round trips created at 24 fps.')
