"""Save a dedicated book camera, then render only its two local release clips."""
import bpy, os, sys
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene
root=os.path.dirname(os.path.abspath(__file__))
assert bpy.data.filepath.endswith('v149-approved-project-covers.blend')
old=bpy.data.objects['CAM_Website_Pans_v119']
home=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
end=bpy.data.objects['CAM_Shelf_books_v137']
def pose(c): return c.matrix_world.translation.copy(),c.matrix_world.to_quaternion(),c.data.lens,c.data.shift_y
def ease(t): return t*t*(3-2*t)
c=bpy.data.objects.new('CAM_BooksApproach_v150',old.data.copy())
c.data.animation_data_clear();s.collection.objects.link(c);c.rotation_mode='QUATERNION'
s.frame_set(277);oldend=pose(old);newend=pose(end)
poses={}
for reverse in (False,True):
    for i in range(73):
        s.frame_set((301 if reverse else 205)+i);p=pose(old);weight=1-ease(i/72) if reverse else ease(i/72)
        value=(p[0]+(newend[0]-oldend[0])*weight,p[1].slerp(newend[1],weight),p[2],p[3]*(1-weight))
        frame=(97 if reverse else 1)+i;poses[frame]=value
        c.location,c.rotation_quaternion,c.data.lens,c.data.shift_y=value
        c.keyframe_insert('location',frame=frame);c.keyframe_insert('rotation_quaternion',frame=frame)
        c.data.keyframe_insert('lens',frame=frame);c.data.keyframe_insert('shift_y',frame=frame)
c['clip_ranges']='1-73 room to top cubby; 97-169 top cubby directly to room'
s.frame_set(1);s.camera=home;bpy.context.view_layer.update()
assert (poses[1][0]-home.matrix_world.translation).length<1e-5
assert (poses[73][0]-end.matrix_world.translation).length<1e-5
book=bpy.data.objects['BOOK_Mid_9']
v=world_to_camera_view(s,home,book.matrix_world.translation)
print('BOOK_HOTSPOT',v.x,1-v.y,flush=True)
target=bpy.data.filepath.replace('v149-approved-project-covers','v150-direct-book-camera')
bpy.ops.wm.save_as_mainfile(filepath=target)
# Ephemeral release pose: never save the review/playback rigs in this state.
for name in ('INTERACT_Vinyl_6','PROJECT_VINYL_V126_Outline_6','PROJECT_VINYL_V126_Record_6'):bpy.data.objects[name].hide_render=False
for name in ('V138_Playback_Record_Rig','V138_Playback_Sleeve_Rig'):
    for o in bpy.data.objects[name].children_recursive:o.hide_render=True
for name in ('V138_Tonearm_Rig','V138_Pivot_YawRig'):
    o=bpy.data.objects[name];basis=o.matrix_basis.copy();o.animation_data_clear();o.matrix_basis=basis
c.animation_data_clear();c.data.animation_data_clear()
targets={slot.material.name for o in s.objects if 'Vinyl' in o.name for slot in o.material_slots if slot.material}
s.render.resolution_percentage=100;s.render.resolution_x=1920;s.render.resolution_y=1080
s.eevee.taa_render_samples=16;s.eevee.volumetric_samples=16
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
for reverse in (False,True):
    name='books-out' if reverse else 'books-in'
    folder=os.path.join(root,'outputs/web-room-v150',name);os.makedirs(folder,exist_ok=True)
    for i in range(73):
        s.frame_set((73 if reverse else 1)+i)
        c.location,c.rotation_quaternion,c.data.lens,c.data.shift_y=poses[(97 if reverse else 1)+i];s.camera=c
        amount=min(1,2*ease(1-i/72 if reverse else i/72))
        for m in bpy.data.materials:
            if m.use_nodes:
                fade=m.node_tree.nodes.get('Selected target fades to black')
                if fade:fade.inputs[0].default_value=amount if m.name in targets else 0
        s.render.filepath=os.path.join(folder,f'{i:04d}.png')
        if not os.path.exists(s.render.filepath):bpy.ops.render.render(write_still=True)
        print('V150_FRAME',name,i,flush=True)
print('V150_COMPLETE',flush=True)
