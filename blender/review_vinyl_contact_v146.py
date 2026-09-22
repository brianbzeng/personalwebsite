"""Isolated geometry QA only; does not save or re-record room footage."""
import bpy,os
from mathutils import Vector
assert bpy.data.filepath.endswith('v146-seated-blank-vinyl.blend')
main=bpy.context.scene;main.frame_set(1);bpy.context.view_layer.update()
qa=bpy.data.scenes.new('V146_Contact_QA');qa.render.engine='BLENDER_WORKBENCH'
qa.render.resolution_x=1000;qa.render.resolution_y=800;qa.render.resolution_percentage=100
qa.display.shading.light='STUDIO';qa.display.shading.color_type='MATERIAL';qa.display.shading.show_shadows=True;qa.display.shading.show_cavity=False
qa.world=bpy.data.worlds.new('V146_QA_World');qa.world.color=(.04,.04,.04);qa.display.shading.background_type='WORLD'
qa.view_settings.view_transform='Standard'
gray=bpy.data.materials.new('V146_QA_Gray');gray.diffuse_color=(.10,.10,.10,1)
black=bpy.data.materials.new('V146_QA_Black');black.diffuse_color=(.002,.002,.002,1)
deps=bpy.context.evaluated_depsgraph_get()
for name in [f'{prefix}{i}' for i in range(7) for prefix in ('INTERACT_Vinyl_','PROJECT_VINYL_V126_Outline_')]:
    ob=bpy.data.objects[name];me=bpy.data.meshes.new_from_object(ob.evaluated_get(deps));me.materials.clear();me.materials.append(black if 'Outline' in name else gray)
    for p in me.polygons:p.material_index=0
    clone=bpy.data.objects.new('QA_'+name,me);qa.collection.objects.link(clone);clone.matrix_world=ob.matrix_world.copy()
cam=bpy.data.objects.new('V146_QA_Camera',bpy.data.cameras.new('V146_QA_Camera'));qa.collection.objects.link(cam);qa.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=.53;cam.location=(.6,1.73,1.66)
cam.rotation_euler=(Vector((2.5,1.73,1.51))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.window.scene=qa
qa.render.filepath=os.path.join(os.path.dirname(__file__),'outputs/review-v146/sleeve-contact.png')
bpy.ops.render.render(write_still=True)
