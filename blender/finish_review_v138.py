"""Final approval-only details: lining paper and clear selected-book contours."""
import bpy
assert bpy.data.filepath.endswith('v138-player-book-review.blend')
col=bpy.data.collections['V138_BOOK_PROTOTYPES']
for kind,cover in [('Hardback',.0027),('Paperback',.00065)]:
    thickness=.038 if kind=='Hardback' else .028
    block=thickness-2*cover-2*(.0011 if kind=='Hardback' else .00008)
    for i in range(3):
        bpy.data.objects['V138_'+kind+'_PageHinge_'+str(i)].location.y=-block/2-.0003-(2-i)*.00012
    name=kind+'_Endpaper'
    if name not in bpy.data.objects:
        mesh=bpy.data.meshes.new(name);mesh.from_pydata([(.0035,cover/2+.00008,-.1055),(.1565,cover/2+.00008,-.1055),(.1565,cover/2+.00008,.1055),(.0035,cover/2+.00008,.1055)],[],[(0,1,2,3)])
        mesh.materials.append(bpy.data.materials['V138_Paper']);ob=bpy.data.objects.new(name,mesh);col.objects.link(ob);ob.parent=bpy.data.objects['V138_'+kind+'_FrontHinge']
for name in ['INTERACT_Vinyl_6','PROJECT_VINYL_V126_Outline_6','PROJECT_VINYL_V126_Record_6']:
    bpy.data.objects[name].hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
