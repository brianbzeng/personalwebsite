"""Versioned shelf poses, decorative sleeves, report-book export and soft shade light."""
import bpy, json, math, os
from mathutils import Vector

s=bpy.context.scene
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out=os.path.join(root,'blender/outputs/web-room-v137');os.makedirs(out,exist_ok=True)
target=os.path.join(root,'blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v137-shelf-book-lamp-glow.blend')
assert 'v136-lamps-bedside-rug' in bpy.data.filepath
assert not os.path.exists(target), 'Never overwrite an earlier saved scene'
s.frame_set(277);bpy.context.view_layer.update()
before={o.name:list(v for row in o.matrix_world for v in row) for o in s.objects}

# Retain the precise authored lean; these covers now stay in the rendered plate.
body=bpy.data.materials['VINYL_V126_Body']
for slot in (0,1):
    o=bpy.data.objects[f'INTERACT_Vinyl_{slot}']
    for material in o.material_slots:material.link='OBJECT';material.material=body
    o['project_title']='';o['project_url']='';o['decorative_blank']=True
    bpy.data.objects[f'PROJECT_VINYL_V126_Record_{slot}'].hide_render=True
    bpy.data.objects[f'PROJECT_VINYL_V126_Record_{slot}'].hide_set(True)

# A broad, low-energy source scatters out of each shade without visible cones.
for name,energy,radius in [('DESK_LampShade',9,.13),('FLOOR_LAMP_V129_DESK_LampShade',13,.17)]:
    o=bpy.data.objects[name]
    for m in {slot.material for slot in o.material_slots if slot.material}:
        n=m.node_tree.nodes['Restrained glow softer at the rims']
        dark='DARK' in m.name
        n.inputs['To Min'].default_value=.10 if dark else .15
        n.inputs['To Max'].default_value=.38 if dark else .55
    lamp=bpy.data.objects[name+'_InternalSoftLight_V135']
    lamp.data.energy=energy;lamp.data.shadow_soft_size=radius

# Preserve the selected book geometry and authored lean, including its outline.
book=bpy.data.objects['BOOK_Mid_9'] # highest +Y = viewer-left end of vertical run
book_wire=bpy.data.objects['CATHODE_WIREFRAME_BOOK_Mid_9']
for slot in book.material_slots:slot.link='OBJECT';slot.material=body
for slot in book_wire.material_slots:
    slot.link='OBJECT';slot.material=bpy.data.materials['INTERACT_MutedAmberPulse_v115_Selected_v119']
book['report_book']=True

def camera(name,z):
    c=bpy.data.objects.new(name,bpy.data.objects['CAM_Website_Pans_v119'].data.copy())
    s.collection.objects.link(c);c.data.animation_data_clear();c.data.lens=50;c.data.shift_x=0;c.data.shift_y=0
    c.location=(.30,1.36,z+.02);aim=Vector((2.45,1.36,z))
    c.rotation_euler=(aim-c.location).to_track_quat('-Z','Y').to_euler()
    return c,aim

cameras=[]
for name,z in [('books',1.995),('records',1.56),('photos',1.135)]:
    c,aim=camera('CAM_Shelf_'+name+'_v137',z);bpy.context.view_layer.update()
    q=c.matrix_world.to_quaternion()
    cameras.append(dict(id=name,camera=list(c.location),target=list(aim),quaternion=[q.x,q.y,q.z,q.w],verticalFov=math.degrees(2*math.atan(36/50/2*9/16))))

def worldmesh(o,center=None,rotation=None):
    deps=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
    positions=[]
    for v in mesh.vertices:
        p=o.matrix_world@v.co
        if center is not None:p=rotation.inverted()@(p-center)
        positions.extend(p)
    result=dict(positions=positions,indices=[i for t in mesh.loop_triangles for i in t.vertices])
    ev.to_mesh_clear();return result

s.frame_set(277);bpy.context.view_layer.update()
old=json.load(open(os.path.join(root,'public/room/vinyl-geometry.json')))
active=[];decorations=[]
for data in old['objects']:
    o=bpy.data.objects[data['name']];q=o.matrix_world.to_quaternion()
    center=Vector((-.028+.2585/2,0,-.1175+.2585/2))
    data['origin']=list(o.matrix_world@center);data['quaternion']=[q.x,q.y,q.z,q.w]
    if data['project']<5:active.append(data)
    else:decorations.append(dict(name=o.name,project=data['project'],origin=data['origin'],quaternion=data['quaternion'],blank=True,interactive=False))

# Depth-only geometry includes both decorations, so interactive sleeves cannot
# draw through the fixed covers or the rack during their slide animation.
occluders=[worldmesh(bpy.data.objects[n]) for n in ['SHELF_VinylRack_Left','SHELF_VinylRack_Right','SHELF_Carcass_Cohesive','INTERACT_Vinyl_0','INTERACT_Vinyl_1']]
center=book.matrix_world.translation.copy();q=book.matrix_world.to_quaternion()
bookdata=dict(name=book.name,origin=list(center),quaternion=[q.x,q.y,q.z,q.w],body=worldmesh(book,center,q),outline=worldmesh(book_wire,center,q),width=.16,height=.198,thickness=.037)
model=dict(version=137,objects=active,decorations=decorations,occluders=occluders,cubbies=cameras,book=bookdata,hoverTravel=.085,side=.2585,outlineRadius=.0013)
with open(os.path.join(out,'shelf-geometry.json'),'w') as f:json.dump(model,f)
assert all(before[n]==list(v for row in bpy.data.objects[n].matrix_world for v in row) for n in before)
with open(os.path.join(out,'scene-audit.json'),'w') as f:json.dump(dict(originalTransformsUnchanged=True,book=book.name,decorations=decorations,cameras=cameras,shadeTransparency=.12,source='v136'),f,indent=2)
s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119'];s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=target)
print('V137_SOURCE_READY',target,flush=True)
