import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');

test('approved playback and sleeve return run on the main site; staging still suppresses redirects',()=>{
  const code=read('app/components/ShelfScene.tsx');
  assert.match(code,/const films=props\.cubby===1\?await loadPlaybackFilms\(\):null/);
  assert.match(code,/if\(!returnedFromPlayer&&typeof selected==='number'&&latest\.current\.motion\)/);
  assert.match(code,/if\(props\.review\)return/);
});

test('the decoded endpoint survives until two paint boundaries; stale releases cannot uncover a new pan',()=>{
  const exports={},frames=[];
  const react={useRef:current=>({current}),useCallback:f=>f,useEffect:()=>{}};
  vm.runInNewContext(ts.transpileModule(read('app/components/panHandoff.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,
    {exports,require:()=>react,requestAnimationFrame:f=>frames.push(f)});
  const h=exports.usePanHandoff(),node={style:{},dataset:{},getContext:()=>({drawImage:()=>{}})};
  h.canvas.current=node;
  const video={readyState:2,videoWidth:1920,videoHeight:1080};
  h.capture(video);h.release();assert.equal(node.dataset.holding,'true');
  frames.shift()();assert.equal(node.dataset.holding,'true');
  h.capture(video);frames.shift()();assert.equal(node.dataset.holding,'true');
  h.release();frames.shift()();frames.shift()();assert.equal(node.dataset.holding,'false');
});

test('return uses the real reversed arm samples, fades the disc, and goes straight to its slot',()=>{
  const code=read('app/components/shelfPlaybackStaging.ts');
  assert.match(code,/player.update\(returning.armFrame/);
  assert.match(code,/record.position.z\+=returning.lift\*\.16/);
  assert.match(code,/composite\(returning.discOpacity,'record'\)/);
  assert.match(code,/sleeve.position.copy\(shelfPose.position\)/);
  assert.doesNotMatch(code,/returnToInspect/);
  const exports={},timing=JSON.parse(read('app/data/shelf-return.json'));
  vm.runInNewContext(ts.transpileModule(read('app/components/shelfReturnMotion.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,
    {exports,require:()=>({default:timing})});
  assert.equal(timing.panDuration,3);
  assert.ok(timing.liftDuration>=1.2);
  assert.ok(timing.fadeStart+timing.fadeDuration<timing.panStart);
  for(let t=0;t<=exports.RETURN_SECONDS;t+=1/120){
    const pose=exports.shelfReturnPose(t);
    if(pose.discOpacity>0)assert.equal(pose.camera,1,'camera must remain locked until disc disappears');
    if(pose.camera>0)assert.equal(pose.coverOpacity,0,'cover returns only after arrival');
  }
  const end=exports.shelfReturnPose(exports.RETURN_SECONDS+.001);
  assert.equal(end.insert,1);assert.equal(end.camera,0);assert.equal(end.discOpacity,0);
  assert.match(code,/\(RETURN_SECONDS\+5\)\*1000/);
});

test('room shortcuts remain accessible without floating label popups',()=>{
  const room=read('app/components/CinematicRoom.tsx');
  assert.match(room,/aria-label="Room shortcuts"/);
  assert.match(room,/aria-label="Enter monitor"/);
  assert.doesNotMatch(room,/<span>Monitor ↗|<span>Projects ↗/);
  assert.match(room,/<PolaroidPulse/);
});
