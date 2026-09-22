import os
exec(compile(open(os.path.join(os.path.dirname(__file__),'prepare_calm_room_v127.py')).read(),os.path.join(os.path.dirname(__file__),'prepare_calm_room_v127.py'),'exec'))
s.render.resolution_percentage=60
render('monitor-check',[1,25,49,65,81,97,113,121],camera)
render('lighting-check',[1,60,127,128,130,132,180,240],home)
print('CALM_PREVIEW_COMPLETE',flush=True)
