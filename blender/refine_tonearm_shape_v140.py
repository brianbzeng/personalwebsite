"""Reference-led pivot, continuous rear tube and fine stylus; retain v139 motion."""
import bpy, math, os, json
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert bpy.data.filepath.endswith('v139-anchored-tonearm.blend')
target=os.path.join(os.path.dirname(bpy.data.filepath),'lofi-room-cathode-glm53f-city-v140-reference-tonearm.blend')
assert not os.path.exists(target), 'Preserve previous review versions.'
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
rig=bpy.data.objects['V138_Tonearm_Rig'];pivot=rig.matrix_world.translation.copy()
collection=bpy.data.collections['V138_PLAYER_REVIEW']
metal=bpy.data.materials['V138_Metal'];gray=bpy.data.materials['V138_Gray']
dark=bpy.data.materials['V138_Contour']
old_samples=[]
for f in range(1,145):
    s.frame_set(f);old_samples.append(rig.matrix_world.copy())
s.frame_set(1)
for name in ('V138_Tonearm_PivotBase','V138_Tonearm_PivotCap','V138_Counterweight','V138_Tonearm','V138_Stylus'):
    old=bpy.data.objects[name];old.hide_render=True;old.hide_set(True)
    old.name=name+'_RetainedV139'

def mesh_obj(name,vertices,faces,mat,parent=None):
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);collection.objects.link(ob);me.materials.append(mat)
    if parent:ob.parent=parent
    return ob

def ring(name,outer,inner,z0,z1,mat):
    verts=[];n=64
    for z,r in ((z0,outer),(z0,inner),(z1,outer),(z1,inner)):
        verts.extend(tuple(pivot+Vector((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z))) for i in range(n))
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,2*n+j,2*n+i),(n+j,n+i,3*n+i,3*n+j),
                      (2*n+i,2*n+j,3*n+j,3*n+i),(j,i,n+i,n+j)))
    return mesh_obj(name,verts,faces,mat)

def tube(name,points,radius,mat,parent=None):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=3
    p=c.splines.new('POLY');p.points.add(len(points)-1)
    for dest,co in zip(p.points,points):dest.co=(*co,1)
    ob=bpy.data.objects.new(name,c);collection.objects.link(ob);c.materials.append(mat)
    if parent:ob.parent=parent
    return ob

# A shallow annular mounting flange, not a tall solid pedestal.
ring('V138_Pivot_MountFlange',.026,.014,-.044,-.040,gray)
ring('V138_Pivot_InnerRace',.0205,.015,-.040,-.029,gray)
ring('V138_Pivot_TrimRing',.0262,.0246,-.0402,-.0394,metal)
# One narrow bent diagonal strap: feet meet the ring, center cradles the tube.
axis=Vector((.5,math.sqrt(3)/2,0));side=Vector((-axis.y,axis.x,0))
profile=[(-.020,-.029),(-.014,-.027),(-.0045,-.003),(.0045,-.003),(.014,-.027),(.020,-.029)]
vertices=[]
for sign in (-1,1):
    for u,z in profile:
        vertices.append(tuple(pivot+axis*u+side*(sign*.0023)+Vector((0,0,z))))
        vertices.append(tuple(pivot+axis*u+side*(sign*.0023)+Vector((0,0,z-.003))))
n=len(profile);faces=[]
for i in range(n-1):
    a=2*i;b=a+2
    faces.extend(((a,b,b+2*n,a+2*n),(a+1,a+2*n+1,b+2*n+1,b+1),
                  (a,a+1,b+1,b),(a+2*n,b+2*n,b+2*n+1,a+2*n+1)))
faces.extend(((0,2*n,2*n+1,1),(2*n-2,2*n-1,4*n-1,4*n-2)))
bracket=mesh_obj('V138_Pivot_DiagonalBracket',vertices,faces,gray)
bevel=bracket.modifiers.new('Manufactured strap edges','BEVEL');bevel.width=.00045;bevel.segments=2

# Keep the rear portion the same diameter as the shaft, with no barrel weight.
points=[(.026,0,0),(0,0,0),(-.12,0,0),(-.13,.0006,0),(-.141,.0025,0),(-.153,.007,0),(-.18,.007,0)]
tube('V138_Tonearm',points,.0032,metal,rig)
# Cartridge body is distinct from the very fine cantilever and contact needle.
verts=[(x,y,z) for z,x0,x1,y0,y1 in [(-.0035,-.200,-.187,.003,.011),(-.009,-.198,-.190,.004,.010)] for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1))]
mesh_obj('V138_Stylus_Cartridge',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],gray,rig)
# Solve the tiny point's local height using the existing landing pose.
s.frame_set(122);q=rig.rotation_quaternion.copy()
x,y=-.202,.007
z=(1.47855-pivot.z-(q@Vector((x,y,0))).z)/(q@Vector((0,0,1))).z
tip=Vector((x,y,z));top=tip+Vector((0,0,.0009))
tube('V138_Stylus_Cantilever',[(-.194,.007,-.009),tuple(top)],.00024,metal,rig)
verts=[];n=12
for center,radius in ((tip,.000035),(top,.00018)):
    verts.extend(tuple(center+Vector((radius*math.cos(i*math.tau/n),radius*math.sin(i*math.tau/n),0))) for i in range(n))
faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
needle=mesh_obj('V138_Stylus',verts,faces,metal,rig)
for f,m in enumerate(old_samples,1):
    s.frame_set(f);bpy.context.view_layer.update()
    assert max(abs(rig.matrix_world[r][c]-m[r][c]) for r in range(4) for c in range(4))<1e-7
s.frame_set(122);bpy.context.view_layer.update()
bottom=min((needle.matrix_world@v.co).z for v in needle.data.vertices)
assert abs(bottom-1.47855)<1e-6
out=os.path.join(ROOT,'blender/outputs/review-v140');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'shape-audit.json'),'w') as f:
    json.dump({'needleTipDiameterMm':.07,'needleMaxDiameterMm':.36,'cantileverDiameterMm':.48,
               'rearTubeExtensionMm':26,'unchangedArmFrames':144,'landingHeight':bottom,
               'pivotStyle':'shallow annular housing with diagonal bent support'},f,indent=2)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=target)
print('V140_REFERENCE_TONEARM_SAVED',target,flush=True)
