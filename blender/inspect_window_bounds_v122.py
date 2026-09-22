from pathlib import Path
import bpy, json

root = Path(__file__).resolve().parent
src = root/'outputs'/'blender'/'lofi-room-cathode-v122-full-window-model-cleanup.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))

out=[]
for ob in bpy.data.objects:
    n=ob.name.lower()
    if ('window' in n or 'blind' in n) and ob.type=='MESH' and not n.startswith('cathode_windowray'):
        pts=[ob.matrix_world@v.co for v in ob.data.vertices]
        if not pts: continue
        out.append({'name':ob.name,'bounds':[round(x,4) for x in (min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts),min(p.z for p in pts),max(p.z for p in pts))]})
print('WINDOWS='+json.dumps(out,indent=2))
