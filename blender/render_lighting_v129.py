"""Render the full ten-second lighting study without modifying the saved scene."""
import bpy, os, json
s=bpy.context.scene
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'outputs/lighting-v129')
folder=os.path.join(out,'idle-study-frames'); os.makedirs(folder,exist_ok=True)
s.render.resolution_percentage=100
s.eevee.taa_render_samples=8; s.eevee.volumetric_samples=16
checks=[]
for index, frame in enumerate(range(2,241,2),1):
    s.frame_set(frame)
    s.render.filepath=os.path.join(folder,f'{index:04d}.png')
    bpy.ops.render.render(write_still=True)
    checks.append({'frame':frame,'flashes':{m.name:next(n for n in m.node_tree.nodes if n.type=='EMISSION').inputs['Strength'].default_value for m in bpy.data.materials if m.name.startswith('CATHODE_V129_QuickFlash_')},'lightning':bpy.data.objects['CTRL_LightningSync'].get('lightning_strength')})
    print('LIGHTING_FRAME',frame,flush=True)
with open(os.path.join(out,'animation-audit.json'),'w') as f:json.dump(checks,f)
print('LIGHTING_ANIMATION_COMPLETE',flush=True)
