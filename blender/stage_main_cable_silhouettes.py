"""Continuous outside-only contours for round main cables, preserving source parts."""
import bpy, math
from mathutils import Vector

coll=bpy.data.collections.new('BRIDGE_V103_MainCable_Outside_Only')
bpy.context.scene.collection.children.link(coll)
base=bpy.data.materials['CATHODE_GLOBAL_BLACK_FLOWING_INK_V77.001']
mat=base.copy(); mat.name='BRIDGE_V103_Animated_Outside_Only'
mat.use_backface_culling=True
matrix=bpy.data.objects['Object_2'].matrix_world.copy()

# Main cables are circular arcs swept with radius four. Reuse the source's
# longitudinal sampling; no original objects are joined or changed.
sections=[(67,483.5,137),(491.3,1183.5,837),(1191.3,1503.0,1537),
          (1571.0,1882.7,1537),(1890.5,2582.7,2237),(2590.5,3007,2937)]
for side in ['L','R']:
 for number,(lo,hi,mid) in enumerate(sections):
    x=(64 if mid<1537 or hi<1537 else 63) if side=='L' else (102 if mid<1537 or hi<1537 else 101)
    # The source changes lateral alignment across the center/deck join.
    zs=[lo,hi]
    for i in range(-15,16):
        z=mid+500*math.sin(i*.05+.025)
        if lo<z<hi:zs.append(z)
    zs=sorted(zs)
    centers=[Vector((x,-650+math.sqrt(250000-(z-mid)**2),z)) for z in zs]
    verts=[]; faces=[]; sides=96
    for j,c in enumerate(centers):
        tangent=(centers[min(j+1,len(centers)-1)]-centers[max(j-1,0)]).normalized()
        radial=Vector((0,tangent.z,-tangent.y))
        for k in range(sides):
            a=2*math.pi*k/sides
            p=c+4.34*(Vector((1,0,0))*math.cos(a)+radial*math.sin(a))
            verts.append(tuple(p))
    for j in range(len(centers)-1):
        for k in range(sides):
            a=j*sides+k;b=j*sides+(k+1)%sides
            # Inward-facing shell: only the silhouette rim is visible.
            faces.append((a+sides,b+sides,b,a))
    mesh=bpy.data.meshes.new(f'V103_{side}_Main_{number}_Shell')
    mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(mesh.name,mesh);coll.objects.link(ob)
    ob.matrix_world=matrix;mesh.materials.append(mat)
    ob['purpose']='Outside-only animated silhouette; no front-face longitudinal stripes'

# Retire main-cable traces and retain suspenders and the structural overlay.
for o in bpy.data.objects:
 if o.name.startswith('V102_') and ('MainCable' in o.name or 'Attachment_and_Deck' in o.name):
    o.hide_set(True);o.hide_render=True
print('Created',len(coll.objects),'main cable contour shells')
