"""Build a compact, layered suburban street composition outside both windows."""

from pathlib import Path
import bpy, json, math, random, sys
from mathutils import Vector

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import outside_short_interactive_rays_v121 as V121

src=HERE/'outputs'/'blender'/'lofi-room-cathode-v128-blanket-field.blend'
out=HERE/'outputs'/'blender'/'lofi-room-cathode-v129-suburban-window-view.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene
original=scene.camera


def material(name,color,rough=0.82,emission=None,strength=0.0):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1.0)
    mat.roughness=rough
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=(*color,1.0)
        bsdf.inputs['Roughness'].default_value=rough
        if emission is not None:
            sock=bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
            if sock: sock.default_value=(*emission,1.0)
            power=bsdf.inputs.get('Emission Strength')
            if power: power.default_value=strength
    return mat


def box(name,center,dims,mat,coll):
    x,y,z=(d*0.5 for d in dims)
    verts=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    mesh=bpy.data.meshes.new(name+'_Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    ob=bpy.data.objects.new(name,mesh); coll.objects.link(ob); ob.location=center; ob.data.materials.append(mat)
    return ob


def gable(name,cx,front_y,width,depth,eave,ridge,mat,coll):
    x0,x1=cx-width/2,cx+width/2; y0,y1=front_y-0.08,front_y+depth
    verts=[(x0-0.12,y0,eave),(x1+0.12,y0,eave),(cx,y0,ridge),(x0-0.12,y1,eave),(x1+0.12,y1,eave),(cx,y1,ridge)]
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(0,2,5,3),(2,1,4,5)]
    mesh=bpy.data.meshes.new(name+'_Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    ob=bpy.data.objects.new(name,mesh); coll.objects.link(ob); ob.data.materials.append(mat); return ob


def pane(name,x,y,z,w,h,frame_mat,glass_mat,coll):
    box(name+'_Glass',(x,y-0.018,z),(w,0.028,h),glass_mat,coll)
    t=0.045
    for suffix,c,d in (
        ('L',(x-w/2-t/2,y-0.040,z),(t,0.035,h+2*t)),
        ('R',(x+w/2+t/2,y-0.040,z),(t,0.035,h+2*t)),
        ('B',(x,y-0.040,z-h/2-t/2),(w,t,t)),
        ('T',(x,y-0.040,z+h/2+t/2),(w,t,t)),
        ('V',(x,y-0.043,z),(t*0.55,0.038,h)),
        ('H',(x,y-0.043,z),(w,0.038,t*0.55))):
        box(name+'_'+suffix,c,d,frame_mat,coll)


def crossed_grass(name,xmin,xmax,ymin,ymax,count,mats,coll,seed):
    rng=random.Random(seed); verts=[]; faces=[]; ids=[]
    for _ in range(count):
        x=rng.uniform(xmin,xmax); y=rng.uniform(ymin,ymax); z=0.095
        h=rng.uniform(0.055,0.16); w=rng.uniform(0.003,0.009); lean=rng.uniform(-0.025,0.025)
        angle=rng.uniform(0,math.tau); mid=rng.randrange(len(mats))
        for a in (angle,angle+math.pi/2):
            dx,dy=math.cos(a)*w,math.sin(a)*w; base=len(verts)
            verts += [(x-dx,y-dy,z),(x+dx,y+dy,z),(x+lean+dx*0.12,y+dy*0.12,z+h*0.86),(x+lean,y,z+h)]
            faces.append((base,base+1,base+2,base+3)); ids.append(mid)
    mesh=bpy.data.meshes.new(name+'_Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    ob=bpy.data.objects.new(name,mesh); coll.objects.link(ob)
    for m in mats: mesh.materials.append(m)
    for p,i in zip(mesh.polygons,ids): p.material_index=i
    return ob


# Remove the generic field so no layers overlap.
old_coll=bpy.data.collections.get('CATHODE_EXTERIOR_SOURCE_FIELD')
if old_coll:
    for ob in list(old_coll.objects): bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.collections.remove(old_coll)
for ob in list(bpy.data.objects):
    if ob.name.startswith(('SUBURB_VIEW_','LIGHT_SuburbView_')):
        bpy.data.objects.remove(ob,do_unlink=True)

coll=bpy.data.collections.new('CATHODE_SUBURBAN_WINDOW_VIEW')
scene.collection.children.link(coll)

mats={
 'near_grass':material('SUBURB_VIEW_NearGrass',(0.055,0.066,0.064)),
 'far_grass':material('SUBURB_VIEW_FarGrass',(0.060,0.072,0.070)),
 'blade_dark':material('SUBURB_VIEW_BladeDark',(0.050,0.060,0.060)),
 'blade_mid':material('SUBURB_VIEW_BladeMid',(0.115,0.125,0.124)),
 'blade_pale':material('SUBURB_VIEW_BladePale',(0.205,0.215,0.214)),
 'walk':material('SUBURB_VIEW_Sidewalk',(0.235,0.240,0.242),0.91),
 'curb':material('SUBURB_VIEW_Curb',(0.285,0.290,0.292),0.90),
 'road':material('SUBURB_VIEW_Road',(0.020,0.024,0.028),0.94),
 'drive':material('SUBURB_VIEW_Driveway',(0.150,0.155,0.158),0.92),
 'wall':material('SUBURB_VIEW_HouseWall',(0.165,0.175,0.180),0.86),
 'roof':material('SUBURB_VIEW_Roof',(0.050,0.056,0.062),0.93),
 'trim':material('SUBURB_VIEW_Trim',(0.315,0.325,0.330),0.84),
 'door':material('SUBURB_VIEW_Door',(0.085,0.092,0.098),0.88),
 'glass':material('SUBURB_VIEW_WindowGlass',(0.090,0.102,0.112),0.58,(0.18,0.19,0.20),0.35),
 'garage':material('SUBURB_VIEW_Garage',(0.205,0.212,0.215),0.88),
 'sky':material('SUBURB_VIEW_Sky',(0.028,0.034,0.043),0.96,(0.042,0.050,0.062),0.18),
}

# Cross-section layers follow the supplied sketch, compressed to the visible depth.
box('SUBURB_VIEW_NearLawn',(0.0,3.42,0.045),(5.8,1.35,0.09),mats['near_grass'],coll)
box('SUBURB_VIEW_NearSidewalk',(0.0,4.22,0.105),(5.8,0.34,0.10),mats['walk'],coll)
box('SUBURB_VIEW_NearCurb',(0.0,4.43,0.115),(5.8,0.10,0.14),mats['curb'],coll)
box('SUBURB_VIEW_Street',(0.0,5.28,0.055),(5.8,1.60,0.11),mats['road'],coll)
box('SUBURB_VIEW_FarCurb',(0.0,6.12,0.115),(5.8,0.10,0.14),mats['curb'],coll)
box('SUBURB_VIEW_FarSidewalk',(0.0,6.34,0.105),(5.8,0.34,0.10),mats['walk'],coll)
box('SUBURB_VIEW_FarLawn',(0.0,7.00,0.045),(5.8,1.05,0.09),mats['far_grass'],coll)
crossed_grass('SUBURB_VIEW_NearGrassBlades',-2.85,2.85,2.82,4.04,9000,[mats['blade_dark'],mats['blade_mid'],mats['blade_pale']],coll,12901)
crossed_grass('SUBURB_VIEW_FarGrassBlades',-2.85,2.85,6.56,7.45,6000,[mats['blade_dark'],mats['blade_mid'],mats['blade_pale']],coll,12902)

# One detached house across the street, centered so both room windows see a coherent façade.
cx,front,width,depth=0.0,7.48,4.20,1.15
box('SUBURB_VIEW_HouseBody',(cx,front+depth/2,0.93),(width,depth,1.72),mats['wall'],coll)
gable('SUBURB_VIEW_HouseRoof',cx,front,width,depth,1.79,2.58,mats['roof'],coll)
garage_x=-1.08; door_x=1.28
box('SUBURB_VIEW_GarageDoor',(garage_x,front-0.035,0.53),(1.45,0.035,0.88),mats['garage'],coll)
for i in range(4): box(f'SUBURB_VIEW_GaragePanel_{i}',(garage_x,front-0.06,0.25+i*0.19),(1.26,0.022,0.025),mats['trim'],coll)
box('SUBURB_VIEW_Driveway',(garage_x,6.93,0.11),(1.72,0.92,0.055),mats['drive'],coll)
box('SUBURB_VIEW_FrontDoor',(door_x,front-0.038,0.58),(0.46,0.040,1.05),mats['door'],coll)
box('SUBURB_VIEW_FrontStep',(door_x,front-0.20,0.11),(0.72,0.34,0.12),mats['walk'],coll)
box('SUBURB_VIEW_Walkway',(door_x,6.93,0.11),(0.34,0.92,0.055),mats['walk'],coll)
pane('SUBURB_VIEW_WindowLeft',-0.12,front,0.93,0.68,0.62,mats['trim'],mats['glass'],coll)
pane('SUBURB_VIEW_WindowRight',0.70,front,0.93,0.58,0.62,mats['trim'],mats['glass'],coll)
pane('SUBURB_VIEW_UpperWindow',0.0,front,1.57,0.72,0.42,mats['trim'],mats['glass'],coll)
box('SUBURB_VIEW_SkyBackdrop',(0.0,9.15,2.2),(6.2,0.12,4.4),mats['sky'],coll)

# Subtle exterior illumination so geometry reads at night without fighting the room lighting.
ld=bpy.data.lights.new('LIGHT_SuburbView_Moon_Data','AREA'); ld.energy=155; ld.shape='RECTANGLE'; ld.size=6.0; ld.size_y=3.0; ld.color=(0.58,0.64,0.72)
lo=bpy.data.objects.new('LIGHT_SuburbView_Moon',ld); coll.objects.link(lo); lo.location=(-2.6,4.8,4.4); lo.rotation_euler=(Vector((0.0,7.1,0.6))-lo.location).to_track_quat('-Z','Y').to_euler()

# Keep all rain hidden until the environment is approved.
for c in bpy.data.collections:
    if 'RAIN' in c.name.upper(): c.hide_render=True; c.hide_viewport=True
for ob in bpy.data.objects:
    if 'RAIN' in ob.name.upper(): ob.hide_render=True; ob.hide_viewport=True

scene['cathode_restyle_version']='v129'
scene['cathode_suburban_window_view_v129']=True
scene['cathode_exterior_layers']='near grass, sidewalk, street, sidewalk, far grass, detached house'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out))

renders={}
cam=V121.qa_camera('CAM_QA_SuburbanWindows_v129',(-2.70,0.20,2.35),(0.0,5.75,1.15),48.0)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v129-suburban-windows.png'; V121.render(scene,cam,img,(1200,800)); renders['room']=str(img)
cam=V121.qa_camera('CAM_QA_SuburbanExterior_v129',(0.0,2.78,1.72),(0.0,7.2,0.90),45.0)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v129-suburban-exterior.png'; V121.render(scene,cam,img,(1200,800)); renders['exterior']=str(img)
if original: scene.camera=original
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'source':str(src),'output':str(out),'layers':['near lawn','near sidewalk','street','far sidewalk','far lawn','house'],'grass_blades':15000,'rain_hidden':True,'renders':renders}
out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('V129_REPORT='+json.dumps(report))
