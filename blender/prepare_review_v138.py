"""Non-destructive turntable/book design review. Does not replace website footage."""
import bpy, math, os, json
from mathutils import Vector, Matrix, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'blender/outputs/review-v138')
os.makedirs(OUT, exist_ok=True)
TARGET = os.path.join(ROOT, 'blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v138-player-book-review.blend')
assert 'v138-review-source' in bpy.data.filepath
assert not os.path.exists(TARGET), 'Never replace an existing review'
s = bpy.context.scene
s.frame_set(1)
bpy.context.view_layer.update()
before = {o.name: list(v for row in o.matrix_world for v in row) for o in s.objects}
collection = bpy.data.collections.new('V138_PLAYER_REVIEW')
s.collection.children.link(collection)

def material(name, rgb, roughness=.7):
    m = bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=roughness
    return m
gray=material('V138_Gray',(.12,.12,.12));black=material('V138_Contour',(.006,.006,.006))
metal=material('V138_Metal',(.25,.25,.25),.32);paper=material('V138_Paper',(.60,.59,.57),.95)
pageedge=material('V138_PageEdge',(.28,.28,.27));recordmat=material('V138_Record',(.012,.012,.012),.34)
labelmat=material('V138_RecordLabel',(.43,.43,.42)); covermat=material('V138_ClothCover',(.075,.075,.075),.92)
white=material('V138_ActiveOutline',(.65,.65,.65))

def link(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    collection.objects.link(o);return o
def empty(name, pos=(0,0,0)):
    o=bpy.data.objects.new(name,None);collection.objects.link(o);o.location=pos;return o
def box(name, pos, dims, mat, parent=None, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos);o=link(bpy.context.object);o.name=name
    o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new('Subtle manufactured edge','BEVEL');mod.width=bevel;mod.segments=2
    if parent:o.parent=parent
    return o
def cylinder(name,pos,radius,depth,mat,parent=None,vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos)
    o=link(bpy.context.object);o.name=name;o.data.materials.append(mat)
    if parent:o.parent=parent
    return o
def lines(name,segments,mat,radius=.0009,parent=None):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=1
    for segment in segments:
        p=data.splines.new('POLY');p.points.add(len(segment)-1)
        for a,co in zip(p.points,segment):a.co=(*co,1)
    o=bpy.data.objects.new(name,data);collection.objects.link(o);data.materials.append(mat)
    if parent:o.parent=parent
    return o
def boxlines(o,mat=black,radius=.0008):
    corners=[Vector(v) for v in o.bound_box]
    # Cube bound-box edges, independent of bevel topology.
    edges=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    wire=lines(o.name+'_Edges',[[corners[a],corners[b]] for a,b in edges],mat,radius,o)
    return wire
def key(o,frame,location=None,rotation=None,scale=None):
    if location is not None:o.location=location;o.keyframe_insert('location',frame=frame)
    if rotation is not None:o.rotation_mode='QUATERNION';o.rotation_quaternion=rotation;o.keyframe_insert('rotation_quaternion',frame=frame)
    if scale is not None:o.scale=scale;o.keyframe_insert('scale',frame=frame)
def bounds(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());pts=[ev.matrix_world@Vector(v) for v in ev.bound_box]
    return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]

# Pack actual contour envelopes, not just underlying boxes. Keep the run centered.
books=[bpy.data.objects[f'BOOK_Mid_{i}'] for i in range(10)]
wires=[bpy.data.objects['CATHODE_WIREFRAME_'+o.name] for o in books]
old_center=(min(bounds(w)[0][1] for w in wires)+max(bounds(w)[1][1] for w in wires))/2
last=books[-1];lastwire=wires[-1]
old=last.matrix_world.copy();pivot=Vector((last.location.x,last.location.y,bounds(last)[0][2]))
delta=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(-4),4,'X')@Matrix.Translation(-pivot)
last.matrix_world=delta@old;lastwire.matrix_world=delta@lastwire.matrix_world
bpy.context.view_layer.update()
# Preserve the foot height after changing the lean.
dz=1.7975-bounds(last)[0][2]
last.location.z+=dz;lastwire.location.z+=dz;bpy.context.view_layer.update()
gap=.0007
for i in range(1,len(books)):
    clearance=.00015 if i==9 else gap
    dy=bounds(wires[i-1])[1][1]+clearance-bounds(wires[i])[0][1]
    books[i].location.y+=dy;wires[i].location.y+=dy;bpy.context.view_layer.update()
