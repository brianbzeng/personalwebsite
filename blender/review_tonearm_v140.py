"""Finish the owned review's rear tube length and render isolated QA stills."""
import bpy, math, os, json
from mathutils import Vector, Matrix
assert bpy.data.filepath.endswith(('v140-reference-tonearm.blend','v141-solid-pivot-j-arm.blend','v142-detailed-pivot-rest.blend'))
is_v142=bpy.data.filepath.endswith('v142-detailed-pivot-rest.blend')
is_v141=bpy.data.filepath.endswith('v141-solid-pivot-j-arm.blend') or is_v142
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'blender/outputs/review-v142' if is_v142 else 'blender/outputs/review-v141' if is_v141 else 'blender/outputs/review-v140')
main=bpy.context.scene
if not is_v141:
    bpy.data.objects['V138_Tonearm'].data.splines[0].points[0].co.x=.026
    main.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    audit_path=os.path.join(OUT,'shape-audit.json')
    with open(audit_path) as f:audit=json.load(f)
    audit['rearTubeExtensionMm']=26
    with open(audit_path,'w') as f:json.dump(audit,f,indent=2)

# These isolated diagnostic stills do not change the saved scene or room footage.
qa=bpy.data.scenes.new('V140_Tonearm_QA')
qa.render.engine='BLENDER_WORKBENCH';qa.render.resolution_x=1100;qa.render.resolution_y=900;qa.render.resolution_percentage=100
qa.display.shading.light='STUDIO';qa.display.shading.color_type='MATERIAL'
qa.display.shading.show_shadows=True;qa.display.shading.show_cavity=True
qa.display.shading.background_type='WORLD';qa.world=bpy.data.worlds.new('V140_QA_Background');qa.world.color=(.055,.055,.055)
qa.view_settings.view_transform='Standard'
camdata=bpy.data.cameras.new('V140_QA_Camera');cam=bpy.data.objects.new('V140_QA_Camera',camdata);qa.collection.objects.link(cam);qa.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=.50
prefixes=('V138_Pivot_','V138_Tonearm','V138_ArmRest','V138_Headshell','V138_Stylus','V138_Player_Platter','V138_Platter','V138_Spindle','V138_PlayerBase_Edge_')
objects=[o for o in main.objects if (o.name.startswith(prefixes) or o.name=='INTERACT_RecordPlayer_Base' or o.name.startswith('INTERACT_RecordPlayer_Base_')) and not o.hide_render]
record=bpy.data.objects['V138_Playback_Record_Rig'];objects+=list(record.children_recursive)
shots=[(90,'overhead-rest',(2.44,1.115,2.3)),(122,'oblique-playing',(2.03,.73,1.91))]
if is_v142:shots += [(90,'pivot-closeup',(2.44,.875,1.51)),(122,'rest-closeup',(2.365,.875,1.51)),(98,'lift-clearance',(2.365,.875,1.51))]
for frame,label,position in shots:
    bpy.context.window.scene=main;main.frame_set(frame);bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    for ob in objects:
        if ob.type not in ('MESH','CURVE') or ob.hide_render:continue
        ev=ob.evaluated_get(deps);me=bpy.data.meshes.new_from_object(ev)
        clone=bpy.data.objects.new('QA_'+ob.name,me);qa.collection.objects.link(clone);clone.matrix_world=ob.matrix_world.copy()
    bpy.context.window.scene=qa;cam.location=position
    look=(2.565,.972,1.44) if label=='pivot-closeup' else (2.455,.972,1.437) if label in ('rest-closeup','lift-clearance') else (2.44,1.115,1.47)
    camdata.ortho_scale=.092 if label=='pivot-closeup' else .055 if label in ('rest-closeup','lift-clearance') else .50
    cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler()
    if label.startswith('overhead'):cam.rotation_euler=(0,0,math.pi/2)
    qa.render.filepath=os.path.join(OUT,label+'.png');bpy.ops.render.render(write_still=True)
    for ob in list(qa.objects):
        if ob!=cam:bpy.data.objects.remove(ob,do_unlink=True)
print('V140_QA_STILLS_COMPLETE',flush=True)
