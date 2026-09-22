import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const json=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
const player=json('../public/review/v138/player.json');

test('record waits half a second after landing then spins on its fixed center',()=>{
  const landed=player.samples[87].V138_Playback_Record_Rig.matrix;
  for(let i=87;i<100;i++)assert.deepEqual(player.samples[i].V138_Playback_Record_Rig.matrix,landed);
  assert.notDeepEqual(player.samples[100].V138_Playback_Record_Rig.matrix,landed);
  for(const sample of player.samples.slice(87))assert.deepEqual(sample.V138_Playback_Record_Rig.matrix.slice(12,15),landed.slice(12,15));
  const a=player.samples[111].V138_Playback_Record_Rig.matrix;
  assert.ok(Math.abs(Math.atan2(a[1],a[0])+Math.PI*2*(100/3)/60*.5)<1e-5);
});

test('viewer-right blank sleeve rests against its neighbor and on the shelf',()=>{
  const audit=json('../blender/outputs/review-v146/contact-audit.json');
  assert.equal(audit.source,'INTERACT_Vinyl_0');assert.equal(audit.neighbor,'INTERACT_Vinyl_1');
  assert.ok(audit.leanPreserved&&audit.onlyAssemblyChanged);
  for(const sample of audit.samples){assert.ok(sample.outlineGap>.0001&&sample.outlineGap<.0002);assert.ok(Math.abs(sample.footHeightDifference)<1e-6);}
  const left=player.meshes.find(m=>m.name==='PROJECT_VINYL_V126_Outline_0'),right=player.meshes.find(m=>m.name==='PROJECT_VINYL_V126_Outline_1');
  const y=m=>m.positions.filter((_,i)=>i%3===1);
  const gap=Math.min(...y(right))-Math.max(...y(left));assert.ok(gap>.0001&&gap<.0002);
});

test('disc stays stationary throughout sleeve extraction, which moves viewer-left and fades',()=>{
  const start=player.samples[0].V138_Playback_Record_Rig.matrix;
  for(const frame of player.samples.slice(0,42))assert.deepEqual(frame.V138_Playback_Record_Rig.matrix,start);
  const first=player.samples[0].V138_Playback_Sleeve_Rig,last=player.samples[48].V138_Playback_Sleeve_Rig;
  assert.ok(last.matrix[13]-first.matrix[13]>.26);assert.equal(first.opacity,1);assert.equal(last.opacity,0);
  const fade=player.samples.map(s=>s.V138_Playback_Sleeve_Rig.opacity);
  for(let i=0;i<16;i++)assert.equal(fade[i],1,'cover holds opaque for the initial 0.2 seconds of sliding');
  assert.ok(fade[16]<1);assert.ok(Math.abs(fade[32]-.4906255)<1e-6);
  for(let i=1;i<fade.length;i++)assert.ok(fade[i]<=fade[i-1],'continuous monotonic fade after delay');
});
test('record lands before tonearm leaves its rest and the cue occurs after contact',()=>{
  const landed=player.samples[87].V138_Playback_Record_Rig.matrix;
  assert.ok(Math.abs(landed[12]-2.465)<1e-5);assert.ok(Math.abs(landed[13]-1.173)<1e-5);
  assert.deepEqual(player.samples[0].V138_Tonearm_Rig.matrix,player.samples[89].V138_Tonearm_Rig.matrix);
  const origin=player.samples[0].V138_Tonearm_Rig.matrix.slice(12,15);
  for(const frame of player.samples)assert.deepEqual(frame.V138_Tonearm_Rig.matrix.slice(12,15),origin);
  assert.notDeepEqual(player.samples[97].V138_Tonearm_Rig.matrix,player.samples[89].V138_Tonearm_Rig.matrix);
  const stylus=player.meshes.find(m=>m.name==='V138_Stylus');
  const tipAt=i=>{
    const m=player.samples[i].V138_Tonearm_Rig.matrix,points=[];
    for(let j=0;j<stylus.positions.length;j+=3){
      const [x,y,z]=stylus.positions.slice(j,j+3);
      points.push([m[0]*x+m[4]*y+m[8]*z+m[12],m[1]*x+m[5]*y+m[9]*z+m[13],m[2]*x+m[6]*y+m[10]*z+m[14]]);
    }
    return points.sort((a,b)=>a[2]-b[2])[0];
  };
  const rest=tipAt(89),raised=tipAt(97),contact=tipAt(121);
  assert.ok(raised[2]-rest[2]>.003&&raised[2]-rest[2]<.004,'small tip lift, not whole-arm translation');
  assert.ok(Math.abs(contact[2]-1.43105)<1e-5,'needle meets the lowered record surface');
  const radius=Math.hypot(contact[0]-2.465,contact[1]-1.173);
  assert.ok(radius>.109&&radius<.118,'needle lands at the outer grooves');
  const audit=json('../blender/outputs/review-v138/audit.json');assert.ok(audit.redirectFrame>audit.soundFrame);assert.ok(audit.soundFrame>98);
});
test('both bindings include separate covers, page blocks, endpapers, and turnable leaves',()=>{
  for(const kind of ['hardback','paperback']){
    const book=json(`../public/review/v138/${kind}.json`);
    for(const name of ['FrontCover','BackCover','PageBlock','Endpaper'])assert.ok(book.meshes.some(m=>m.name.endsWith(name)));
    assert.equal(book.meshes.filter(m=>m.bent).length,3);
  }
  const audit=json('../blender/outputs/review-v138/audit.json');for(const gap of audit.wireGapsMeters)assert.ok(gap>0&&gap<.001);
});
test('tonearm uses a fine contact needle, diagonal support and slim continuous rear tube',()=>{
  for(const old of ['V138_Tonearm_PivotBase','V138_Tonearm_PivotCap','V138_Counterweight'])assert.ok(!player.meshes.some(m=>m.name===old));
  for(const name of ['V138_Pivot_SolidDiagonalHousing','V138_Pivot_MountFlange','V138_Stylus_Cantilever'])assert.ok(player.meshes.some(m=>m.name===name));
  const needle=player.meshes.find(m=>m.name==='V138_Stylus');
  const extent=axis=>{const v=needle.positions.filter((_,i)=>i%3===axis);return Math.max(...v)-Math.min(...v);};
  assert.ok(extent(0)<.0004&&extent(1)<.0004,'sub-millimeter needle, not a rectangular peg');
  const arm=player.meshes.find(m=>m.name==='V138_Tonearm');
  const xs=arm.positions.filter((_,i)=>i%3===0);
  assert.ok(Math.max(...xs)>.025&&Math.max(...xs)<.030,'short shaft-like rear extension');
  const ys=arm.positions.filter((_,i)=>i%3===1);
  assert.ok(Math.max(...ys)>.026,'pronounced J-shaped terminal bend');
  const base=player.meshes.find(m=>m.name==='INTERACT_RecordPlayer_Base');
  const zs=base.positions.filter((_,i)=>i%3===2);
  assert.ok(Math.abs(Math.max(...zs)-Math.min(...zs)-.0375)<1e-5,'plinth height is halved');
  for(const frame of player.samples)assert.deepEqual(frame.V138_Pivot_YawRig.matrix.slice(12,15),frame.V138_Tonearm_Rig.matrix.slice(12,15),'housing and arm share a fixed bearing');
});
test('approved room release keeps review navigation isolated',()=>{
  const room=readFileSync(new URL('../app/components/CinematicRoom.tsx',import.meta.url),'utf8');assert.match(room,/const MEDIA = "\/room\/v149\/"/);
  const review=readFileSync(new URL('../app/review/player-books/review.tsx',import.meta.url),'utf8');assert.match(review,/animate\(1,138,navigate\?openProject:undefined,true\)/);assert.match(review,/generation.current\+\+/);assert.match(review,/child.opener=null/);
});
test('reference pivot has ordered concentric tiers, separate bearings/collar and molded rest clamp',()=>{
  const audit=json('../blender/outputs/review-v142/assembly-audit.json');
  assert.equal(audit.crossedOutCueLeverIncluded,false);assert.equal(audit.tiers.length,5);
  for(let i=1;i<audit.tiers.length;i++){
    assert.ok(audit.tiers[i].radius<audit.tiers[i-1].radius);
    assert.ok(Math.abs(audit.tiers[i].bottom-audit.tiers[i-1].top)<1e-7);
  }
  for(const name of ['V138_Pivot_SilverCollar','V138_Pivot_YokeBridge','V138_ArmRest_OpenClamp','V138_ArmRest_BackCheek'])assert.ok(player.meshes.some(m=>m.name===name));
  const cleanup=json('../blender/outputs/review-v143/cleanup-audit.json');
  assert.ok(cleanup.maxSleevePoseError<1e-6);
  for(const name of cleanup.hiddenObjects)assert.ok(!player.meshes.some(m=>m.name===name),`${name} removed from visible export`);
  assert.ok(!player.meshes.some(m=>/Cue.*Lever|LiftControlLever/.test(m.name)));
});