new_center=(bounds(wires[0])[0][1]+bounds(wires[-1])[1][1])/2
for o in books+wires:o.location.y+=old_center-new_center
bpy.context.view_layer.update()
gaps=[bounds(wires[i])[0][1]-bounds(wires[i-1])[1][1] for i in range(1,10)]
assert min(gaps)>0,'Outlines must not overlap'

# Retain all historical player pieces hidden, so there is no old arm/record ghost.
for o in list(s.objects):
    if 'RecordPlayer' in o.name and not o.name.endswith('_Base'):
        o.hide_render=True;o.hide_set(True);o['v138_retained_original']=True

# Viewer axes: forward=-X, left=+Y. Platter left, tonearm pivot at back right.
platter_center=Vector((2.465,1.173,1.467))
platter=cylinder('V138_Player_Platter',platter_center,.12325,.016,gray)
lines('V138_Platter_Rim',[[tuple(platter_center+Vector((.123*math.cos(a*math.tau/96),.123*math.sin(a*math.tau/96),.008))) for a in range(97)]],metal,.0009)
cylinder('V138_Spindle',(2.465,1.173,1.483),.00165,.016,metal,vertices=20)
pivot=Vector((2.565,.972,1.493))
cylinder('V138_Tonearm_PivotBase',(pivot.x,pivot.y,1.468),.024,.028,gray,vertices=48)
cylinder('V138_Tonearm_PivotCap',(pivot.x,pivot.y,1.488),.017,.016,metal,vertices=48)
armroot=empty('V138_Tonearm_Rig',pivot)
lines('V138_Tonearm',[[(.018,0,.002),(0,0,0),(-.12,0,0),(-.153,.007,0),(-.18,.007,0)]],metal,.0032,armroot)
shell=box('V138_Headshell',(-.193,.007,0),(.033,.013,.007),gray,armroot,.001)
boxlines(shell)
cylinder('V138_Counterweight',(.023,0,.002),.01,.023,gray,armroot,32).rotation_euler.y=math.pi/2
needle=box('V138_Stylus',(-.202,.007,-.009),(.005,.004,.012),metal,armroot)
restpos=Vector((pivot.x-.154,pivot.y+.007,1.4525))
cylinder('V138_ArmRest_Base',restpos+Vector((0,0,.002)),.009,.004,gray,vertices=32)
cylinder('V138_ArmRest_Post',restpos+Vector((0,0,.017)),.0028,.031,metal,vertices=24)
lines('V138_ArmRest_Cradle',[[tuple(restpos+Vector((0,-.006,.039))),tuple(restpos+Vector((0,-.006,.035))),tuple(restpos+Vector((0,.006,.035))),tuple(restpos+Vector((0,.006,.039)))]],gray,.0018)

# A real thin ring mesh, not a zero-thickness circle; spindle hole stays open.
def ring(name,radius,inner,depth,mat,parent):
    n=128;verts=[]
    for z in (-depth/2,depth/2):
        for r in (inner,radius):verts.extend((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for i in range(n))
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(n+i,n+j,3*n+j,3*n+i),(i,2*n+i,2*n+j,j)])
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.materials.append(mat)
    o=bpy.data.objects.new(name,data);collection.objects.link(o);o.parent=parent;return o
discroot=empty('V138_Playback_Record_Rig')
ring('V138_Playback_Record',.12,.0022,.003,recordmat,discroot)
ring('V138_Playback_Label',.029,.0023,.00315,labelmat,discroot)
for r in (.044,.058,.075,.092,.11):
    lines('V138_Groove_'+str(r),[[(r*math.cos(i*math.tau/96),r*math.sin(i*math.tau/96),.00155) for i in range(97)]],black,.00012,discroot)

# Separate moving sleeve and stationary disc. Keep the approved artwork untouched.
sleeve=empty('V138_Playback_Sleeve_Rig')
source=bpy.data.objects['INTERACT_Vinyl_6']
center=Vector((-.028+.2585/2,0,-.1175+.2585/2))
copy=source.copy();copy.data=source.data.copy();collection.objects.link(copy);copy.name='V138_Playback_Sleeve';copy.animation_data_clear();copy.parent=sleeve
copy.matrix_parent_inverse=Matrix.Identity(4);copy.location=-center;copy.rotation_euler=(0,0,0);copy.scale=(1,1,1)
outline=bpy.data.objects['PROJECT_VINYL_V126_Outline_6'].copy();outline.data=outline.data.copy();collection.objects.link(outline);outline.name='V138_Playback_SleeveEdges';outline.parent=sleeve
outline.matrix_parent_inverse=Matrix.Identity(4);outline.location=-center;outline.rotation_euler=(0,0,0);outline.scale=(1,1,1)
sleeve['opacity']=1.0
for ob in (copy,outline):
    for slot in ob.material_slots:
        original=slot.material
        if not original:continue
        m=original.copy();m.name='V138_Fading_'+original.name;slot.link='OBJECT';slot.material=m
        nt=m.node_tree;output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');surface=output.inputs['Surface'].links[0].from_socket
        mix=nt.nodes.new('ShaderNodeMixShader');transparent=nt.nodes.new('ShaderNodeBsdfTransparent')
        nt.links.new(transparent.outputs[0],mix.inputs[1]);nt.links.new(surface,mix.inputs[2]);nt.links.new(mix.outputs[0],output.inputs['Surface'])
        driver=mix.inputs[0].driver_add('default_value').driver;driver.expression='opacity'
        v=driver.variables.new();v.name='opacity';v.targets[0].id=sleeve;v.targets[0].data_path='["opacity"]'

