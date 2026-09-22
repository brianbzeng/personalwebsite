"""Replace the suburban exterior with an elevated grayscale city view."""

from pathlib import Path
import bpy, json, random, sys
from mathutils import Vector

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import outside_short_interactive_rays_v121 as V121

src=HERE/'outputs'/'blender'/'lofi-room-cathode-v129-suburban-window-view.blend'
out=HERE/'outputs'/'blender'/'lofi-room-cathode-v130-urban-skyline-window-view.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene
original=scene.camera


def mat(name,color,rough=.86,emit=None,power=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=(*color,1); m.roughness=rough; m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs:
        bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough
        if emit is not None:
            s=bs.inputs.get('Emission Color') or bs.inputs.get('Emission')
            if s: s.default_value=(*emit,1)
            p=bs.inputs.get('Emission Strength')
            if p: p.default_value=power
    return m


def box(name,c,d,m,cx):
    x,y,z=(v/2 for v in d)
    vs=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    fs=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(vs,[],fs); me.update()
    ob=bpy.data.objects.new(name,me); cx.objects.link(ob); ob.location=c; ob.data.materials.append(m); return ob


old=bpy.data.collections.get('CATHODE_SUBURBAN_WINDOW_VIEW')
if old:
    for ob in list(old.objects): bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.collections.remove(old)
for ob in list(bpy.data.objects):
    if ob.name.startswith(('CITY_VIEW_','LIGHT_CityView_')): bpy.data.objects.remove(ob,do_unlink=True)

coll=bpy.data.collections.new('CATHODE_URBAN_WINDOW_VIEW'); scene.collection.children.link(coll)
m={
 'sky':mat('CITY_VIEW_Sky',(0.018,0.023,0.033),.98,(0.026,0.032,0.045),.18),
 'a':mat('CITY_VIEW_BuildingA',(0.075,0.080,0.090)),
 'b':mat('CITY_VIEW_BuildingB',(0.105,0.108,0.116)),
 'c':mat('CITY_VIEW_BuildingC',(0.055,0.060,0.068)),
 'trim':mat('CITY_VIEW_Trim',(0.155,0.160,0.170),.90),
 'dark':mat('CITY_VIEW_WindowDark',(0.012,0.016,0.024),.64,(0.018,0.024,0.036),.06),
 'lit':mat('CITY_VIEW_WindowLit',(0.300,0.310,0.325),.58,(0.52,0.54,0.58),1.15),
 'mid':mat('CITY_VIEW_WindowMid',(0.100,0.110,0.125),.62,(0.15,0.17,0.20),.32),
 'roof':mat('CITY_VIEW_Rooftop',(0.030,0.034,0.041),.94),
 'road':mat('CITY_VIEW_StreetBelow',(0.012,0.015,0.020),.96),
}

box('CITY_VIEW_SkyBackdrop',(0,12.0,2.4),(12.0,.12,8.5),m['sky'],coll)
# Street is below the apartment sight line, providing depth without dominating the view.
box('CITY_VIEW_StreetBelow',(0,4.25,-2.65),(9.0,2.2,.12),m['road'],coll)

rng=random.Random(13008)
buildings=[
 (-3.20,6.6,1.75,6.4,-2.25,'c'),
 (-1.55,5.8,1.55,5.6,-2.15,'a'),
 (0.00,6.3,1.72,6.8,-2.60,'b'),
 (1.65,5.7,1.48,5.3,-2.05,'a'),
 (3.10,6.8,1.85,7.1,-2.75,'c'),
]
window_count=0
for bi,(cx,y,w,h,base,key) in enumerate(buildings):
    depth=1.25+rng.uniform(-.15,.25)
    box(f'CITY_VIEW_Building_{bi:02d}',(cx,y+depth/2,base+h/2),(w,depth,h),m[key],coll)
    # Roof parapet and utility mass establish an apartment-block silhouette.
    box(f'CITY_VIEW_Parapet_{bi:02d}',(cx,y-.035,base+h-.06),(w+.08,.11,.20),m['roof'],coll)
    if bi%2==0:
        box(f'CITY_VIEW_RoofUtility_{bi:02d}',(cx+w*.18,y+depth*.42,base+h+.20),(w*.30,.42,.42),m['roof'],coll)
    cols=max(2,int(w/.38)); rows=max(6,int(h/.46))
    xgap=w/(cols+1); zgap=(h-.45)/(rows+1)
    for row in range(rows):
        z=base+.30+(row+1)*zgap
        for col in range(cols):
            x=cx-w/2+(col+1)*xgap
            lit_roll=rng.random()
            wm=m['lit'] if lit_roll<.22 else (m['mid'] if lit_roll<.45 else m['dark'])
            box(f'CITY_VIEW_Window_{bi:02d}_{row:02d}_{col:02d}',(x,y-.018,z),(xgap*.58,.025,zgap*.48),wm,coll)
            window_count+=1
    # Horizontal floor ledges make the varying heights readable through blinds.
    for row in range(1,rows):
        z=base+.30+row*zgap+.5*zgap
        box(f'CITY_VIEW_Ledge_{bi:02d}_{row:02d}',(cx,y-.034,z),(w+.04,.045,.025),m['trim'],coll)

# Rear skyline silhouettes fill small gaps without looking like duplicated façades.
for i,(cx,w,h) in enumerate(((-2.4,1.3,7.8),(-.75,1.0,8.8),(.9,1.15,7.7),(2.45,1.2,8.4))):
    box(f'CITY_VIEW_BackTower_{i:02d}',(cx,9.0,-3.1+h/2),(w,1.0,h),m['roof'],coll)

ld=bpy.data.lights.new('LIGHT_CityView_Moon_Data','AREA'); ld.energy=120; ld.shape='RECTANGLE'; ld.size=8; ld.size_y=5; ld.color=(.54,.60,.70)
lo=bpy.data.objects.new('LIGHT_CityView_Moon',ld); coll.objects.link(lo); lo.location=(-3.2,4.0,5.0); lo.rotation_euler=(Vector((0,7.0,.8))-lo.location).to_track_quat('-Z','Y').to_euler()

for c in bpy.data.collections:
    if 'RAIN' in c.name.upper(): c.hide_render=True; c.hide_viewport=True
for ob in bpy.data.objects:
    if 'RAIN' in ob.name.upper(): ob.hide_render=True; ob.hide_viewport=True

scene['cathode_restyle_version']='v130'; scene['cathode_urban_window_view_v130']=True
scene['cathode_exterior_setting']='elevated apartment looking across a city street'
bpy.context.view_layer.update(); bpy.ops.wm.save_as_mainfile(filepath=str(out))

renders={}
cam=V121.qa_camera('CAM_QA_UrbanRoomView_v130',(-2.70,.20,2.35),(0,6.0,1.05),48)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v130-urban-room-view.png'; V121.render(scene,cam,img,(1200,800)); renders['room']=str(img)
cam=V121.qa_camera('CAM_QA_UrbanExterior_v130',(0,2.78,1.72),(0,6.2,.90),48)
img=HERE/'outputs'/'blender'/'lofi-room-cathode-v130-urban-exterior.png'; V121.render(scene,cam,img,(1200,800)); renders['exterior']=str(img)
if original: scene.camera=original
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'source':str(src),'output':str(out),'buildings':len(buildings),'rear_towers':4,'facade_windows':window_count,'rain_hidden':True,'renders':renders}
out.with_name(out.stem+'-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('V130_REPORT='+json.dumps(report))
