"""Photo/official-diagram reconstruction of visible LP70X-style pivot and rest.
Dimensions below are photo-derived visual proportions, not factory blueprints.
No cue-control lever is created. Existing J arm, fine stylus and action stay intact.
"""
import bpy, math, os, json
from mathutils import Vector, Matrix
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert bpy.data.filepath.endswith('v141-solid-pivot-j-arm.blend')
target=os.path.join(os.path.dirname(bpy.data.filepath),'lofi-room-cathode-glm53f-city-v142-detailed-pivot-rest.blend')
assert not os.path.exists(target)
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
col=bpy.data.collections['V138_PLAYER_REVIEW'];arm=bpy.data.objects['V138_Tonearm_Rig'];yaw=bpy.data.objects['V138_Pivot_YawRig'];pivot=arm.location.copy()
gray=bpy.data.materials['V138_Gray'];metal=bpy.data.materials['V138_Metal'];dark=bpy.data.materials['V138_Contour']
socketmat=bpy.data.materials['V138_RecordLabel']
base_z=1.415
preserved={o.name:o.matrix_world.copy() for o in s.objects}
for ob in list(s.objects):
    if ob.type in ('MESH','CURVE') and not ob.hide_render and ob.name.startswith(('V138_Pivot_','V138_ArmRest_')):
        ob.hide_render=True;ob.hide_set(True);ob.name+='_RetainedV141'

def mesh(name,verts,faces,mat,parent=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mat)
    if parent:ob.parent=parent
    return ob
def link(ob,name,mat,parent=None):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob);ob.name=name;ob.data.materials.append(mat)
    if parent:ob.parent=parent
    return ob
def cyl(name,loc,r,depth,mat,parent=None,axis=Vector((0,0,1))):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=depth,location=loc)
    ob=link(bpy.context.object,name,mat,parent);ob.rotation_mode='QUATERNION';ob.rotation_quaternion=axis.to_track_quat('Z','Y')
    bevel=ob.modifiers.new('Machined rim','BEVEL');bevel.width=min(.00035,depth*.15);bevel.segments=2
    return ob
def box(name,loc,dims,mat,parent=None,rot=0,bevel=.0005):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=link(bpy.context.object,name,mat,parent)
    ob.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.rotation_euler.z=rot
    if bevel:
        mod=ob.modifiers.new('Molded rounded edge','BEVEL');mod.width=bevel;mod.segments=3
    return ob
def arc_strip(name,center,inner,outer,start,end,width,mat,parent=None,steps=40):
    # Extruded annular segment in YZ, giving an actual curved saddle cross-section.
    verts=[]
    for x in (-width/2,width/2):
        for r in (inner,outer):
            for i in range(steps+1):
                a=start+(end-start)*i/steps;verts.append(tuple(Vector(center)+Vector((x,r*math.cos(a),r*math.sin(a)))))
    n=steps+1;faces=[]
    for i in range(steps):
        faces.extend(((i,i+1,n+i+1,n+i),(2*n+i,3*n+i,3*n+i+1,2*n+i+1),
                      (i,2*n+i,2*n+i+1,i+1),(n+i,n+i+1,3*n+i+1,3*n+i)))
    faces.extend(((0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)))
    return mesh(name,verts,faces,mat,parent)
def tube(name,points,r,mat,parent=None):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2
    p=c.splines.new('POLY');p.points.add(len(points)-1)
    for v,co in zip(p.points,points):v.co=(*co,1)
    ob=bpy.data.objects.new(name,c);col.objects.link(ob);c.materials.append(mat)
    if parent:ob.parent=parent
    return ob

# Bottom-up concentric steps: silver mounting flange, black skirt, raised terraces,
# a small top rotating drum. Heights accumulate; no separated/floating circles.
tiers=[('MountFlange',.031,.0012,metal),('LowerSkirt',.0297,.0036,gray),
       ('MiddleTerrace',.0264,.0038,gray),('UpperTerrace',.0218,.0034,gray),
       ('BearingDrum',.0165,.005,gray)]
z=base_z;tier_audit=[]
for name,r,h,mat in tiers:
    ob=cyl('V138_Pivot_'+name,(pivot.x,pivot.y,z+h/2),r,h,mat)
    tier_audit.append({'part':name,'radius':r,'bottom':z,'top':z+h});z+=h
# Fine circular parting seams and interrupted molded terrace pads from the photo.
for i,(r,zoff) in enumerate(((.0295,.0047),(.0261,.0085),(.0215,.0119))):
    tube('V138_Pivot_TerraceSeam_'+str(i),[(pivot.x+r*math.cos(a*math.tau/96),pivot.y+r*math.sin(a*math.tau/96),base_z+zoff) for a in range(97)],.00017,dark)
for i,(a0,a1) in enumerate(((-2.5,-1.2),(-.8,.1),(.55,1.6))):
    verts=[];n=24
    for zz,rr in ((base_z+.0086,.0222),(base_z+.0086,.0255),(base_z+.0092,.0222),(base_z+.0092,.0255)):
        verts.extend((pivot.x+rr*math.cos(a0+(a1-a0)*j/n),pivot.y+rr*math.sin(a0+(a1-a0)*j/n),zz) for j in range(n+1))
    m=n+1;faces=[]
    for j in range(n):faces.extend(((j,j+1,m+j+1,m+j),(2*m+j,3*m+j,3*m+j+1,2*m+j+1),(j,2*m+j,2*m+j+1,j+1),(m+j,m+j+1,3*m+j+1,3*m+j)))
    faces.extend(((0,m,3*m,2*m),(m-1,3*m-1,4*m-1,2*m-1)))
    mesh('V138_Pivot_MoldedPad_'+str(i),verts,faces,gray)

