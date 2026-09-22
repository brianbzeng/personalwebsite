"""Pack the approved artwork into a new source; preserve all earlier versions."""
import bpy,os,json,shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert bpy.data.filepath.endswith('v148-delayed-record-spin.blend')
target=bpy.data.filepath.replace('v148-delayed-record-spin','v149-approved-project-covers')
assert not os.path.exists(target)
art=os.path.join(ROOT,'public/room/vinyl-art/v149');os.makedirs(art,exist_ok=True)
slugs=['castingcompass','amazon-review-audit','f1-constructors-forecast','nba-odds-predictor','ttb-label-review-assistant']
images={};audit=[]
for slug in slugs:
    for side in ('front','back','spine'):
        base=slug+'-'+side+'.png'
        draft='cover-approval-v7' if slug=='f1-constructors-forecast' and side=='front' else 'cover-approval-v4'
        source=os.path.join(ROOT,'public/room/vinyl-art',base) if side=='spine' else os.path.join(ROOT,'blender/outputs',draft,base)
        dest=os.path.join(art,base);assert not os.path.exists(dest);shutil.copy2(source,dest)
        image=bpy.data.images.load(dest,check_existing=False);image.name='V149_'+base;image.pack();images[base]=image
        audit.append({'file':base,'source':source,'packed':True})
changed=0
for material in bpy.data.materials:
    if not material.use_nodes:continue
    for node in material.node_tree.nodes:
        if node.type=='TEX_IMAGE' and node.image:
            base=os.path.basename(node.image.filepath)
            if base in images:node.image=images[base];changed+=1
bpy.context.scene.frame_set(1)
bpy.context.scene.camera=bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
bpy.context.scene['v149_release']='Approved cover artwork, prior player refinement and personal Polaroids; room renders freeze review-only motion.'
bpy.ops.wm.save_as_mainfile(filepath=target)
out=os.path.join(ROOT,'blender/outputs/web-room-v149');os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'cover-audit.json'),'w') as f:json.dump({'materialsUpdated':changed,'assets':audit},f,indent=2)
print('V149_COVERS_SAVED',target,flush=True)
