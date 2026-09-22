import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,statSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as T from 'three';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('four equal cards fly in order and return exactly to their original shelf poses',async()=>{
 const photoModel=JSON.parse(read('public/review/v154/photos.json'));
 const exports={};vm.runInNewContext(ts.transpileModule(read('app/components/shelfPolaroids.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports,fetch:async()=>({ok:true,json:async()=>photoModel})});
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(22.8951925,16/9,.01,20),spec=JSON.parse(read('public/room/v149/shelf-geometry.json')).cubbies[2];camera.position.fromArray(spec.camera);camera.quaternion.fromArray(spec.quaternion);
 const gallery=await exports.createPolaroidGallery({...T,TextureLoader:class{async loadAsync(){return new T.Texture();}}},scene,camera,()=>true,()=>{},()=>{});
 const cards=scene.children.filter(o=>o instanceof T.Group).sort((a,b)=>a.userData.photoIndex-b.userData.photoIndex),origins=cards.map(o=>({p:o.position.clone(),q:o.quaternion.clone()}));assert.equal(cards.length,4);
 assert.deepEqual(origins.slice(1).map(o=>o.p.toArray()),[[2.455,1.31,.978],[2.48,1.455,.96],[2.47,1.25,.96]]);
 assert.ok(Math.abs(origins[0].p.z-.96699534)<1e-6);assert.ok(Math.abs(origins[0].p.x-2.465)<1e-6);assert.ok(Math.abs(origins[0].p.y-1.52)<1e-6);
 const paperNormal=new T.Vector3(0,0,1).applyQuaternion(origins[0].q);assert.ok(Math.abs(paperNormal.angleTo(new T.Vector3(0,0,1))-Math.PI/40)<1e-6);
 assert.equal(exports.PHOTO_LABELS.join('|'),'Las Vegas selfie|Escape room group|Friends at night|Fishing trip');
 const paperMaterials=cards.flatMap(c=>c.children.flatMap(mesh=>Array.isArray(mesh.material)?mesh.material:[mesh.material])).filter(m=>m?.color?.getHex()===0x848484);
 assert.equal(paperMaterials.length,4);assert.ok(paperMaterials.every(m=>m.toneMapped===false));
 const prints=cards.flatMap(c=>c.children.flatMap(mesh=>Array.isArray(mesh.material)?mesh.material:[mesh.material])).filter(m=>m?.map);
 assert.equal(prints.length,4);assert.ok(prints.every(m=>Math.abs(m.color.r-.65*Math.pow(2,-.3))<1e-8&&m.toneMapped===false));
 const hit=scene.children.find(o=>o instanceof T.Mesh&&o.userData.selection==='photos');assert.ok(hit.geometry.parameters.depth>=.12);assert.equal(hit.material.opacity,0);
 let now=0;const advance=n=>{for(let i=0;i<n;i++)gallery.update(now+=16);};gallery.open();advance(6);assert.ok(cards[0].position.distanceTo(origins[0].p)>0);assert.ok(cards[1].position.distanceTo(origins[1].p)<1e-8);advance(10);assert.ok(cards[1].position.distanceTo(origins[1].p)>0);assert.ok(cards[2].position.distanceTo(origins[2].p)<1e-8);advance(100);
 const positions=cards.map(c=>c.position.clone().project(camera)),widths=cards.map(c=>{c.updateMatrixWorld(true);const box=new T.Box3().setFromObject(c);return box.getSize(new T.Vector3()).length();});
 for(let i=1;i<4;i++){assert.ok(Math.abs(widths[i]-widths[0])<1e-5);assert.ok(positions[i].x>positions[i-1].x);assert.ok(Math.abs(positions[i].y-positions[0].y)<1e-6);}
 assert.ok(Math.abs((positions[1].x-positions[0].x)-(positions[3].x-positions[2].x))<1e-6);
 gallery.inspect(2);advance(40);const done=gallery.close();advance(140);await done;
 cards.forEach((c,i)=>{assert.ok(c.position.distanceTo(origins[i].p)<1e-8);assert.ok(c.quaternion.angleTo(origins[i].q)<1e-6);assert.equal(c.scale.x,1);});gallery.dispose();
});
test('direct photo pan and clean backdrop exist, and the book repository link is preserved',()=>{
 for(const file of ['photos-in.mp4','photos-out.mp4','photos-still.webp'])assert.ok(statSync(new URL('../public/room/v154/'+file,import.meta.url)).size>1000);
 assert.ok(statSync(new URL('../public/room/v152/photos-background.webp',import.meta.url)).size>1000);
 assert.match(read('app/components/CinematicRoom.tsx'),/PHOTOS_MEDIA = '\/room\/v154\/'/);
 assert.match(read('app/components/CinematicRoom.tsx'),/cubby===2\?'photos-out'/);
 const book=JSON.parse(read('public/books/f1/book.json'));assert.equal(book.pages.length,234);assert.match(book.pages[0].html,/class="repository"/);assert.match(book.pages[0].html,/https:\/\/github.com\/brianbzeng\/f1-stewarding-analysis/);
});
