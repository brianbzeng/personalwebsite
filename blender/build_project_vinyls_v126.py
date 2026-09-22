"""Bake the seven project sleeves into a NEW scene; retain all source objects."""
import bpy, json, math, os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
records=json.load(open(os.path.join(ROOT,'app/data/vinyls.json')))
scene=bpy.context.scene
scene.frame_set(277)
SIDE=.2585
RADIUS=.0013
collection=bpy.data.collections.new('PROJECT_VINYL_ART_V126');scene.collection.children.link(collection)
def emission(name,color=None,image=None):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission')
    e.inputs['Strength'].default_value=2**.3
    if image:
        t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(image,check_existing=True);t.image.pack();m.node_tree.links.new(t.outputs['Color'],e.inputs['Color'])
    else:
        srgb=lambda x:x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
        e.inputs['Color'].default_value=(*[srgb(x) for x in color],1)
    m.node_tree.links.new(e.outputs[0],out.inputs['Surface']);return m
bodymat=emission('VINYL_V126_Body',(.28235,)*3)
black=emission('VINYL_V126_Black',(.03137,)*3)
disc_material=emission('VINYL_V126_Record',(.06667,)*3)
pulse=bpy.data.materials['INTERACT_MutedAmberPulse_v115_Selected_v119']
def mesh(name,verts,faces,materials,parent=None):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    ob=bpy.data.objects.new(name,data);collection.objects.link(ob)
    if parent:ob.parent=parent
    for m in materials:data.materials.append(m)
    return ob
def curve(name,segments,material,parent=None):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=RADIUS;data.bevel_resolution=1;data.resolution_u=1
    for points in segments:
        spline=data.splines.new('POLY');spline.points.add(len(points)-1)
        for p,co in zip(spline.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,data);collection.objects.link(ob);data.materials.append(material)
    if parent:ob.parent=parent
    return ob
objects=[]
# Looking +X from the approved shelf camera, +Y is viewer-left.
for slot in range(7):
    project=6-slot;r=records[project]
    o=bpy.data.objects[f'INTERACT_Vinyl_{slot}']
    old_wire=bpy.data.objects[f'CATHODE_WIREFRAME_INTERACT_Vinyl_{slot}'];old_wire.hide_render=True;old_wire.hide_set(True)
    # Preserve the leaning rightmost sleeve; replace its tiny historical shear
    # with a rigid square that remains leaned against its neighbour.
    if slot==0:o.rotation_euler.x=-.2583
    half=SIDE/2;thickness=.024 if slot in [0,2,4,6] else .026;y=thickness/2
    center=Vector((-.028+half,0,-.1175+half))
    a,b=-half,half
    faces=[[(a,-y,a),(b,-y,a),(b,-y,b),(a,-y,b)],
           [(b,y,a),(a,y,a),(a,y,b),(b,y,b)],
           [(a,-y,b),(a,y,b),(a,y,a),(a,-y,a)],
           [(b,-y,a),(b,y,a),(b,y,b),(b,-y,b)],
           [(a,-y,a),(a,y,a),(b,y,a),(b,-y,a)],
           [(a,-y,b),(b,-y,b),(b,y,b),(a,y,b)]]
    vertices=[Vector(v)+center for f in faces for v in f]
    data=bpy.data.meshes.new(o.name+'_Square_v126');data.from_pydata(vertices,[],[tuple(range(i*4,i*4+4)) for i in range(6)]);data.update();o.data=data
    textures=[emission(f'VINYL_V126_{r["slug"]}_{side}',image=os.path.join(ROOT,'public/room/vinyl-art',r['slug']+'-'+side+'.png')) for side in ['front','back','spine']]
    for m in [bodymat,*textures]:data.materials.append(m)
    uv=data.uv_layers.new(name='Project artwork')
    for p,mi in zip(data.polygons,[1,2,3,0,0,0]):
        p.material_index=mi
        for li,coord in zip(p.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=coord
    corners=[(x,yy,z) for x in [a,b] for yy in [-y,y] for z in [a,b]]
    edges=[[corners[i],corners[j]] for i in range(8) for j in range(i+1,8) if sum(corners[i][k]!=corners[j][k] for k in range(3))==1]
    outline=curve(f'PROJECT_VINYL_V126_Outline_{slot}',[[Vector(p)+center for p in e] for e in edges],pulse,o)
    # Record peeks from the back edge. Front/back artwork remains upright.
    points=[(center.x+.065+.12*math.cos(i*math.tau/96),0,center.z+.12*math.sin(i*math.tau/96)) for i in range(96)]
    record=mesh(f'PROJECT_VINYL_V126_Record_{slot}',points,[tuple(range(96))],[disc_material],o)
    o['project_title']=r['title'];o['project_url']=r['href'] or '';o['viewer_order']=project+1
    scene.view_layers.update()
    q=o.matrix_world.to_quaternion()
    # Canonical object data is shared with the browser, not approximated there.
    objects.append({'name':o.name,'project':project,'origin':list(o.matrix_world@center),'quaternion':[q.x,q.y,q.z,q.w],
      'positions':[v for f in faces for p in f for v in p],
      'indices':[i*4+j for i in range(6) for j in [0,1,2,0,2,3]],
      'uvs':[v for _ in range(6) for uvco in [(0,0),(1,0),(1,1),(0,1)] for v in uvco],
      'materials':[1,2,3,0,0,0],'edges':edges,'thickness':thickness})
occluders=[]
for name in ['SHELF_VinylRack_Left','SHELF_VinylRack_Right']:
    o=bpy.data.objects[name];o.data.calc_loop_triangles()
    occluders.append({'positions':[c for v in o.data.vertices for c in (o.matrix_world@v.co)],'indices':[i for t in o.data.loop_triangles for i in t.vertices]})
geometry={'objects':objects,'occluders':occluders,'camera':[1.1,1.65,1.54],'target':[2.4,1.65,1.52],
 'verticalFov':math.degrees(2*math.atan(36/50/2*9/16)),'hoverTravel':.085,'side':SIDE,'outlineRadius':RADIUS,'version':126}
out=os.path.join(ROOT,'blender/outputs/web-room-v126');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'vinyl-geometry.json'),'w') as f:json.dump(geometry,f)
scene['vinyl_project_manifest']='app/data/vinyls.json'
print('PROJECT_SLEEVES_READY',flush=True)
