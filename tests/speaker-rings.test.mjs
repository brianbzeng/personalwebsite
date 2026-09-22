import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const exports={};vm.runInNewContext(ts.transpileModule(read('app/components/speakerRings.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports});
test('pool contains eighteen distinct closed smooth rings centered on the emitter',()=>{
 assert.equal(exports.SPEAKER_RING_COUNT,18);assert.equal(new Set(exports.SPEAKER_RING_PATHS).size,18);
 for(let shape=0;shape<18;shape++){
  const p=exports.speakerRingPoints(shape),path=exports.SPEAKER_RING_PATHS[shape];
  assert.ok(path.endsWith(' Z'));assert.equal((path.match(/ C /g)||[]).length,24);
  for(const axis of ['x','y'])assert.ok(Math.abs(p.reduce((sum,v)=>sum+v[axis],0))<1e-9);
  assert.ok(p.every(v=>Number.isFinite(v.x)&&Number.isFinite(v.y)&&Math.hypot(v.x,v.y)>6));
 }
});
test('each shuffled pool is exhausted before reuse and refills never repeat consecutively',()=>{
 const pick=exports.createRingPicker(()=>.371);let previous=-1;
 for(let cycle=0;cycle<10;cycle++){
  const batch=[];for(let i=0;i<18;i++){const value=pick();assert.notEqual(value,previous);previous=value;batch.push(value);}
  assert.equal(new Set(batch).size,18);
 }
});
test('waves expand about zero without directional drift and resample only between emissions',()=>{
 const css=read('app/components/roomSpeakerActivity.css'),component=read('app/components/RoomSpeakerActivity.tsx');
 const wave=css.slice(css.indexOf('@keyframes speaker-wave'),css.indexOf('@keyframes speaker-note'));
 assert.doesNotMatch(wave,/translate/);assert.match(wave,/scale\(3.2\)/);
 assert.match(component,/onAnimationIteration/);assert.match(css,/vector-effect:non-scaling-stroke/);
});
