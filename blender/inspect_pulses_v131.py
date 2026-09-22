import bpy,json,os
from mathutils import Vector
groups={}
for o in bpy.context.scene.objects:
    if o.hide_render:continue
    for slot in o.material_slots:
        m=slot.material
        if m and m.name.startswith('CATHODE_V129_QuickFlash_'):
            points=[o.matrix_world@Vector(p) for p in o.bound_box]
            groups.setdefault(m.name,[]).append({'name':o.name,'bounds':[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]})
out=os.path.join(os.path.dirname(__file__),'outputs/web-room-v131');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'source-groups.json'),'w') as f:json.dump(groups,f,indent=2)
print(json.dumps(groups),flush=True)
