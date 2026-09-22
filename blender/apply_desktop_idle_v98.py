"""Apply the approved ultrawide idle loop to the monitor front only."""
import bpy
from pathlib import Path

root = Path('C:/Users/Brian Zeng/Documents/Blender-Asset-Research/personalwebsite/blender/outputs')
movie = root / 'desktop-idle-ultrawide-2540x980-24fps.mp4'
target = root / 'blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v98-animated-macos-monitor.blend'
assert movie.is_file() and not target.exists()
screen = bpy.data.objects['INTERACT_Monitor_Screen']
assert len(screen.data.polygons) == 6
if screen.data.users > 1:
    screen.data = screen.data.copy()
front = [p for p in screen.data.polygons if p.normal.y < -0.99]
assert len(front) == 1
image = bpy.data.images.load(str(movie), check_existing=False)
image.name = 'Desktop_Idle_Ultrawide_240f'
image.colorspace_settings.name = 'sRGB'
mat = bpy.data.materials.new('Monitor_Animated_Desktop_V98')
mat.use_nodes = True
nodes = mat.node_tree.nodes
output = nodes.get('Material Output')
texture = nodes.new('ShaderNodeTexImage')
texture.image = image
texture.interpolation = 'Linear'
texture.extension = 'EXTEND'
texture.image_user.frame_duration = 240
texture.image_user.frame_start = 1
texture.image_user.frame_offset = 0
texture.image_user.use_cyclic = True
texture.image_user.use_auto_refresh = True
emission = nodes.new('ShaderNodeEmission')
emission.inputs['Strength'].default_value = 1.0
mat.node_tree.links.new(texture.outputs['Color'], emission.inputs['Color'])
mat.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
texture.location = (-450, 120)
emission.location = (-150, 120)
output.location = (80, 120)
nodes.active = texture
uv = screen.data.uv_layers.active or screen.data.uv_layers.new(name='UVMap')
xs = [v.co.x for v in screen.data.vertices]
zs = [v.co.z for v in screen.data.vertices]
for li in front[0].loop_indices:
    co = screen.data.vertices[screen.data.loops[li].vertex_index].co
    uv.data[li].uv = ((co.x-min(xs))/(max(xs)-min(xs)), (co.z-min(zs))/(max(zs)-min(zs)))
screen.data.materials.append(mat)
front[0].material_index = len(screen.data.materials)-1
screen.data.update()
bpy.context.scene.frame_set(1)
image.filepath = '//../../desktop-idle-ultrawide-2540x980-24fps.mp4'
bpy.ops.wm.save_as_mainfile(filepath=str(target))
print('Saved animated monitor version:', target.name)
