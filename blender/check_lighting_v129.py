import bpy, os, json
from mathutils import Vector
s=bpy.context.scene
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs/lighting-v129')
def bounds(o):
    points=[o.matrix_world@Vector(p) for p in o.bound_box]
    return [[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
desk=bpy.data.objects['DESK_LampShade']; tall=bpy.data.objects['FLOOR_LAMP_V129_DESK_LampShade']
shelf=bpy.data.objects['SHELF_Carcass_Cohesive']
assert bounds(tall)[1][0]>bounds(shelf)[1][1], 'Floor shade intersects bookshelf'
assert len([o for o in s.objects if o.name.startswith('LAMP_V129_') and o.type=='LIGHT'])==4
assert abs(desk.location.x+1.3)<.001
assert bpy.data.objects['CTRL_LightningSync'].animation_data is not None
report={'shadeBounds':{'desk':bounds(desk),'floor':bounds(tall)},'floorLampToBookshelfGap':bounds(tall)[1][0]-bounds(shelf)[1][1],'lights':{o.name:{'watts':o.data.energy,'softness':o.data.spot_blend} for o in s.objects if o.name.startswith('LAMP_V129_') and o.type=='LIGHT'}}
with open(os.path.join(out,'verification.json'),'w') as f:json.dump(report,f,indent=2)
camera=s.camera.copy(); camera.data=s.camera.data.copy(); s.collection.objects.link(camera)
camera.animation_data_clear(); camera.location=(-.1,-2.4,2.45)
camera.rotation_euler=(Vector((.5,2.35,1.4))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=40; camera.data.shift_y=0; s.camera=camera
s.frame_set(1); s.render.filepath=os.path.join(out,'lamps-closeup.png')
bpy.ops.render.render(write_still=True)
print('LIGHTING_CHECKS_PASS',flush=True)
