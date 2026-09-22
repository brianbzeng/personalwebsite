"""Level the display and attach independent edge guides to each stand part."""
import bpy
from mathutils import Matrix,Vector

body=bpy.data.objects['INTERACT_Monitor_Body']
screen=bpy.data.objects['INTERACT_Monitor_Screen']
old=bpy.data.objects['GLM_MONITOR_V19_CleanOutline']
pivot=screen.matrix_world.translation.copy()
rotation=Matrix.Rotation(-body.rotation_euler.y,4,'Y')
undo=Matrix.Translation(pivot)@rotation@Matrix.Translation(-pivot)
body.matrix_world=undo@body.matrix_world
screen.matrix_world=undo@screen.matrix_world

outline=old.copy();outline.data=old.data.copy()
outline.name='GLM_MONITOR_V105_LevelDisplayOutline'
old.users_collection[0].objects.link(outline)
outline.matrix_world=undo@old.matrix_world
for index in [2,1]:outline.data.splines.remove(outline.data.splines[index])
world=outline.matrix_world.copy();outline.parent=body
outline.matrix_world=world
old.hide_set(True);old.hide_render=True

for name in ['DESK_MonitorBase','DESK_MonitorStem']:
    source=bpy.data.objects[name]
    data=bpy.data.curves.new(name+'_V105_AlignedEdges','CURVE')
    data.dimensions='3D';data.bevel_depth=old.data.bevel_depth;data.bevel_resolution=2
    data.materials.append(old.data.materials[0])
    for edge in source.data.edges:
        s=data.splines.new('POLY');s.points.add(1)
        for p,index in zip(s.points,edge.vertices):p.co=(*source.data.vertices[index].co,1)
    ob=bpy.data.objects.new(data.name,data);source.users_collection[0].objects.link(ob)
    ob.parent=source;ob.matrix_parent_inverse=Matrix.Identity(4)
    ob.matrix_basis=Matrix.Identity(4)
    ob['alignment']='Local mesh edges; follows stand part independently of display'
print('Display leveled; stand outlines rebuilt and parented to their own meshes')
