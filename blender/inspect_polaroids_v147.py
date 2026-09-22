import bpy,json
from mathutils import Vector
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
for letter in 'ABCD':
 o=bpy.data.objects[f'SHELF_Polaroid_{letter}_Photo']
 print(json.dumps({'name':o.name,'location':list(o.matrix_world.translation),'matrix':[list(r) for r in o.matrix_world],'dims':list(o.dimensions),'verts':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'materials':[slot.material.name for slot in o.material_slots]}))
