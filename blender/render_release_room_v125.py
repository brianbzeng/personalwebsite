"""Full-resolution release assets. Runs in background, never saves over the scene."""
import bpy, os, json, math
from mathutils import Vector
s=bpy.context.scene
camera=bpy.data.objects['CAM_Website_Pans_v119']
home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
home.data=home.data.copy(); home.data.shift_y=-.0175
camera.data=camera.data.copy()
poses=[]
for start,target in [(1,Vector((0,2.47590017,1.40280008))),(193,Vector((2.4,1.65,1.52))),(385,Vector((2.615,-2.28,2.1)))]:
    first_target=home.location+(home.rotation_euler.to_quaternion()@Vector((0,0,-1)))*(target-home.location).length
    for frame in range(start,start+192):
        s.frame_set(frame); f=frame-start
        t=0 if f<12 else (f-12)/72 if f<=84 else 1 if f<=108 else 1-(f-108)/72 if f<=180 else 0
        t=t*t*(3-2*t); aim=first_target.lerp(target,t)
        if start==1: aim=aim.lerp(Vector((0,7,2.2)),.64*math.sin(math.pi*t)**6)
        poses.append((frame,(aim-camera.location).to_track_quat('-Z','Y'),-.0175*(1-t)))
for frame,rotation,shift in poses:
    camera.rotation_quaternion=rotation; camera.keyframe_insert('rotation_quaternion',frame=frame)
    camera.data.shift_y=shift; camera.data.keyframe_insert('shift_y',frame=frame)
s.render.resolution_x=1920; s.render.resolution_y=1080; s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
s.eevee.taa_render_samples=32; s.eevee.volumetric_samples=32
root=os.path.join(os.path.dirname(__file__),'outputs','web-room-v125')
os.makedirs(root,exist_ok=True)
def render(name,frames,cam):
    s.camera=cam; folder=os.path.join(root,name); os.makedirs(folder,exist_ok=True)
    for i,f in enumerate(frames):
        s.frame_set(f); s.render.filepath=os.path.join(folder,f'{i:04d}.png')
        if not os.path.exists(s.render.filepath): bpy.ops.render.render(write_still=True)
        print('RELEASE_FRAME',name,i,flush=True)

# Export only the 7 tiny sleeves, in Blender world coordinates. The holder stays
# in the background plate. Geometry is unchanged, including the leaning sleeve.
s.frame_set(277); objects=[]
for i in range(7):
    o=bpy.data.objects[f'INTERACT_Vinyl_{i}']; o.data.calc_loop_triangles()
    origin=o.matrix_world.translation.copy()
    positions=[round(c,7) for v in o.data.vertices for c in (o.matrix_world@v.co-origin)]
    indices=[v for tri in o.data.loop_triangles for v in tri.vertices]
    objects.append({'name':o.name,'origin':list(origin),'positions':positions,'indices':indices})
occluders=[]
for name in ['SHELF_VinylRack_Left','SHELF_VinylRack_Right']:
    o=bpy.data.objects[name];o.data.calc_loop_triangles()
    occluders.append({'positions':[round(c,7) for v in o.data.vertices for c in (o.matrix_world@v.co)],'indices':[v for tri in o.data.loop_triangles for v in tri.vertices]})
with open(os.path.join(root,'vinyl-geometry.json'),'w') as f:
    json.dump({'objects':objects,'occluders':occluders,'camera':[1.1,1.65,1.54],'target':[2.4,1.65,1.52],'verticalFov':math.degrees(2*math.atan(36/50/2*9/16)),'hoverTravel':.085},f)
hidden=[]
for o in s.objects:
    if o.name.startswith(('INTERACT_Vinyl_','CATHODE_WIREFRAME_INTERACT_Vinyl_')) and not o.hide_render:
        hidden.append(o); o.hide_render=True
render('vinyl-background',[277],camera)
for o in hidden:o.hide_render=False
for name,frames in [('vinyl-in',range(205,278)),('vinyl-out',range(301,374)),('diploma-in',range(397,470)),('diploma-out',range(493,566)),('monitor-in',range(13,86)),('monitor-out',range(109,182))]:
    render(name,frames,camera)
for m in bpy.data.materials:
    if m.use_nodes:
        n=m.node_tree.nodes.get('Selected target fades to black')
        if n:n.inputs[0].driver_remove('default_value');n.inputs[0].default_value=0
render('idle',range(1,121),home)
print('RELEASE_COMPLETE',flush=True)
