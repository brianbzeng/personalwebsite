"""Project the real card edges for a room-space interaction highlight."""
import bpy,json,os
from bpy_extras.object_utils import world_to_camera_view
project=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
source=os.path.join(project,'blender/outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v156-restored-playback.blend')
bpy.ops.wm.open_mainfile(filepath=source)
scene=bpy.context.scene;scene.frame_set(1)
camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119'];scene.camera=camera
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
bpy.context.view_layer.update()
segments=[]
for letter in 'ABCD':
    obj=bpy.data.objects[f'SHELF_Polaroid_{letter}_Card']
    for edge in obj.data.edges:
        points=[]
        for vertex in edge.vertices:
            point=world_to_camera_view(scene,camera,obj.matrix_world@obj.data.vertices[vertex].co)
            points.append([round(point.x*1920,4),round((1-point.y)*1080,4)])
        segments.append(points)
target=os.path.join(project,'public/room/v157/polaroid-outlines.json')
os.makedirs(os.path.dirname(target),exist_ok=True)
with open(target,'w') as f:json.dump(segments,f,separators=(',',':'))
print('PHOTO_OUTLINES_EXPORTED',len(segments),flush=True)
