"""Small approval stills only; no production animation re-recording."""
import bpy, os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out=os.path.join(root,'blender/outputs/review-v138')
s=bpy.context.scene
for m in bpy.data.materials:
    if m.use_nodes:
        fade=m.node_tree.nodes.get('Selected target fades to black')
        if fade:fade.inputs[0].default_value=1
for camera,frame,name in [('CAM_V138_Player_Review',1,'player-start'),('CAM_V138_Player_Review',122,'player-playing'),('CAM_V138_BookStack_Review',1,'stack-spacing')]:
    s.camera=bpy.data.objects[camera];s.frame_set(frame)
    s.render.resolution_x=1280;s.render.resolution_y=900;s.eevee.taa_render_samples=24
    s.render.filepath=os.path.join(out,name+'.png');bpy.ops.render.render(write_still=True)
bs=bpy.data.scenes['V138_Book_Prototypes']
bpy.context.window.scene=bs
for frame,name in [(1,'book-samples-closed'),(86,'book-samples-open')]:
    bs.frame_set(frame);bs.render.resolution_x=1280;bs.render.resolution_y=900;bs.eevee.taa_render_samples=24
    bs.render.filepath=os.path.join(out,name+'.png');bpy.ops.render.render(write_still=True)
print('V138_PROBES_COMPLETE',flush=True)
