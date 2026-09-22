import bpy,os,json
s=bpy.context.scene
names=['CAM_APPROVED_GREETING_Restored_v119','CAM_MonitorRounded_v133','CAM_Website_Pans_v119']+[f'CAM_Shelf_{n}_v137' for n in ('books','records','photos')]
current={n:bpy.data.objects[n] for n in names}
source=os.path.join(os.path.dirname(bpy.data.filepath),'lofi-room-cathode-glm53f-city-v137-shelf-book-lamp-glow.blend')
with bpy.data.libraries.load(source,link=False) as (src,dst):dst.objects=list(names)
refs=dst.objects
for o in refs:s.collection.objects.link(o)
result=[]
for f in (1,73,121,128,241,277,301,373,397,469,493,565):
    s.frame_set(f);bpy.context.view_layer.update()
    for n,ref in zip(names,refs):
        o=current[n]
        result.append(dict(frame=f,name=n,positionError=(o.matrix_world.translation-ref.matrix_world.translation).length,angleError=o.matrix_world.to_quaternion().rotation_difference(ref.matrix_world.to_quaternion()).angle,lensError=o.data.lens-ref.data.lens,shiftError=o.data.shift_y-ref.data.shift_y,current=list(o.matrix_world.translation),approved=list(ref.matrix_world.translation)))
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'blender/outputs/web-room-v149/camera-audit.json')
with open(out,'w') as f:json.dump(result,f,indent=2)
print(json.dumps([r for r in result if r['frame']==1],indent=2))
