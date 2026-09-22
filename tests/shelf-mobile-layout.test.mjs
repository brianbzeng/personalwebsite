import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const api={};vm.runInNewContext(ts.transpileModule(read('app/components/shelfMobileLayout.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:api});
function geometry(width,height,margins){
 const stageHeight=width*9/16;
 const stage={left:0,top:(height-stageHeight)/2,width,height:stageHeight};
 const fit=api.visibleShelfFit(stage,{left:0,top:0,width,height},22.895192527,16/9,margins);
 return {fit,pixelsPerUnit:stageHeight/(2*1.2*Math.tan(22.895192527*Math.PI/360))};
}
test('landscape inspection fits visible viewport rather than cropped 16:9 host',()=>{
 for(const [width,height] of [[926,322],[844,290],[667,260],[1024,600]]){
  const margins={left:64,right:112,top:14,bottom:54};
  const {fit,pixelsPerUnit}=geometry(width,height,margins);
  const scale=api.shelfInspectionScale(fit,.16*2*1.1,.198*1.08,1.7);
  assert.ok(.198*1.08*scale*pixelsPerUnit<=height-68+.001);
  assert.ok(.16*2*1.1*scale*pixelsPerUnit<=width-176+.001);
  assert.ok(scale>0&&scale<=1.7);
  assert.ok(Math.abs(fit.y*pixelsPerUnit-20)<.001,'raise objects above bottom controls');
  assert.ok(Math.abs(fit.x*pixelsPerUnit+24)<.001,'reserve right book menu space');
 }
});
test('photo enlargement including forward lift remains inside usable height',()=>{
 for(const [width,height] of [[926,322],[844,290],[667,260]]){
  const {fit,pixelsPerUnit}=geometry(width,height);
  const large=Math.min(fit.height*.93/.20,fit.width*.78/.16);
  assert.ok(large*.20*pixelsPerUnit*(1.2/(1.2-.035))<=height-68);
 }
});
test('desktop is opt-in gated and playback/return preserve fitted scale continuity',()=>{
 const scene=read('app/components/ShelfScene.tsx'),gallery=read('app/components/shelfPolaroids.ts'),playback=read('app/components/shelfPlaybackStaging.ts');
 assert.match(scene,/latest.current.mobileLayout && window.matchMedia\(SHELF_MOBILE_QUERY\).matches/);
 assert.match(scene,/opening \* w \* scale \/ 2/);
 assert.match(scene,/recordReturn.scale\+\(1-recordReturn.scale\)/);
 assert.match(scene,/visualViewport\?\.addEventListener\('resize'/);
 assert.match(gallery,/mobileFit:\(\)=>ShelfFit\|null=\(\)=>null/);
 assert.match(playback,/record.scale.copy\(recordStartScale\).lerp/);
 assert.match(playback,/if\(returned\)sleeve.scale.setScalar\(1\)/);
});
