"""Four approved photo crops, mapped upright left-to-right onto existing cards."""
import bpy,os,json
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert bpy.data.filepath.endswith('v146-seated-blank-vinyl.blend')
target=os.path.join(os.path.dirname(bpy.data.filepath),'lofi-room-cathode-glm53f-city-v147-personal-polaroids.blend')
assert not os.path.exists(target)
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
before={o.name:list(v for row in o.matrix_world for v in row) for o in s.objects}
order=sorted([bpy.data.objects[f'SHELF_Polaroid_{c}_Photo'] for c in 'ABCD'],key=lambda o:o.matrix_world.translation.y,reverse=True)
audit=[]
for i,ob in enumerate(order,1):
    path=os.path.join(ROOT,f'public/room/polaroid-art/v147/photo-{i}.png')
    assert os.path.isfile(path),path
    image=bpy.data.images.load(path,check_existing=False);image.name=f'V147_Polaroid_{i}';image.pack()
    mat=bpy.data.materials.new(f'V147_Polaroid_{i}_Grayscale');mat.use_nodes=True
    nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial')
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Linear';tex.extension='EXTEND'
    bw=nt.nodes.new('ShaderNodeRGBToBW');bw.name='Neutral grayscale print'
    nt.links.new(tex.outputs['Color'],bw.inputs[0])
    emit=nt.nodes.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=.65
    nt.links.new(bw.outputs[0],emit.inputs['Color']);nt.links.new(emit.outputs[0],out.inputs['Surface'])
    mat['polaroid_texture']=f'/room/polaroid-art/v147/photo-{i}.png'
    mat['photo_order']=i
    # Only the top photo face gets an image; thin sides keep their dark material.
    ob.data=ob.data.copy();ob.data.materials.append(mat);index=len(ob.data.materials)-1
    uv=ob.data.uv_layers.active or ob.data.uv_layers.new(name='PolaroidImageUV')
    xs=[v.co.x for v in ob.data.vertices];ys=[v.co.y for v in ob.data.vertices]
    for p in ob.data.polygons:
        if p.normal.z>.9:
            p.material_index=index
            for li in p.loop_indices:
                v=ob.data.vertices[ob.data.loops[li].vertex_index].co
                # Local +X runs toward viewer-right; local +Y points up the print.
                uv.data[li].uv=((v.x-min(xs))/(max(xs)-min(xs)),(v.y-min(ys))/(max(ys)-min(ys)))
    ob['photo_left_to_right']=i
    audit.append({'position':i,'object':ob.name,'image':image.name,'path':mat['polaroid_texture'],'grayscale':True,'packed':bool(image.packed_file)})
assert all(before[o.name]==list(v for row in o.matrix_world for v in row) for o in s.objects)
camera=bpy.data.objects.new('CAM_V147_Polaroid_Review',bpy.data.cameras.new('CAM_V147_Polaroid_Review'))
s.collection.objects.link(camera);camera.location=(1.93,1.39,1.67)
camera.rotation_euler=(Vector((2.49,1.39,.975))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=55
# Keep the scene's original active camera and all existing animation untouched.
bpy.ops.wm.save_as_mainfile(filepath=target)
outdir=os.path.join(ROOT,'blender/outputs/review-v147');os.makedirs(outdir,exist_ok=True)
with open(os.path.join(outdir,'polaroid-audit.json'),'w') as f:json.dump({'orderedPhotos':audit,'existingTransformsUnchanged':True,'existingFramesPreserved':True},f,indent=2)
print('V147_POLAROIDS_SAVED',target)
