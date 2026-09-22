import bpy,json
s=bpy.context.scene
names=['BRIDGE_V41_FlushOutline_Object_3','V102_Structural_No_Hanger_Overlap','CATHODE_WIREFRAME_DESK_MousePad','CATHODE_WIREFRAME_DESK_Mouse']
for name in names:
 o=bpy.data.objects[name];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
 print(name,'visible',o.visible_get(),'hide',o.hide_render,o.hide_viewport,'collections',[(c.name,c.hide_render,c.hide_viewport) for c in o.users_collection],'bounds',list(e.dimensions))
def walk(l,path):
 if l.exclude or l.collection.hide_render or l.collection.hide_viewport:print('COL',path+'/'+l.name,'exclude',l.exclude,'render',l.collection.hide_render,'viewport',l.collection.hide_viewport)
 for c in l.children:walk(c,path+'/'+l.name)
walk(bpy.context.view_layer.layer_collection,'')
