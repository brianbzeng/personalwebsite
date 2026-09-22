"""Add continuous exterior tower flange edges without changing approved cables."""
import bpy,json
from pathlib import Path
profiles=json.loads((Path(__file__).parent/'outputs/bridge-v103-tower-corners.json').read_text())
coll=bpy.data.collections.new('BRIDGE_V104_Tower_Edge_Repairs')
bpy.context.scene.collection.children.link(coll)
mat=bpy.data.materials['CATHODE_GLOBAL_BLACK_FLOWING_INK_V77.001']
matrix=bpy.data.objects['Object_2'].matrix_world.copy()
for key,edges in profiles.items():
    t,side=key.split('_');t=int(t)
    points=edges[0 if side=='L' else 1]
    for depth in [-1,1]:
        data=bpy.data.curves.new(f'V104_{key}_OuterFlange_{depth}','CURVE')
        data.dimensions='3D';data.bevel_depth=.34;data.bevel_resolution=2
        data.materials.append(mat)
        s=data.splines.new('POLY');s.points.add(len(points)-1)
        for p,(x,y) in zip(s.points,points):
            p.co=(x+(-.10 if side=='L' else .10),y,t+depth*3.10,1)
        ob=bpy.data.objects.new(data.name,data);coll.objects.link(ob);ob.matrix_world=matrix
        ob['repair']='Continuous exterior flange edge from cap to base; no source mesh changes'
print('Added',len(coll.objects),'continuous exterior tower edge paths')
