"""Solid diagonal bearing, J arm, half-height plinth; new approval version only."""
import bpy, math, os, json
from mathutils import Vector, Matrix, Quaternion
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert bpy.data.filepath.endswith('v140-reference-tonearm.blend')
target=os.path.join(os.path.dirname(bpy.data.filepath),'lofi-room-cathode-glm53f-city-v141-solid-pivot-j-arm.blend')
assert not os.path.exists(target)
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
col=bpy.data.collections['V138_PLAYER_REVIEW']
gray=bpy.data.materials['V138_Gray'];metal=bpy.data.materials['V138_Metal'];dark=bpy.data.materials['V138_Contour']
rig=bpy.data.objects['V138_Tonearm_Rig'];record=bpy.data.objects['V138_Playback_Record_Rig']
old_arm=rig.location.copy();drop=.0475
base=bpy.data.objects['INTERACT_RecordPlayer_Base'];base_bottom=1.3775;old_height=base.dimensions.z
base.scale.z*=.5;base.location.z=base_bottom+old_height/4
# Rebuild base contours at constant line thickness, rather than scaling tubes flat.
oldwire=bpy.data.objects['CATHODE_WIREFRAME_INTERACT_RecordPlayer_Base'];oldwire.hide_render=True;oldwire.hide_set(True)
base_top=base_bottom+old_height/2

def retire(ob):
    ob.hide_render=True;ob.hide_set(True);ob.name+='_RetainedV140'
def tube(name,points,radius,mat,parent=None):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=3
    sp=c.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,c);col.objects.link(ob);c.materials.append(mat)
    if parent:ob.parent=parent
    return ob
def link(ob,name,mat,parent=None):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob);ob.name=name;ob.data.materials.append(mat)
    if parent:ob.parent=parent
    return ob
def cyl(name,loc,radius,depth,mat,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius,depth=depth,location=loc)
    return link(bpy.context.object,name,mat,parent)
