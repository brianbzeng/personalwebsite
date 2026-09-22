"""Retain the exact rendered shelf camera moves as editable Blender actions."""
import bpy
s=bpy.context.scene
assert 'v137-shelf-book-lamp-glow' in bpy.data.filepath
assert 'CAM_ShelfApproach_v137' not in bpy.data.objects
old=bpy.data.objects['CAM_Website_Pans_v119'];end=bpy.data.objects['CAM_Shelf_records_v137']
def pose(c):return c.matrix_world.translation.copy(),c.matrix_world.to_quaternion(),c.data.lens,c.data.shift_y
def ease(t):return t*t*(3-2*t)
def clone(name):
    c=bpy.data.objects.new(name,old.data.copy());c.data.animation_data_clear();s.collection.objects.link(c);c.rotation_mode='QUATERNION';return c
def key(c,frame,p):
    c.location=p[0];c.rotation_quaternion=p[1];c.data.lens=p[2];c.data.shift_y=p[3]
    c.keyframe_insert('location',frame=frame);c.keyframe_insert('rotation_quaternion',frame=frame)
    c.data.keyframe_insert('lens',frame=frame);c.data.keyframe_insert('shift_y',frame=frame)
approach=clone('CAM_ShelfApproach_v137')
s.frame_set(277);oldend=pose(old);newend=pose(end)
for reverse in (False,True):
    for i in range(73):
        frame=(301 if reverse else 205)+i;s.frame_set(frame);p=pose(old);weight=1-ease(i/72) if reverse else ease(i/72)
        key(approach,frame,(p[0]+(newend[0]-oldend[0])*weight,p[1].slerp(newend[1],weight),p[2],p[3]*(1-weight)))
nav=clone('CAM_ShelfNavigation_v137')
cubbies=[bpy.data.objects['CAM_Shelf_'+name+'_v137'] for name in ('books','records','photos')]
for start,(a,b) in zip((1,49,97,145),((1,0),(0,1),(1,2),(2,1))):
    pa,pb=pose(cubbies[a]),pose(cubbies[b])
    for i in range(37):
        t=ease(i/36);key(nav,start+i,(pa[0].lerp(pb[0],t),pa[1].slerp(pb[1],t),pa[2],pa[3]))
nav['clip_ranges']='1-37 records to books; 49-85 books to records; 97-133 records to photos; 145-181 photos to records'
approach['clip_ranges']='205-277 room to records; 301-373 records to room'
s.frame_set(277);bpy.context.view_layer.update()
assert (approach.matrix_world.translation-end.matrix_world.translation).length<1e-6
s.frame_set(1);s.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('V137_CAMERAS_SAVED',flush=True)