test('new physical contours share the player lighting sweep and circled socket tab is absent',()=>{
  const audit=json('../blender/outputs/review-v145/wire-audit.json');
  assert.ok(!player.meshes.some(m=>m.name===audit.hidden));
  assert.equal(audit.material,'CATHODE_V131_Travel_record-player');
  for(const name of audit.animatedContours){
    const mesh=player.meshes.find(m=>m.name===name);assert.ok(mesh);
    assert.ok(mesh.materials.every(m=>m.sweep&&m.unlit));
    assert.equal(mesh.materials[0].sweep.start,152);assert.equal(mesh.materials[0].sweep.duration,96);
  }
  const code=readFileSync(new URL('../app/review/player-books/review.tsx',import.meta.url),'utf8');
  assert.ok(!code.includes('m.transparent=opacity'),'no abrupt per-face transparency switch');
  assert.match(code,/mix\(texture2D\(backgroundImage,vUv\),texture2D\(fullImage,vUv\),opacity\)/);
});

test('player theme is grayscale with matte surfaces and attached silhouette-only outlines',()=>{
  const audit=json('../blender/outputs/review-v144/theme-audit.json');
  assert.equal(audit.fadeDelaySeconds,.2);assert.ok(audit.maxSleevePoseError<1e-6);
  for(const name of audit.themedParts){
    const mesh=player.meshes.find(m=>m.name===name);assert.ok(mesh);
    for(const mat of mesh.materials){assert.equal(mat.color[0],mat.color[1]);assert.equal(mat.color[1],mat.color[2]);assert.equal(mat.roughness,.9);}
  }
  for(const name of audit.silhouettes){
    const outline=player.meshes.find(m=>m.name===name),source=player.meshes.find(m=>m.name===name.replace('_ThemeOutline',''));
    assert.ok(outline&&source);assert.equal(outline.rig,source.rig);
    assert.ok(outline.materials.every(m=>m.unlit&&m.frontSide),'reverse-wound silhouette shells are front-side culled, not double-sided black copies');
  }
  assert.ok(!audit.silhouettes.some(n=>n.includes('Stylus')));
});
