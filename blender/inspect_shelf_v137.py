import bpy, json, os
from mathutils import Vector
s=bpy.context.scene
s.frame_set(277)
rows=[]
for o in s.objects:
    if any(w in o.name.lower() for w in ['shelf','book','vinyl']):
        if o.type in ('MESH','CURVE','EMPTY'):
            bb=[o.matrix_world@Vector(v) for v in o.bound_box] if o.type!='EMPTY' else [o.matrix_world.translation]
            rows.append(dict(name=o.name,type=o.type,hidden=o.hide_render,parent=o.parent.name if o.parent else None,min=[min(v[k] for v in bb) for k in range(3)],max=[max(v[k] for v in bb) for k in range(3)],location=list(o.location),rotation=list(o.rotation_euler),scale=list(o.scale)))
out=os.path.join(os.path.dirname(__file__),'outputs/shelf-v137-qa/scene-audit.json')
with open(out,'w') as f:json.dump(rows,f,indent=2)
for frame in (1,205,277,301,373):
    s.frame_set(frame);c=bpy.data.objects['CAM_Website_Pans_v119']
    print('CAMERA',frame,list(c.matrix_world.translation),list(c.matrix_world.to_quaternion()),c.data.lens,c.data.shift_y,flush=True)
for n in ('INTERACT_Vinyl_0','INTERACT_Vinyl_1'):
    o=bpy.data.objects[n]; print('VINYL',n,list(o.matrix_world.translation),list(o.rotation_euler),o.parent.name if o.parent else None,flush=True)
print('AUDIT_DONE',out,flush=True)
