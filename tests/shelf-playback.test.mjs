import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as T from 'three';
import ts from 'typescript';
import vm from 'node:vm';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const exports={};vm.runInNewContext(ts.transpileModule(read('app/components/bookPageMotion.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports});
test('actual mesh binding column stays fixed across both directions and the whole turn',()=>{
 const w=.16,h=.198,thick=.037,g=new T.PlaneGeometry(w*.98,h*.97,32,24);g.rotateX(Math.PI/2);g.translate(w*.49,0,0);
 const a=g.getAttribute('position'),right=new T.Matrix4().makeTranslation(-w/2,-thick/2-.0025,0);
 const left=new T.Matrix4().makeTranslation(-w/2,-thick/2,0).multiply(new T.Matrix4().makeRotationZ(-Math.PI)).multiply(new T.Matrix4().makeTranslation(0,.0025,0));
 for(let row=0;row<25;row++){const i=row*33,x=a.getX(i),z=a.getZ(i);assert.ok(Math.abs(x)<1e-8);
  const rest=new T.Vector3(x,0,z).applyMatrix4(right),other=new T.Vector3(x,0,z).applyMatrix4(left);assert.ok(rest.distanceTo(other)<1e-7);
  for(const direction of [-1,1])for(let frame=0;frame<=100;frame++){const p=exports.pageTurnVertex(x,z,w*.98,h*.97,frame/100,.9,direction);assert.ok(new T.Vector3(p.x,p.y,p.z).applyMatrix4(right).distanceTo(rest)<1e-7);}
 }g.dispose();
});
test('nearest cover surface wins; exposed record uses playback, not a face flip',()=>{
 const source=read('app/components/ShelfScene.tsx');
 assert.match(source,/intersectObjects\(scene.children, true\)\.find/);
 assert.match(source,/if\(result.result.object.userData.disc\)playRecord\(\)/);
 assert.match(source,/down && !down.dragged && !locked/);
 assert.match(source,/if\(locked\|\|typeof selected!==.*player/);
 assert.match(source,/PROJECTS\[id\]\.href/);
});
test('inspection and playback retain the same detailed two-sided disc and recorded timing',()=>{
 const scene=read('app/components/ShelfScene.tsx'),player=read('app/components/shelfRecordPlayer.ts');
 assert.match(scene,/player!\.record.clone\(true\)/);assert.doesNotMatch(scene,/CircleGeometry\(\.12/);
 assert.match(player,/foreground.attach\(record\)/);assert.match(player,/reverse.scale.z=-1/);
 assert.match(player,/record.position.addScaledVector\(offset,1-flight\)/);
 assert.doesNotMatch(player,/renderer.render\(player.background,camera\)/);
 assert.match(player,/renderer.render\(source,camera\)/);
 assert.match(player,/exitDirection\*\.31/);
 assert.match(player,/72\+seconds\*model.fps/);
 const model=JSON.parse(read('public/review/v138/player.json'));
 const parts=model.meshes.filter(m=>m.rig==='V138_Playback_Record_Rig');
 assert.equal(parts.filter(m=>m.name.startsWith('V138_Groove_')).length,5);
 const matrixAt=frame=>new T.Matrix4().fromArray(model.samples[frame-1].V138_Playback_Record_Rig.matrix);
 const positionAt=frame=>new T.Vector3().setFromMatrixPosition(matrixAt(frame));
 assert.ok(positionAt(88).distanceTo(new T.Vector3(2.465,1.173,1.4295))<1e-5);
 assert.ok(positionAt(138).distanceTo(positionAt(88))<1e-5);
 assert.equal((100-88)/model.fps,.5);
 assert.ok(matrixAt(99).equals(matrixAt(88)));
 assert.ok(!matrixAt(110).equals(matrixAt(100)));
});
test('corner controls prefetch neighbours, retain stationary hover and use inward touch targets',()=>{
 const scene=read('app/components/ShelfScene.tsx'),shelf=read('app/components/BookshelfExperience.tsx'),css=read('app/components/vinylShelf.css');
 assert.match(scene,/if\(report\)await preparePeeks\(\)/);
 assert.match(scene,/opening!==1/);
 assert.match(shelf,/matches\(':hover,:focus-visible'\)/);
 assert.match(shelf,/onPointerMove=\{\(\) => controls.current\?\.corner\(1\)/);
 assert.match(css,/clamp\(72px,8vw,112px\)/);
});