# 24 fps: reveal, fly/flip, land, lift/swing/lower arm, play, then browser redirect cue.
start=Vector((2.10,1.18,1.608));front=Quaternion((0,0,1),-math.pi/2)
discfront=front@Quaternion((1,0,0),math.pi/2)
for f in (1,42):key(discroot,f,start,discfront)
key(discroot,62,(2.20,1.173,1.62),discfront.slerp(Quaternion(),.55))
key(discroot,78,(2.425,1.173,1.535),Quaternion())
key(discroot,88,(2.465,1.173,1.477),Quaternion())
for f in range(89,145):key(discroot,f,(2.465,1.173,1.477),Quaternion((0,0,1),(f-88)/24*math.tau*33.333/60))
key(sleeve,1,start+Vector((0,.065,0)),front);key(sleeve,12,start+Vector((0,.065,0)),front)
key(sleeve,42,start+Vector((0,.34,0)),front);key(sleeve,144,start+Vector((0,.34,0)),front)
for f,value in ((1,1),(24,1),(44,0),(144,0)):
    sleeve['opacity']=value;sleeve.keyframe_insert('["opacity"]',frame=f)
for f,z,yaw in ((1,0,0),(90,0,0),(98,.014,0),(112,.014,-.63),(122,-.002,-.63),(144,-.002,-.63)):
    key(armroot,f,pivot+Vector((0,0,z)),Quaternion((0,0,1),yaw))
for f,label in ((1,'SELECTED_RECORD'),(12,'SLEEVE_LEFT_DISC_FIXED'),(42,'RECORD_FLIPS_TO_PLAYER'),(88,'RECORD_LANDS'),(98,'ARM_LIFTS_FROM_REST'),(122,'NEEDLE_DROP_SOUND'),(138,'OPEN_PROJECT_NEW_TAB')):
    s.timeline_markers.new('V138_'+label,frame=f)

def camera(scene,name,pos,target,lens=50):
    data=bpy.data.cameras.new(name);data.lens=lens
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
reviewcam=camera(s,'CAM_V138_Player_Review',(1.61,.57,1.98),(2.38,1.20,1.55),48)
stackcam=camera(s,'CAM_V138_BookStack_Review',(1.83,.94,2.22),(2.4,1.06,1.93),55)

