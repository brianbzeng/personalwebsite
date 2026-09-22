import bpy, os
s=bpy.context.scene
assert 'v129-lamp-lighting-preview' in bpy.data.filepath
for o in s.objects:
    if o.type=='LIGHT' and any(k in o.name for k in ['Lightning','StormFlash']): o.data.diffuse_factor=.015
s.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
s.eevee.taa_render_samples=8; s.eevee.volumetric_samples=16
folder=os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs/lighting-v129/idle-study-frames')
# All other sampled frames have zero weather-light energy and stay identical.
for frame in range(126,135,2):
    s.frame_set(frame); s.render.filepath=os.path.join(folder,f'{frame//2:04d}.png'); bpy.ops.render.render(write_still=True)
