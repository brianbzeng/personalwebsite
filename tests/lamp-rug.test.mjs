import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL(`../${p}`,import.meta.url),'utf8');

test('translucency is isolated to the two shade meshes with original lighting and outlines preserved',()=>{
  const source=read('blender/translucent_lamps_v135.py');
  assert.match(source,/names = \['DESK_LampShade', 'FLOOR_LAMP_V129_DESK_LampShade'\]/);
  assert.match(source,/mat = original.copy\(\)/);
  assert.match(source,/opacity.inputs\[0\].default_value = .12/);
  assert.match(source,/light.energy = 3 if name == 'DESK_LampShade' else 4/);
  assert.match(source,/if n not in names/);
  assert.match(source,/assert all\(lights_before/);
  assert.match(source,/assert pulse_before ==/);
  assert.match(source,/mat.surface_render_method = 'DITHERED'/);
});

test('rug is reshaped under the bed together with its outline and fitted traveling sweep',()=>{
  const source=read('blender/bedside_rug_v136.py');
  assert.match(source,/names = \['RUG_Base', 'CATHODE_WIREFRAME_RUG_Base'\]/);
  assert.match(source,/new = \(\(.50, 2.65\), \(-2.70, .40\)\)/);
  assert.match(source,/obj.data = obj.data.copy\(\)/);
  assert.match(source,/scale.inputs\[1\].default_value = max\(values\)-min\(values\)/);
  assert.match(source,/assert all\(before/);
  assert.doesNotMatch(source,/bpy.data.objects.remove|bpy.ops.object.delete/);
});

test('combined lamps and rug footage and cursor mask have their own revision',()=>{
  assert.match(read('blender/render_room_v130.py'),/revision='136' if '--v136' in sys.argv/);
  assert.match(read('blender/render_hover_mask_v130.py'),/outputs\/web-room-v136' if '--v136' in sys.argv/);
  assert.match(read('blender/encode_room_v130.ps1'),/'136'/);
});
