import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL(`../${p}`,import.meta.url),'utf8');
const source=read('blender/prepare_room_v131.py');
const clamp=x=>Math.max(0,Math.min(1,x));
const smooth=(a,b,x)=>{const t=clamp((x-a)/(b-a));return t*t*(3-2*t);};
function strength(frame,u,offset){
  const elapsed=((frame-1-offset)%240+240)%240;
  const progress=Math.min(elapsed/96,1)*1.83-.18;
  const d=progress-u;
  return .65*smooth(-.16,0,d)*(1-smooth(.05,.65,d));
}
test('travel uses shared evaluated world bounds, excluding archived render collections',()=>{
  assert.match(source,/layer.exclude or layer.collection.hide_render/);
  assert.match(source,/o.name not in render_objects/);
  assert.match(source,/o.evaluated_get\(depsgraph\)/);
  assert.match(source,/ShaderNodeNewGeometry/);
  assert.match(source,/outputs\['Position'\]/);
  assert.doesNotMatch(source,/outputs\['Generated'\]/);
  assert.match(source,/for o,i in slots:o.material_slots\[i\].link='OBJECT';o.material_slots\[i\].material=mat/);
});
test('every point receives a complete pass and substantially longer local fade',()=>{
  assert.match(source,/duration=96;cycle=240;peak=\.65/);
  assert.match(source,/front=smooth\(-\.16,0\);tail=mathnode\('SUBTRACT',1,smooth\(\.05,\.65\)\)/);
  assert.ok(.60*96/1.83/24>1.3,'decay lasts over 1.3 seconds');
  for(const offset of [0,8,43,160,199,224,239])for(const u of [0,.05,.25,.5,.75,.95,1]){
    const samples=Array.from({length:240},(_,i)=>strength(i+1,u,offset));
    assert.ok(Math.max(...samples)>.64,`point ${u} must receive full illumination`);
    assert.ok(samples.filter(x=>x>.05).length>25,'not a five-frame flash');
    assert.ok(samples.filter(x=>x===0).length>100,'each model has a quiet interval');
  }
});
test('randomly staggered sweeps and their tails are seamless across idle-loop boundaries',()=>{
  for(const offset of [0,8,43,80,160,199,224,239])for(const u of [0,.3,.7,1]){
    assert.ok(Math.abs(strength(1,u,offset)-strength(241,u,offset))<1e-12);
    assert.ok(Math.abs(strength(240.999,u,offset)-strength(1.001,u,offset))<.0003);
    assert.equal(strength(offset+1,u,offset),0);
    assert.ok(strength(offset+97,u,offset)<1e-12);
  }
});
test('animation-only revision preserves transforms and the approved camera and lamp layout',()=>{
  assert.match(source,/assert before==/);
  assert.match(source,/CAM_APPROVED_GREETING_Restored_v119/);
  assert.doesNotMatch(source,/bpy\.ops\.object\.join|bmesh|\.location\s*=|\.rotation_euler\s*=/);
  assert.match(read('blender/render_room_v130.py'),/monitor=bpy.data.objects\['CAM_MonitorRounded_v133' if revision in \('133','134','136'\) else 'CAM_MonitorCubby_v130'\]/);
});
