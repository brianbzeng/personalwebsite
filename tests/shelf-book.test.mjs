import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,statSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const exports={};vm.runInNewContext(ts.transpileModule(read('app/components/shelfState.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports});
const shelf=read('app/components/BookshelfExperience.tsx'),scene=read('app/components/ShelfScene.tsx');
const model=JSON.parse(read('public/room/v149/shelf-geometry.json'));
test('navigation is bounded to the three specified cubbies and begins at records',()=>{
  assert.deepEqual([...exports.CUBBIES],['Books','Records','Camera & photographs']);
  for(let i=0;i<3;i++)for(const d of [-1,1])assert.equal(exports.adjacentCubby(i,d),Math.max(0,Math.min(2,i+d)));
  assert.match(shelf,/\[cubby, setCubby\] = useState\(initialCubby\)/);
  assert.deepEqual(model.cubbies.map(c=>c.id),['books','records','photos']);
  for(const c of model.cubbies){assert.equal(c.camera[1],model.cubbies[1].camera[1]);assert.ok(Math.abs(c.target[1]-1.36)<1e-6);}
});
test('only first five records and the viewer-left top-stack book can be selected',()=>{
  for(const i of [-1,5,6,9,NaN,.5])assert.equal(exports.canSelectRecord(i),false);
  for(let i=0;i<5;i++)assert.equal(exports.canSelectRecord(i),true);
  assert.equal(model.book.name,'BOOK_Mid_9');assert.ok(model.book.body.indices.length>0);assert.ok(model.book.outline.indices.length>0);
  assert.match(scene,/if \(!canSelectRecord\(data.project\)\) continue/);
  assert.match(shelf,/PROJECTS.slice\(0, 5\)/);
});
test('book starts closed, cannot free-rotate, and has bounded blank spreads',()=>{
  assert.equal(exports.BLANK_SPREADS,3);
  assert.equal(exports.nextSpread(0,-1),0);assert.equal(exports.nextSpread(0,1),1);assert.equal(exports.nextSpread(2,1),2);assert.equal(exports.nextSpread(2,-1),1);
  assert.match(scene,/if \(typeof selected === "number"\) \(\{ turn, tilt \} = dragVinyl/);
  assert.match(scene,/item.id === "book" \? frontPose : turned/);
  assert.match(scene,/select\(value: ShelfSelection\)/);
  assert.match(scene,/open = false; corner = null; pageTurn = null/);
  assert.match(scene,/openedBook.visible = false/);
  assert.match(shelf,/aria-label="Previous spread"/);assert.match(shelf,/aria-label="Next spread"/);
  assert.match(scene,/deformTurn\(t,pageTurn.initialCurl,pageTurn.direction\)/);
});
test('camera handoffs wait for resting geometry and presented video frames',()=>{
  assert.match(shelf,/await controls.current\?\.settle\(\)/);
  assert.match(shelf,/requestVideoFrameCallback/);
  assert.match(scene,/settleResolve && distance < .00001 && opening === 0/);
  assert.match(shelf,/setTimeout\(onFailed, 8000\)/);
  assert.match(shelf,/if \(travel\) return/);
  assert.match(shelf,/!ready && !failed/);
});
test('new scene preserves existing transforms and broadens shade glow without opaque beams',()=>{
  const audit=JSON.parse(read('blender/outputs/web-room-v137/scene-audit.json'));
  assert.equal(audit.originalTransformsUnchanged,true);assert.equal(audit.shadeTransparency,.12);
  const prepare=read('blender/prepare_shelf_v137.py');assert.match(prepare,/shadow_soft_size=radius/);assert.match(prepare,/To Max/);
  assert.doesNotMatch(prepare,/ShaderNodeVolume|ShaderNodeBsdfDiffuse/);
});
test('shelf clips and compact geometry are available without loading a full room model',()=>{
  for(const name of ['shelf-1-0.mp4','shelf-0-1.mp4','shelf-1-2.mp4','shelf-2-1.mp4','books-still.webp','books-background.webp','photos-still.webp'])assert.ok(statSync(new URL('../public/room/v149/'+name,import.meta.url)).size<1_000_000);
  assert.ok(statSync(new URL('../public/room/v149/shelf-geometry.json',import.meta.url)).size<100_000);
});