def box(name,loc,dims,mat,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=link(bpy.context.object,name,mat,parent)
    ob.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return ob
bpy.context.view_layer.update()
corners=[base.matrix_world@Vector(p) for p in base.bound_box]
edges=((0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7))
for i,(a,b) in enumerate(edges):tube('V138_PlayerBase_Edge_'+str(i),[corners[a],corners[b]],.0007,dark)

# Lower flight endpoint smoothly, preserving the stationary extraction phase.
record_poses=[]
for frame in range(1,145):
    s.frame_set(frame);record_poses.append((record.location.copy(),record.rotation_quaternion.copy(),record.scale.copy()))
record.animation_data_clear()
for frame,(pos,q,scale) in enumerate(record_poses,1):
    t=max(0,min(1,(frame-42)/46));pos.z-=drop*t*t*(3-2*t)
    record.location=pos;record.rotation_quaternion=q;record.scale=scale
    record.keyframe_insert('location',frame=frame);record.keyframe_insert('rotation_quaternion',frame=frame);record.keyframe_insert('scale',frame=frame)
s.frame_set(1)
platter=bpy.data.objects['V138_Player_Platter']
platter_top=1.475-drop
platter.dimensions.z=platter_top-base_top;platter.location.z=(platter_top+base_top)/2
for name in ('V138_Platter_Rim','V138_Spindle'):bpy.data.objects[name].location.z-=drop

# Shorter pedestal: a closed stepped mounting plate and a solid bearing body.
for ob in list(s.objects):
    if ob.name.startswith('V138_Pivot_') and not ob.hide_render:retire(ob)
pivot=old_arm-Vector((0,0,drop));rig.location=pivot
cyl('V138_Pivot_MountFlange',(pivot.x,pivot.y,base_top+.002),.026,.004,gray)
cyl('V138_Pivot_TrimRing',(pivot.x,pivot.y,base_top+.0045),.0262,.001,metal)
cyl('V138_Pivot_Turntable',(pivot.x,pivot.y,base_top+.008),.0215,.006,gray)
housingrig=bpy.data.objects.new('V138_Pivot_YawRig',None);col.objects.link(housingrig);housingrig.location=pivot;housingrig.rotation_mode='QUATERNION'
cyl('V138_Pivot_BearingSeat',(0,0,-.016),.014,.012,gray,housingrig)
housing=box('V138_Pivot_SolidDiagonalHousing',(0,0,-.001),(.017,.039,.025),gray,housingrig)
housing.rotation_euler.z=-math.pi/6
bev=housing.modifiers.new('Rounded solid bearing body','BEVEL');bev.width=.002;bev.segments=3
bpy.context.view_layer.objects.active=housing;housing.select_set(True)
bpy.ops.object.modifier_apply(modifier=bev.name)
# Actual bore along the shaft: the arm runs inside the solid body, not on top.
cut=cyl('V141_TemporaryBore',(0,0,0),.0038,.09,gray,housingrig);cut.rotation_euler.y=math.pi/2
bpy.context.view_layer.update()
boolean=housing.modifiers.new('Shaft bore','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cut
bpy.context.view_layer.objects.active=housing;bpy.ops.object.modifier_apply(modifier=boolean.name)
bpy.data.objects.remove(cut,do_unlink=True)

# Straight shaft into a smooth 45-degree circular J, not a chain of sharp elbows.
retire(bpy.data.objects['V138_Tonearm'])
points=[(.026,0,0),(0,0,0),(-.135,0,0)]
for i in range(1,25):
    a=(math.pi/4)*i/24;points.append((-.135-.04*math.sin(a),.04*(1-math.cos(a)),0))
end=Vector(points[-1])+Vector((-.70710678,.70710678,0))*.018
points.append(tuple(end));tube('V138_Tonearm',points,.0032,metal,rig)
head_transform=Matrix.Translation(end)@Matrix.Rotation(-math.pi/4,4,'Z')@Matrix.Translation(Vector((.18,-.007,0)))
for name in ('V138_Headshell','V138_Stylus','V138_Stylus_Cartridge','V138_Stylus_Cantilever'):
    ob=bpy.data.objects[name];ob.matrix_basis=head_transform@ob.matrix_basis
bpy.context.view_layer.update()
needle=bpy.data.objects['V138_Stylus'];local=[needle.matrix_local@v.co for v in needle.data.vertices]
def orientation(yaw,pitch):return Quaternion((0,0,1),yaw)@Quaternion((0,1,0),pitch)
def tip(yaw,pitch):return min((pivot+orientation(yaw,pitch)@p for p in local),key=lambda p:p.z)
def radius(yaw):
    p=tip(yaw,0);return math.hypot(p.x-2.465,p.y-1.173)
lo,hi=-.8,0
for _ in range(40):
    mid=(lo+hi)/2
    if radius(mid)<.1145:lo=mid
    else:hi=mid
landing_yaw=(lo+hi)/2
record_top=1.4785-drop;lo,hi=-.01,.02
for _ in range(40):
    mid=(lo+hi)/2
    if tip(landing_yaw,mid).z<record_top+.00005:lo=mid
    else:hi=mid
landing_pitch=(lo+hi)/2
keys=[(1,0,0),(90,0,0),(98,0,math.radians(1)),(112,landing_yaw,math.radians(1)),(122,landing_yaw,landing_pitch),(144,landing_yaw,landing_pitch)]
rig.animation_data_clear();audit=[]
for frame in range(1,145):
    a,b=next((a,b) for a,b in zip(keys,keys[1:]) if a[0]<=frame<=b[0]);t=(frame-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
    yaw=a[1]+(b[1]-a[1])*t;pitch=a[2]+(b[2]-a[2])*t
    rig.rotation_quaternion=orientation(yaw,pitch);rig.keyframe_insert('rotation_quaternion',frame=frame)
    housingrig.rotation_quaternion=Quaternion((0,0,1),yaw);housingrig.keyframe_insert('rotation_quaternion',frame=frame)
    audit.append({'frame':frame,'needleBottom':list(tip(yaw,pitch))})

# Rest follows the straight section, with shallow lips clear of the small lift.
for ob in list(s.objects):
    if ob.name.startswith('V138_ArmRest_') and not ob.hide_render:retire(ob)
rx,ry=pivot.x-.110,pivot.y
cyl('V138_ArmRest_Base',(rx,ry,base_top+.0015),.007,.003,gray)
seat=pivot.z-.0032-.0005-.0009
cyl('V138_ArmRest_Post',(rx,ry,(base_top+.003+seat)/2),.002,(seat-base_top-.003),metal)
tube('V138_ArmRest_Cradle',[(rx,ry-.005,seat+.001),(rx,ry-.005,seat),(rx,ry+.005,seat),(rx,ry+.005,seat+.001)],.0009,gray)
for frame in range(1,145):
    s.frame_set(frame);bpy.context.view_layer.update()
    assert (rig.matrix_world.translation-pivot).length<1e-7
    assert (housingrig.matrix_world.translation-pivot).length<1e-7
s.frame_set(122);bpy.context.view_layer.update()
bottom=min((needle.matrix_world@v.co).z for v in needle.data.vertices)
assert abs(bottom-record_top-.00005)<1e-6
assert abs(base.dimensions.z-old_height*.5)<1e-6
out=os.path.join(ROOT,'blender/outputs/review-v141');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'player-audit.json'),'w') as f:json.dump({'baseOldHeight':old_height,'baseNewHeight':base.dimensions.z,'baseTop':base_top,'fixedPivot':list(pivot),'recordTop':record_top,'landingYaw':landing_yaw,'landingPitch':landing_pitch,'samples':audit},f,indent=2)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=target)
print('V141_SAVED',target,'BASE_HEIGHT',base.dimensions.z,'NEEDLE',bottom,flush=True)
