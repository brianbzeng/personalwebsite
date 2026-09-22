import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as THREE from 'three';
const root=new URL('../',import.meta.url);
const room=readFileSync(new URL('app/components/CinematicRoom.tsx',root),'utf8');
const shelf=readFileSync(new URL('app/components/BookshelfExperience.tsx',root),'utf8')+readFileSync(new URL('app/components/ShelfScene.tsx',root),'utf8');
const geometry=JSON.parse(readFileSync(new URL('public/room/v149/shelf-geometry.json',root),'utf8'));
const projects=JSON.parse(readFileSync(new URL('app/data/vinyls.json',root),'utf8'));
const module={exports:{}};
vm.runInNewContext(ts.transpileModule(readFileSync(new URL('app/components/vinylInteraction.ts',root),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:module.exports});
const {dragVinyl,snapVinylFace}=module.exports;
test('holder and diploma enter local views instead of redirecting',()=>{
  assert.match(room,/onClick=\{enterVinyls\}/);assert.match(room,/onClick=\{enterDiploma\}/);
  assert.match(room,/lazy\(\(\) => import\("\.\/VinylShelf"\)\)/);
  assert.doesNotMatch(room,/href="\/about" aria-label="About Brian"/);
});
test('five active sleeves are square and the two fixed covers retain their authored poses',()=>{
  assert.equal(geometry.objects.length,5);assert.equal(geometry.hoverTravel,.085);
  assert.equal(geometry.version,149);
  for(const object of geometry.objects){
    assert.equal(object.positions.length,72);assert.equal(object.indices.length,36);assert.equal(object.edges.length,12);
    assert.ok(object.positions.every(Number.isFinite));assert.ok(object.indices.every(i=>i>=0&&i<24));
    const x=object.positions.filter((_,i)=>i%3===0),z=object.positions.filter((_,i)=>i%3===2);
    assert.equal(Math.max(...x)-Math.min(...x),Math.max(...z)-Math.min(...z));
    assert.equal(object.uvs.length,48);
  }
  assert.deepEqual([...geometry.objects,...geometry.decorations].sort((a,b)=>b.origin[1]-a.origin[1]).map(o=>o.project),[0,1,2,3,4,5,6]);
  assert.ok(Math.abs(geometry.decorations[0].quaternion[0]+.1287912726)<1e-7,'rightmost sleeve retains its current evaluated lean, not the stale -0.29 rad export');
  assert.ok(geometry.decorations.every(o=>o.blank&&!o.interactive));
  assert.ok(geometry.outlineRadius>0);
});
test('selection inspects before navigation and supports touch, flip, and cleanup',()=>{
  for(const token of ['selected === result.value','pointercancel','setPointerCapture','Front / back','Return to holder','renderer.dispose()']) {
    assert.ok(shelf.includes(token),token);
  }
  assert.match(shelf,/import\("three"\)/);
  assert.match(shelf,/CylinderGeometry/);
  assert.doesNotMatch(shelf,/LineBasicMaterial/);
  assert.doesNotMatch(shelf,/window.location.assign/);
  assert.match(shelf,/\(\{ turn, tilt \} = snapVinylFace\(turn\)\); needsPaint = true/);
});

test('five project links stay intact while the final two covers are blank decorations',()=>{
  assert.deepEqual(projects.map(p=>p.title),['CastingCompass','Amazon','F1 Constructor','NBA Home Win Predictor','TTB Label','','']);
  assert.ok(projects.slice(5).every(p=>p.decorative&&p.summary===''&&p.label===''));
  assert.deepEqual(projects.map(p=>p.href),['https://castingcompass.com','https://github.com/brianbzeng/amazonmodel','https://github.com/brianbzeng/f1model','https://nba.brianbzeng.com/','https://treasury.brianbzeng.com/',null,null]);
  for(const p of projects)for(const face of ['front','back','spine'])assert.ok(existsSync(new URL(`public/room/vinyl-art/${p.slug}-${face}.png`,root)));
  const generator=readFileSync(new URL('blender/create_vinyl_textures.mjs',root),'utf8');
  assert.match(generator,/translate\(64 448\) rotate\(90\)/);
});

test('vertical drag tips forward; horizontal drag direction is unchanged',()=>{
  const up=dragVinyl(0,0,0,-30),down=dragVinyl(0,0,0,30);
  assert.ok(up.tilt>0);assert.ok(down.tilt<0);
  const top=new THREE.Vector3(0,1,0).applyAxisAngle(new THREE.Vector3(1,0,0),up.tilt);
  assert.ok(top.z>0,'top edge moves toward the viewer in camera space');
  assert.equal(dragVinyl(0,0,30,0).turn,.36);
});

test('Front/Back always lands at an exact face with zero tilt after arbitrary drags',()=>{
  for(const turn of [-17.2,-4.1,-.3,0,.7,2.1,3.4,16.8]){
    const snapped=snapVinylFace(turn);assert.equal(snapped.tilt,0);
    assert.ok(Math.abs(Math.sin(snapped.turn))<1e-12);
    const second=snapVinylFace(snapped.turn);
    assert.ok(Math.abs(Math.cos(snapped.turn)+Math.cos(second.turn))<1e-12);
  }
});

test('return waits on a presented video frame while retaining the departing surface',()=>{
  assert.match(room,/requestVideoFrameCallback/);
  for(const phase of ['vinyl-out','books-out','photos-out','diploma-out','return'])assert.match(room,new RegExp(`phase\\s*===\\s*["']${phase}["']`));
  assert.match(room,/\(phase === "vinyl-out" \|\| phase === "books-out" \|\| phase\s*===\s*['"]photos-out['"]\) && holdingReturn/);
  const css=readFileSync(new URL('app/components/cinematicRoom.css',root),'utf8');
  assert.match(css,/\.cinematic-transition \{ opacity: 0; \}/);
});
