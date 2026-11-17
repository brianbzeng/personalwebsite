"""Render the retired book region and retain original pixels elsewhere.

Original full-resolution raw frames are required. Render border keeps the
complete scene's lighting and depth, at original samples/color management.
Only the small book rectangle is composited; source assets are never modified.
"""
import bpy, os, math, subprocess, shutil
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

def patch_renderer(source_root):
    ffmpeg = shutil.which('ffmpeg')
    assert ffmpeg
    def render(path, name, index):
        source = os.path.join(source_root, name, f'{index:04d}.png')
        assert os.path.exists(source), source
        s = bpy.context.scene
        bpy.context.view_layer.update()
        obj = bpy.data.objects['CATHODE_WIREFRAME_BOOK_Mid_9']
        points = [world_to_camera_view(s, s.camera, obj.matrix_world @ Vector(v)) for v in obj.bound_box]
        w, h = s.render.resolution_x, s.render.resolution_y
        x0 = max(0, math.floor(min(v.x for v in points)*w)-12)
        x1 = min(w, math.ceil(max(v.x for v in points)*w)+12)
        y0 = max(0, math.floor(min(v.y for v in points)*h)-12)
        y1 = min(h, math.ceil(max(v.y for v in points)*h)+12)
        if x1<=x0 or y1<=y0 or all(v.z<0 for v in points):
            shutil.copyfile(source, path)
            return
        s.render.use_border = True
        s.render.use_crop_to_border = True
        # Blender truncates float32 border coordinates to pixel boundaries.
        # A half-pixel bias keeps them inside the intended integer bin instead
        # of occasionally truncating n-epsilon to n-1.
        s.render.border_min_x, s.render.border_max_x = (x0+.5)/w, min(1, (x1+.5)/w)
        s.render.border_min_y, s.render.border_max_y = (y0+.5)/h, min(1, (y1+.5)/h)
        crop = path + '.crop.png'
        s.render.filepath = crop
        bpy.ops.render.render(write_still=True)
        subprocess.run([ffmpeg,'-v','error','-y','-i',source,'-i',crop,
            '-filter_complex',f'[0:v][1:v]overlay={x0}:{h-y1}:format=rgb',
            '-frames:v','1','-threads','1',path],check=True)
        s.render.filepath = path
        s.render.use_border = False
        s.render.use_crop_to_border = False
    return render
