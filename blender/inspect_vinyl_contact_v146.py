import bpy,json
from mathutils import Vector
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
def bounds(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    p=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
    return [[min(v[i] for v in p),max(v[i] for v in p)] for i in range(3)]
for n in ['INTERACT_Vinyl_0','INTERACT_Vinyl_1','PROJECT_VINYL_V126_Outline_0','PROJECT_VINYL_V126_Outline_1','PROJECT_VINYL_V126_Record_0']:
    o=bpy.data.objects[n]
    print(json.dumps({'name':n,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'rotation':list(o.rotation_euler),'bounds':bounds(o),'constraints':[c.type for c in o.constraints],'drivers':[(d.data_path,d.driver.expression) for d in o.animation_data.drivers] if o.animation_data else [],'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None}))
