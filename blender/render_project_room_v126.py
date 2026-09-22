"""Re-render from a new project-labeled scene without overwriting v121."""
import bpy, os
folder=os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(folder,'build_project_vinyls_v126.py')).read(),os.path.join(folder,'build_project_vinyls_v126.py'),'exec'))
# Reuse the approved camera paths exactly; no new camera interpretation.
source=open(os.path.join(folder,'render_release_room_v125.py')).read()
setup=source.split('# Export only')[0].replace("'web-room-v125'","'web-room-v126'")
exec(compile(setup,os.path.join(folder,'render_release_room_v125.py'),'exec'))
saved=os.path.join(folder,'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v126-project-vinyls.blend')
if os.path.exists(saved):raise RuntimeError('Refusing to overwrite the saved project-vinyl scene')
s.camera=home;s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=saved)
render('vinyl-still',[277],camera)
hidden=[]
for o in s.objects:
    if (o.name.startswith('INTERACT_Vinyl_') or o.name.startswith('PROJECT_VINYL_V126_')) and not o.hide_render:
        hidden.append(o);o.hide_render=True
render('vinyl-background',[277],camera)
for o in hidden:o.hide_render=False
for name,frames in [('vinyl-in',range(205,278)),('vinyl-out',range(301,374)),('diploma-in',range(397,470)),('diploma-out',range(493,566)),('monitor-in',range(13,86)),('monitor-out',range(109,182))]:render(name,frames,camera)
for m in bpy.data.materials:
    if m.use_nodes:
        n=m.node_tree.nodes.get('Selected target fades to black')
        if n:n.inputs[0].driver_remove('default_value');n.inputs[0].default_value=0
render('idle',range(1,121),home)
print('PROJECT_ROOM_COMPLETE',flush=True)