# Nested gimbal: solid outer yoke, inset tilting body, distinct side bearing caps.
angle=-math.pi/6;R=Matrix.Rotation(angle,3,'Z');v=R@Vector((0,1,0))
for sign,label in ((-1,'Left'),(1,'Right')):
    box('V138_Pivot_Yoke'+label,tuple(R@Vector((0,sign*.0127,.0007))),(.0065,.0036,.028),gray,yaw,angle,.001)
box('V138_Pivot_YokeBridge',(0,0,.0145),(.0065,.029,.0045),gray,yaw,angle,.0011)
body=box('V138_Pivot_SolidDiagonalHousing',(0,0,.001),(.011,.0205,.0215),gray,arm,angle,.0015)
bpy.context.view_layer.objects.active=body
bpy.ops.object.modifier_apply(modifier=body.modifiers[0].name)
cut=cyl('V142_TemporaryBore',(0,0,0),.0036,.08,gray,arm,Vector((1,0,0)))
bpy.context.view_layer.update();mod=body.modifiers.new('Actual shaft bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
for sign,label in ((-1,'Left'),(1,'Right')):
    cyl('V138_Pivot_BearingCap'+label,tuple(v*(sign*.0152)),.0038,.0035,gray,yaw,v)
    cyl('V138_Pivot_BearingScrew'+label,tuple(v*(sign*.01705)),.0019,.00045,metal,yaw,v)
    a=v*(sign*.01732)+Vector((-.00075,0,-.00065));b=v*(sign*.01732)+Vector((.00075,0,.00065))
    tube('V138_Pivot_ScrewSlot'+label,[a,b],.00022,dark,yaw)
# Tapered shaft socket and narrow bright collar, separate from the slender tube.
verts=[];n=48;sections=[(-.016,.0045),(-.012,.0050),(-.004,.0062),(.006,.0057),(.010,.0047)]
for xx,r in sections:verts.extend((xx,r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n)) for i in range(n))
faces=[tuple(range(n-1,-1,-1)),tuple(range((len(sections)-1)*n,len(sections)*n))]
for k in range(len(sections)-1):
    for i in range(n):faces.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
mesh('V138_Pivot_ShaftSocket',verts,faces,gray,arm)
cyl('V138_Pivot_SilverCollar',(-.0165,0,0),.00465,.0015,metal,arm,Vector((1,0,0)))
# Low rear lifting shoe is distinct from the forward parked-arm clamp.
# The crossed-out hand lever is intentionally absent.
tube('V138_Pivot_LiftShoe',[(-.023,-.012,-.0039),(-.026,-.006,-.0039),(-.027,0,-.0039),(-.026,.006,-.0039),(-.023,.012,-.0039)],.0008,gray,yaw)

# Forward rest: pale socket with a recessed dark slot, short black stem,
# a molded curved cradle, taller back cheek and open retaining clamp.
rx,ry=pivot.x-.110,pivot.y
cyl('V138_ArmRest_Base',(rx,ry,base_z+.00925),.0077,.0185,socketmat)
cyl('V138_ArmRest_SocketLip',(rx,ry,base_z+.0186),.0067,.0012,socketmat)
box('V138_ArmRest_SocketSlot',(rx-.00765,ry,base_z+.004),(.0003,.0026,.005),dark,bevel=.0002)
seat_bottom=pivot.z-.0051
cyl('V138_ArmRest_Post',(rx,ry,(base_z+.0185+seat_bottom)/2),.0028,seat_bottom-base_z-.0185,gray)
arc_strip('V138_ArmRest_Cradle',(rx,ry,pivot.z),.0034,.0051,math.pi,math.tau-math.pi/6,.0072,gray)
box('V138_ArmRest_BackCheek',(rx,ry-.0043,pivot.z+.0038),(.0072,.0018,.008),gray,bevel=.00055)
arc_strip('V138_ArmRest_OpenClamp',(rx,ry-.004,pivot.z+.001),.006,.008,math.radians(85),math.radians(280),.0022,gray)
box('V138_ArmRest_ClampTab',(rx,ry-.005,pivot.z+.0087),(.0038,.003,.0022),gray,bevel=.0004)
cyl('V138_ArmRest_ClampHinge',(rx-.004,ry-.004,pivot.z-.003),.0012,.001,metal,axis=Vector((1,0,0)))

# Verify the existing geometry/action targets have not moved.
for name in ('INTERACT_RecordPlayer_Base','V138_Tonearm_Rig','V138_Pivot_YawRig','V138_Playback_Record_Rig'):
    bpy.context.view_layer.update();assert max(abs(bpy.data.objects[name].matrix_world[r][c]-preserved[name][r][c]) for r in range(4) for c in range(4))<1e-6
for frame in range(1,145):
    s.frame_set(frame);bpy.context.view_layer.update();assert (arm.matrix_world.translation-pivot).length<1e-7
out=os.path.join(ROOT,'blender/outputs/review-v142');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'assembly-audit.json'),'w') as f:json.dump({'reference':'AT-LP70X family official diagram plus Brian close-up photos','dimensionBasis':'photo-derived; no dimensioned factory pivot blueprint found','tiers':tier_audit,'crossedOutCueLeverIncluded':False,'fixedPivot':list(pivot),'clampState':'open/unlatched','preserved':'J arm, needle, record flight, contact timing, half-height plinth'},f,indent=2)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=target)
print('V142_DETAILED_ASSEMBLY_SAVED',target,flush=True)
