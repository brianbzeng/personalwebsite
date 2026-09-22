"""Render a new scene version, then an occlusion-correct floor interaction mask."""
import bpy,os
folder=os.path.dirname(os.path.abspath(__file__))
exec(compile(open(os.path.join(folder,'prepare_calm_room_v127.py')).read(),os.path.join(folder,'prepare_calm_room_v127.py'),'exec'))
saved=os.path.join(folder,'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v127-calm-room.blend')
s.camera=home;s.frame_set(1)
if not os.path.exists(saved):bpy.ops.wm.save_as_mainfile(filepath=saved)
render('idle',range(1,241),home)
render('monitor-in',range(1,122),camera)
render('monitor-out',range(121,242),camera)
render('vinyl-still',[277],pan)
hidden=[]
for o in s.objects:
    if (o.name.startswith('INTERACT_Vinyl_') or o.name.startswith('PROJECT_VINYL_V126_')) and not o.hide_render:
        hidden.append(o);o.hide_render=True
render('vinyl-background',[277],pan)
for o in hidden:o.hide_render=False
for name,frames in [('vinyl-in',range(205,278)),('vinyl-out',range(301,374)),('diploma-in',range(397,470)),('diploma-out',range(493,566))]:render(name,frames,pan)

exec(compile(open(os.path.join(folder,'render_floor_mask_v127.py')).read(),os.path.join(folder,'render_floor_mask_v127.py'),'exec'))
print('CALM_ROOM_COMPLETE',flush=True)
