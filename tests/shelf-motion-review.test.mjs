import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as T from 'three';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const exported={};vm.runInNewContext(ts.transpileModule(read('app/components/bookPageMotion.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:exported});
test('both stationary page faces stay inside the front board for every closing angle',()=>{
  for(let frame=0;frame<=200;frame++)for(const clearance of [.0025,.00225]){
    const opening=frame/200,angle=Math.PI*opening,p=exported.closingPageOffset(opening,clearance);
    for(let x=0;x<=.16;x+=.004){const distance=(x+p.x)*Math.sin(angle)+p.y*Math.cos(angle);assert.ok(distance>.002,'paper must clear the 4 mm thick cover');}
  }
  assert.ok(Math.abs(exported.closingPageOffset(1).y+.0025)<1e-9);
});
test('new sleeve origins and only decorative masks move together once',()=>{
  const old=JSON.parse(read('public/room/v149/shelf-geometry.json')),next=JSON.parse(read('public/room/v156/shelf-geometry.json'));
  old.objects.forEach((o,i)=>{assert.ok(Math.abs(next.objects[i].origin[0]-(o.origin[0]-.01))<1e-9);assert.deepEqual(next.objects[i].positions,o.positions);});
  old.occluders.forEach((o,i)=>o.positions.forEach((v,j)=>assert.ok(Math.abs(next.occluders[i].positions[j]-(v-(i>=3&&j%3===0?.01:0)))<1e-9)));
});
test('rerecorded camera is the original sample path, not a replacement zoom',()=>{
  const audit=JSON.parse(read('blender/outputs/web-room-v156/camera-audit.json'));
  const shelf=JSON.parse(read('public/room/v156/shelf-geometry.json')).cubbies[1],player=JSON.parse(read('public/review/v138/player.json')).camera;
  for(const a of audit){const frame=a.frame+1;const raw=a.sequence==='playback'?(frame-42)/46:1-(a.frame/24-.18)/.75;const t=Math.max(0,Math.min(1,raw)),w=t*t*(3-2*t);
    assert.ok(Math.abs(a.weight-w)<1e-8);
    const position=new T.Vector3().fromArray(shelf.camera).lerp(new T.Vector3().fromArray(player.position),w);
    assert.ok(position.distanceTo(new T.Vector3().fromArray(a.position))<1e-6);
    const vfov=shelf.verticalFov+(player.fov-shelf.verticalFov)*w,lens=36/(2*Math.tan(vfov*Math.PI/360)*(16/9));assert.ok(Math.abs(lens-a.lens)<1e-4);
  }
});
test('staging cannot automatically redirect and floating messages are fully removed',()=>{
  assert.match(read('app/components/ShelfScene.tsx'),/if\(props.review\)return/);
  for(const f of ['CinematicRoom','BookshelfExperience','ShelfScene'])assert.doesNotMatch(read(`app/components/${f}.tsx`),/InteractionHint|dismissInteractionHint/);
  assert.equal(existsSync(new URL('../app/components/InteractionHints.tsx',import.meta.url)),false);
});
