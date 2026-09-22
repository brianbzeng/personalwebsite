import bpy
from mathutils import Matrix, Vector

frame = bpy.data.objects['BED_Frame_Carcass_Cohesive']
assert not frame.get('bed_enlarged_v109'), 'Already applied'
# Recess the covered foot end, leaving the visible head end unchanged.
for name in ['BED_Mattress', 'CATHODE_WIREFRAME_BED_Mattress']:
    obj = bpy.data.objects[name]
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        p = obj.matrix_world @ vertex.co
        if p.y > -1.2:
            p.y = -1.2 + (p.y + 1.2) * ((-.92 + 1.2) / (-.845 + 1.2))
            vertex.co = inverse @ p
    obj.data.update()

# Anchor at the rear wall-side corner, so expansion goes into the room.
pivot = Vector((2.66, -2.77, .06))
transform = Matrix.Translation(pivot) @ Matrix.Scale(1.15, 4) @ Matrix.Translation(-pivot)
names = ['BED_Blanket_FacetedContinuous', 'BED_Frame_Carcass_Cohesive', 'BED_Mattress', 'BED_Pillow']
for name in names:
    for target in [name, 'CATHODE_WIREFRAME_' + name]:
        obj = bpy.data.objects[target]
        obj.matrix_world = transform @ obj.matrix_world
frame['bed_enlarged_v109'] = True
bpy.context.view_layer.update()
print('Bed scaled 15%; mattress foot recessed with its outline.')