# Two separate, real book assets. No random replacement until user approval.
bs=bpy.data.scenes.new('V138_Book_Prototypes');bs.world=s.world.copy();bs.render.engine='BLENDER_EEVEE'
collection=bpy.data.collections.new('V138_BOOK_PROTOTYPES');bs.collection.children.link(collection)
def prototype(kind,y):
    hard=kind=='Hardback';w=.16;h=.218;t=.038 if hard else .028;cover=.0027 if hard else .00065
    root=empty('V138_'+kind+'_Root',(0,y,0));root['binding']=kind;root['width']=w;root['height']=h;root['thickness']=t
    back=box(kind+'_BackCover',(0,t/2-cover/2,0),(w,cover,h),covermat,root,.0004)
    boxlines(back,radius=.00065 if hard else .00035)
    hinge=empty('V138_'+kind+'_FrontHinge',(-w/2,-t/2+cover/2,0));hinge.parent=root
    frontcover=box(kind+'_FrontCover',(w/2,0,0),(w,cover,h),covermat,hinge,.0004)
    boxlines(frontcover,radius=.00065 if hard else .00035)
    gap=.0011 if hard else .00008;inset=.0035 if hard else .0006
    block_thick=t-2*cover-2*gap
    block=box(kind+'_PageBlock',(.001,0,0),(w-inset*2,block_thick,h-inset*2),paper,root,.00025)
    box(kind+'_Spine',(-w/2+cover/2,0,0),(cover,t,h),covermat,root,.0004)
    # Sparse physical page-edge lines follow head/tail/fore-edge, never the spine.
    seg=[];xmin=-w/2+inset+.001;xmax=w/2-inset+.001;zmax=h/2-inset
    for i in range(1,25):
        yy=-block_thick/2+block_thick*i/25
        seg.append([(xmin,yy,zmax+.00006),(xmax,yy,zmax+.00006),(xmax+.00006,yy,-zmax),(xmin,yy,-zmax-.00006)])
    lines(kind+'_PageEdges',seg,pageedge,.00007,root)
    pages=[]
    for i in range(3):
        ph=empty('V138_'+kind+'_PageHinge_'+str(i),(-w/2+inset,-block_thick/2-.0003-i*.00012,0));ph.parent=root
        pw=w-inset*2;hh=h-inset*2;verts=[(pw*j/24,0,z) for z in (-hh/2,hh/2) for j in range(25)]
        faces=[(j,j+1,26+j,25+j) for j in range(24)]
        data=bpy.data.meshes.new(kind+'_Leaf'+str(i));data.from_pydata(verts,[],faces);data.materials.append(paper)
        page=bpy.data.objects.new(kind+'_Leaf'+str(i),data);collection.objects.link(page);page.parent=ph
        solid=page.modifiers.new('Actual sheet thickness','SOLIDIFY');solid.thickness=.0001
        page.shape_key_add(name='Flat');bend=page.shape_key_add(name='Turning curl')
        for v in bend.data:v.co.y=-.013*math.sin(math.pi*v.co.x/pw)
        f0=94+i*30
        for f,a in ((1,0),(f0,0),(f0+24,-math.pi),(240,-math.pi)):key(ph,f,rotation=Quaternion((0,0,1),a))
        for f,v in ((1,0),(f0,0),(f0+12,1),(f0+24,0),(240,0)):
            bend.value=v;bend.keyframe_insert('value',frame=f)
        pages.append(ph)
    for f,a in ((1,0),(30,0),(78,-math.pi),(240,-math.pi)):key(hinge,f,rotation=Quaternion((0,0,1),a))
    for f,x in ((1,0),(12,0),(30,-.035),(240,-.035)):key(root,f,location=(x,y,0))
    return root,hinge,pages
hard,hardhinge,hardpages=prototype('Hardback',0)
soft,softhinge,softpages=prototype('Paperback',.32)
bookcam=camera(bs,'CAM_V138_Book_Prototype',(.39,-.57,.39),(0,.12,0),52)
bs.camera=bookcam
for name,pos,power,size in [('Key',(0,-.4,.6),28,.6),('Fill',(.4,.5,.3),15,.5)]:
    data=bpy.data.lights.new('V138_Book_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(data.name,data);bs.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
bs.world.use_nodes=True;bs.world.node_tree.nodes.get('Background').inputs[0].default_value=(.08,.08,.08,1)
bs.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
bs.render.film_transparent=False
for scene in (s,bs):
    scene.render.fps=24;scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.eevee.taa_render_samples=32
bs.frame_start=1;bs.frame_end=240
s['v138_review_status']='Awaiting model/motion approval. No website footage re-recorded.'
s['v138_playback_frames']='1-144: cover left/fade; stationary disc; flight; arm from rest; needle122; new-tab138'
s['v138_original_book_distribution']='Unchanged until approval. Only top-stack spacing/lean corrected.'
s.camera=reviewcam;s.frame_start=1;s.frame_end=144;s.frame_set(1)
bs.frame_set(1)

# Validate exact stationary phase and intentional touch clearance.
s.frame_set(12);a=discroot.matrix_world.copy();s.frame_set(42);b=discroot.matrix_world.copy()
assert all(abs(a[i][j]-b[i][j])<1e-7 for i in range(4) for j in range(4))
s.frame_set(1);bpy.context.view_layer.update()
allowed={o.name for o in books+wires}
unchanged=[n for n,v in before.items() if n not in allowed and list(k for row in bpy.data.objects[n].matrix_world for k in row)!=v]
assert not unchanged,unchanged
audit={'source':bpy.data.filepath,'target':TARGET,'wireGapsMeters':gaps,'leanDegrees':4,'platter':list(platter_center),'pivot':list(pivot),'discStationaryFrames':[1,42],'soundFrame':122,'redirectFrame':138,'newTab':True,'bookSamplesOnly':True,'existingTransformsUnchangedExceptPackedBooks':True}
with open(os.path.join(OUT,'audit.json'),'w') as f:json.dump(audit,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=TARGET)
print('V138_REVIEW_SAVED',TARGET,flush=True)
