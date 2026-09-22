import bpy
import os

screen = bpy.data.objects['INTERACT_Monitor_Screen']
body = bpy.data.objects['INTERACT_Monitor_Body']
assert not body.get('standard_monitor_v106'), 'Already resized'
ratio = (screen.dimensions.z * 16 / 9) / screen.dimensions.x
body.scale.x *= ratio
screen.scale.x *= ratio
body['standard_monitor_v106'] = True
# The display outline is parented to the body; stand outlines stay independent.
movie = os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), '../../desktop-idle-skeleton-1920x1080-24fps.mp4'))
assert os.path.isfile(movie)
image = bpy.data.images.load(movie, check_existing=False)
image.name = 'Desktop_Idle_Skeleton_1080p_192f'
image.source = 'MOVIE'
image.filepath = bpy.path.relpath(movie)
for material in screen.data.materials:
    if not material or not material.use_nodes:
        continue
    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image and node.image.source == 'MOVIE':
            node.image = image
            node.image_user.frame_duration = 192
            node.image_user.frame_start = 1
            node.image_user.frame_offset = 0
            node.image_user.use_cyclic = True
            node.image_user.use_auto_refresh = True
bpy.context.view_layer.update()
print('Monitor aspect ratio:', screen.dimensions.x / screen.dimensions.z)
