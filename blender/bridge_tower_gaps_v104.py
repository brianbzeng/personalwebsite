"""Bridge aligned, facing endpoints only on existing tower longitudinal edges."""
import bpy
from mathutils import Vector
old=bpy.data.objects['V102_Structural_No_Hanger_Overlap']
coll=bpy.data.collections['BRIDGE_V104_Tower_Edge_Repairs']
ends=[]
for s in old.data.splines:
    ps=[p.co.to_3d() for p in s.points]
    if s.use_cyclic_u or len(ps)<2:continue
    for p,q in [(ps[0],ps[1]),(ps[-1],ps[-2])]:
        d=p-q
        if d.length<.01:continue
        d.normalize()
        t=min([487,1187,1887,2587],key=lambda t:abs(p.z-t))
        if abs(p.z-t)>12 or not -303<p.y<-27:continue
        if not (45<p.x<70 or 94<p.x<120):continue
        if abs(d.y)<.985:continue
        ends.append((p,d,t))
pairs=[]
for i,(p,d,t) in enumerate(ends):
    for j,(q,e,u) in enumerate(ends[i+1:],i+1):
        v=q-p;length=v.length
        if t!=u or not 1<length<45:continue
        n=v/length
        if n.dot(d)<.995 or (-n).dot(e)<.995:continue
        if (v-d*v.dot(d)).length>.35:continue
        if (v-e*v.dot(e)).length>.35:continue
        pairs.append((length,i,j))
used=set();accepted=[]
for length,i,j in sorted(pairs):
    if i in used or j in used:continue
    p,d,t=ends[i];q,e,u=ends[j]
    data=bpy.data.curves.new(f'V104_Tower_{t}_Gap_{len(accepted):03d}','CURVE')
    data.dimensions='3D';data.bevel_depth=old.data.bevel_depth;data.bevel_resolution=2
    data.materials.append(old.data.materials[0])
    s=data.splines.new('POLY');s.points.add(1)
    s.points[0].co=(*(p-d*.10),1);s.points[1].co=(*(q-e*.10),1)
    ob=bpy.data.objects.new(data.name,data);coll.objects.link(ob);ob.matrix_world=old.matrix_world
    ob['gap_length']=length;ob['repair']='Aligned existing endpoints; no additional parallel edge'
    accepted.append((t,round(length,3),tuple(p),tuple(q)));used.update([i,j])
bpy.app.driver_namespace['v104_gap_repairs']=accepted
print('Reconnected',len(accepted),'aligned gaps')
