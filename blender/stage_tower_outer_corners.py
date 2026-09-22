"""Replace tower-overlapping guides; source meshes and old curves stay intact."""
import bpy, json
from pathlib import Path
from mathutils import Vector

TOWERS = (487,1187,1887,2587)
root = Path(__file__).parent / 'outputs'
profiles = json.loads((root / 'bridge-v103-tower-corners.json').read_text())
collection = bpy.data.collections.new('BRIDGE_V103_Outer_Corners')
bpy.context.scene.collection.children.link(collection)
material = bpy.data.materials['CATHODE_GLOBAL_BLACK_FLOWING_INK_V77.001']
matrix = bpy.data.objects['Object_2'].matrix_world.copy()

def curve(name, runs, radius=.34):
    runs = [p for p in runs if len(p)>1]
    if not runs: return
    data=bpy.data.curves.new(name,'CURVE')
    data.dimensions='3D'; data.bevel_depth=radius; data.bevel_resolution=2
    data.materials.append(material)
    for run in runs:
        s=data.splines.new('POLY'); s.points.add(len(run)-1)
        for p,co in zip(s.points,run):p.co=(*co,1)
    ob=bpy.data.objects.new(name,data); collection.objects.link(ob)
    ob.matrix_world=matrix
    return ob

def in_tower(p):
    return 44<p.x<121 and -303<p.y<-27 and min(abs(p.z-t) for t in TOWERS)<13

sources=[o for o in bpy.data.objects if o.name.startswith('V102_') and o.type=='CURVE' and not o.hide_render]
for old in sources:
    runs=[]
    structural=old.name=='V102_Structural_No_Hanger_Overlap'
    for s in old.data.splines:
        points=[p.co.to_3d() for p in s.points]
        if s.use_cyclic_u and points:points.append(points[0])
        run=[]
        for a,b in zip(points,points[1:]):
            d=b-a
            # Preserve cross-bracing and cap details; remove longitudinal groove guides.
            discard=(in_tower((a+b)/2) and abs(d.y)>max(abs(d.x),abs(d.z))*3) if structural else (in_tower(a) or in_tower(b))
            if discard:
                if len(run)>1:runs.append(run)
                run=[]
            else:
                if not run:run.append(tuple(a))
                run.append(tuple(b))
        if len(run)>1:runs.append(run)
    curve(old.name.replace('V102_','V103_'),runs)
    old.hide_set(True);old.hide_render=True

# Treat each upright as a single tapered member, ignoring its inset seams.
# The inner edge changes taper near y=-117; small joint notches aren't traced.
for key,edges in profiles.items():
    t,side=key.split('_');t=int(t)
    for edge_index,edge in enumerate(edges):
        outer=(side=='L' and edge_index==0) or (side=='R' and edge_index==1)
        def interpolate(y):
            for (x0,y0),(x1,y1) in zip(edge,edge[1:]):
                if y0<=y<=y1:return x0+(x1-x0)*(y-y0)/(y1-y0)
            return edge[-1][0]
        ys=[-282.5,-260,-230,-200,-170,-150,-117,-90,-60,-27.5]
        if outer:
            xy=[(interpolate(y),y) for y in ys]
        else:
            # Uninterrupted taper follows the main flange edge, not circular sockets,
            # inset seams, or small attachment tabs.
            anchors=[(interpolate(y),y) for y in [-280,-260,-150,-117,-60,-27.5]]
            xy=anchors
        for depth in [-1,1]:
            z=t+depth*(3 if outer else 5)
            run=[(x,y,z+depth*.12) for x,y in xy]
            ob=curve(f'V103_Tower_{t}_{side}_Corner_{edge_index}_{depth}',[run])
            ob['outline_intent']='Single outer longitudinal corner; no internal groove outlines'
print('Created',len(collection.objects),'outline objects; original bridge meshes untouched.')
