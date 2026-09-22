import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,statSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const exports={};vm.runInNewContext(ts.transpileModule(read('app/components/bookPageMotion.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports});
const {curlPageCorner,pageTurnPose,pageTurnVertex}=exports;
test('curl affects only the lower outside corner with no displacement at rest',()=>{
 for(const [x,z] of [[0,0],[.2,.15],[0,-.15]]){const p=curlPageCorner(x,z,.2,.3,1);assert.equal(p.x,x);assert.equal(p.y,0);assert.equal(p.z,z);}
 const flat=curlPageCorner(.2,-.15,.2,.3,0);assert.equal(flat.y,0);
 const curled=curlPageCorner(.2,-.15,.2,.3,1);assert.ok(curled.y<-.025&&curled.y>-.04);assert.ok(curled.x<.2&&curled.z>-.15);
 for(let x=0;x<=.2;x+=.01)for(let z=-.15;z<=.15;z+=.01)assert.ok(Object.values(curlPageCorner(x,z,.2,.3,1)).every(Number.isFinite));
});
test('page turn is flat at both endpoints and mirrored in reverse',()=>{
 for(const t of [0,.2,.5,.8,1]){const a=pageTurnPose(t,1),b=pageTurnPose(t,-1);assert.ok(Math.abs(a.angle+b.angle-Math.PI)<1e-12);assert.equal(a.bend,-b.bend);}
 assert.ok(Math.abs(pageTurnPose(0,1).bend)<1e-12);assert.ok(Math.abs(pageTurnPose(1,1).bend)<1e-12);
});
test('reading uses one visual surface and turns advance through adjacent leaves',()=>{
 const scene=read('app/components/ShelfScene.tsx'),css=read('app/components/reportBook.css'),overlay=read('app/components/ReportBookOverlay.tsx');
 assert.match(scene,/prepareTurn\(spread\+Math.sign\(journey.target-spread\)/);
 assert.match(scene,/turnHinge.position.set\(-w \/ 2, -thick \/ 2 - \.0025, 0\)/);
 assert.match(scene,/g.translate\(w \* \.49, 0, 0\)/);
 assert.match(scene,/material.polygonOffset=true/);
 assert.match(scene,/pageMap\(direction===1\?next\*2\+1:next\*2,direction===-1\)/);
 assert.match(scene,/leftPeekReady && corner === -1/);
 assert.match(scene,/rightPeekReady && corner === 1/);
 assert.doesNotMatch(scene,/turnHinge.rotation.z = -angle/);
 assert.match(scene,/leftCurl=0;rightCurl=0;deform\(leftPage.geometry,0\)/);
 assert.doesNotMatch(scene,/layoutVisible=.*leftCurl/);
 assert.match(css,/color:transparent!important/);
 assert.doesNotMatch(overlay,/report-panorama-bridge|Formula 1 stewarding · 2018–2025/);
 assert.match(overlay,/onJump\(0\)/);assert.match(overlay,/onJump\(book.pages.length-1\)/);
});
test('corner-led turn continues the hover curl, holds its spine and lands flat',()=>{
 for(const d of [-1,1])for(const x of [0,.03,.1,.196])for(const z of [-.145,0,.145]){
  const c=curlPageCorner(x,z,.196,.29,.8),p=pageTurnVertex(x,z,.196,.29,0,.8,d);
  assert.ok(Math.abs(p.x-d*c.x)<1e-10&&Math.abs(p.y-c.y)<1e-10&&Math.abs(p.z-c.z)<1e-10);
  const end=pageTurnVertex(x,z,.196,.29,1,.8,d);assert.equal(end.x,-d*x);assert.equal(end.y,0);assert.equal(end.z,z);
  for(const t of [.1,.4,.7,.99]){
   const q=pageTurnVertex(x,z,.196,.29,t,.8,d);assert.ok(Object.values(q).every(Number.isFinite));assert.ok(q.y<=0);
   if(x===0){assert.ok(q.x===0);assert.equal(q.y,0);assert.equal(q.z,z);}
  }
 }
});
test('transparent accessible corners replace arrows; instruction hints are absent',()=>{
 const shelf=read('app/components/BookshelfExperience.tsx');
 assert.doesNotMatch(shelf,/Hover to slide|Drag to turn|↶|↷/);
 assert.match(shelf,/onFocus=\{\(\) => controls.current\?\.corner\(1\)\}/);
 assert.match(read('app/components/ShelfScene.tsx'),/32, 24/);
});
test('dedicated books clips preserve direct return and remain lightweight',()=>{
 const room=read('app/components/CinematicRoom.tsx'),shelf=read('app/components/BookshelfExperience.tsx');
 assert.match(room,/BOOKS_MEDIA = "\/room\/v150\/"/);assert.match(room,/initialCubby=\{initialCubby\}/);
 assert.match(shelf,/moveTo\(cubby, true\)/);assert.match(shelf,/onExit\(cubby\)/);
 for(const name of ['books-in','books-out'])assert.ok(statSync(new URL('../public/room/v150/'+name+'.mp4',import.meta.url)).size<6_000_000);
});
