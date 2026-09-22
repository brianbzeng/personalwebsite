"""One outside contour shell per physical suspender, not per imported mesh part."""
import bpy, math, json
from mathutils import Vector
coll=bpy.data.collections.new('BRIDGE_V103_Suspender_Outside_Only')
bpy.context.scene.collection.children.link(coll)
mat=bpy.data.materials['BRIDGE_V103_Animated_Outside_Only']
matrix=bpy.data.objects['Object_2'].matrix_world.copy()
bvh=bpy.app.driver_namespace['v103_bvh']
ids=sorted({(o.name.split('_')[1],int(o.name.rsplit('_',1)[1])) for o in bpy.data.objects
            if o.name.startswith('V102_') and '_Suspender_' in o.name and not o.hide_render})
report=[]
for side,z in ids:
    mid=min((137,837,1537,2237,2937),key=lambda t:abs(t-z))
    top=-650+math.sqrt(250000-(z-mid)**2)
    deck=bvh.ray_cast(Vector((82,-180,z)),Vector((0,1,0)),60)[0]
    bottom=deck.y if deck else -147
    y=(top-147)/2
    xlo,xhi=(54,74) if side=='L' else (91,111)
    lo=bvh.ray_cast(Vector((xlo,y,z)),Vector((1,0,0)),20)[0]
    hi=bvh.ray_cast(Vector((xhi,y,z)),Vector((-1,0,0)),20)[0]
    if not lo or not hi or not 4.8<hi.x-lo.x<5.2:
        for step in range(max(1,int((-130-top)*4))):
            yy=top+step*.25
            a=bvh.ray_cast(Vector((xlo,yy,z)),Vector((1,0,0)),20)[0]
            b=bvh.ray_cast(Vector((xhi,yy,z)),Vector((-1,0,0)),20)[0]
            if a and b and 4.9<b.x-a.x<5.1:
                lo,hi=a,b
                break
    if not lo or not hi or not 4.8<hi.x-lo.x<5.2:
        report.append({'side':side,'z':z,'status':'not a clear exposed cylinder; original retained'})
        continue
    x=(lo.x+hi.x)/2;rad=(hi.x-lo.x)/2+.32
    verts=[];faces=[];n=64
    for yy in [top,bottom]:
        for k in range(n):
            a=k*2*math.pi/n
            verts.append((x+rad*math.cos(a),yy,z+rad*math.sin(a)))
    for k in range(n):
        j=(k+1)%n
        faces.append((k,j,j+n,k+n))
    mesh=bpy.data.meshes.new(f'V103_{side}_Suspender_{z:04d}_Shell')
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(mesh.name,mesh);coll.objects.link(ob)
    ob.matrix_world=matrix;mesh.materials.append(mat)
    ob['physical_cable_id']=f'{side}_{z}'
    for old in bpy.data.objects:
        if old.name.startswith('V102_'+side+'_') and old.name.endswith(f'Suspender_{z:04d}'):
            old.hide_set(True);old.hide_render=True
    report.append({'side':side,'z':z,'status':'single outside shell','center_x':x,'radius':rad})
bpy.app.driver_namespace['v103_hanger_report']=report
print('Replaced',len(coll.objects),'suspenders;',len(ids)-len(coll.objects),'retained for further inspection')
print([r for r in report if 'retained' in r['status']])
