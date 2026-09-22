import bpy, os
s=bpy.context.scene
s.render.resolution_percentage=33
s.eevee.taa_render_samples=4
s.eevee.volumetric_samples=8
s.render.image_settings.file_format='PNG'
s.render.image_settings.color_mode='RGB'
folder=os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath),'../../camera-pan-preview-v119'))
os.makedirs(folder,exist_ok=True)
for index,frame in enumerate(range(1,577,3)):
    s.frame_set(frame)
    s.render.filepath=os.path.join(folder,f'{index:04d}.png')
    bpy.ops.render.render(write_still=True)
