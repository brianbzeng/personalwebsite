"""Thin physical feature contours sharing the existing room lighting material."""
import bpy, bmesh, math, os, json
from mathutils import Vector
assert bpy.data.filepath.endswith('v144-themed-player-delayed-fade.blend')
target=os.path.join(os.path.dirname(bpy.data.filepath),'lofi-room-cathode-glm53f-city-v145-lit-player-wireframe.blend')
assert not os.path.exists(target)
s=bpy.context.scene;s.frame_set(1)
tab=bpy.data.objects['V138_ArmRest_SocketSlot'];tab.hide_render=True;tab.hide_set(True)
col=bpy.data.collections['V138_PLAYER_REVIEW']
light=bpy.data.materials['CATHODE_V131_Travel_record-player']
assert light.node_tree.nodes.get('SWEEP_CLOCK')
shell_light=light.copy();shell_light.name='V138_PulseSilhouette'
shell_light.use_backface_culling=True;shell_light['review_front_side']=True
linked=[]
for ob in list(s.objects):
    if ob.hide_render:continue
    if ob.name.startswith(('V138_Pivot_','V138_Tonearm')) and ob.name.endswith('_ThemeOutline'):
        for slot in ob.material_slots:slot.link='OBJECT';slot.material=shell_light
        linked.append(ob.name)
    if ob.name.startswith('V138_Pivot_TerraceSeam'):
        for slot in ob.material_slots:slot.link='OBJECT';slot.material=light
        linked.append(ob.name)

def wire(name,segments,parent):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=.00012;data.bevel_resolution=1
    for points in segments:
        if len(points)<2:continue
        sp=data.splines.new('POLY');sp.points.add(len(points)-1)
        for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,data);col.objects.link(ob);ob.parent=parent;data.materials.append(light)
    ob['wire_radius_m']=.00012;linked.append(name);return ob

# Longitudinal rails follow the continuous J tube, with rings only at its ends.
arm=bpy.data.objects['V138_Tonearm']
points=[Vector(p.co[:3]) for p in arm.data.splines[0].points]
normals=[]
for i,p in enumerate(points):
    tangent=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
    normals.append(Vector((-tangent.y,tangent.x,0)).normalized())
segments=[];radius=arm.data.bevel_depth+.000025
for a in (0,math.pi/2,math.pi,3*math.pi/2):
    segments.append([p+radius*(normal*math.cos(a)+Vector((0,0,math.sin(a)))) for p,normal in zip(points,normals)])
for i in (0,len(points)-1):
    segments.append([points[i]+radius*(normals[i]*math.cos(a*math.tau/48)+Vector((0,0,math.sin(a*math.tau/48)))) for a in range(49)])
wire('V138_Tonearm_FeatureWire',segments,arm)

# Source-face creases select tier rims, yoke corners and socket boundaries;
# no smooth cylinder tessellation or triangulation edges are included.
for ob in list(s.objects):
    if ob.hide_render or ob.type!='MESH' or not ob.name.startswith('V138_Pivot_') or 'Outline' in ob.name:continue
    bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update();segments=[]
    for edge in bm.edges:
        if edge.is_boundary or (edge.is_manifold and edge.calc_face_angle()>math.radians(40)):
            segments.append([v.co.copy() for v in edge.verts])
    bm.free()
    if segments:wire(ob.name+'_FeatureWire',segments,ob)

# All added curves use the identical material datablock/clock as the room player.
assert all(slot.material==light for ob in s.objects if ob.name.endswith('_FeatureWire') for slot in ob.material_slots)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=target)
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'blender/outputs/review-v145');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'wire-audit.json'),'w') as f:json.dump({'hidden':'V138_ArmRest_SocketSlot','animatedContours':linked,'material':light.name,'radiusMeters':.00012,'fadeDelayPreservedSeconds':.2},f,indent=2)
print('V145_LIT_WIREFRAME_COMPLETE',target)
