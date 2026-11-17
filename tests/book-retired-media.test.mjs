import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const read=name=>readFileSync(new URL('../app/components/'+name,import.meta.url),'utf8');
function load(name,require=()=>({})){
  const exports={};
  vm.runInNewContext(ts.transpileModule(read(name),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports,require});
  return exports;
}
function modules(enabled){
  const state=enabled===undefined?load('shelfState.ts'):{BOOK_EXPERIENCE_ENABLED:enabled};
  const plates=load('panHandoff.ts',name=>name==='./shelfState'?state:{});
  const cache=load('sceneTransitionCache.ts',name=>name==='./shelfState'?state:plates);
  return {state,plates,cache};
}

test('retired books use unhighlighted media for every active room pan and exit preload',()=>{
  const {state,cache}=modules();
  assert.equal(state.BOOK_EXPERIENCE_ENABLED,false);
  for(const coherent of [false,true]){
    const media=cache.sceneMedia(coherent,coherent);
    for(const phase of ['vinyl-in','vinyl-out','photos-in','photos-out','diploma-in','diploma-out'])
      assert.equal(cache.sceneTransitionSrc(phase,media),`/room/v163/${phase}.mp4`);
    assert.equal(cache.sceneTransitionSrc('approach',media),'/room/v163/monitor-in.mp4');
    assert.equal(cache.sceneTransitionSrc('return',media),'/room/v163/monitor-out.mp4');
    assert.equal(cache.shelfExitSrc(1,coherent,coherent),cache.sceneTransitionSrc('vinyl-out',media));
    assert.equal(cache.shelfExitSrc(2,coherent,coherent),cache.sceneTransitionSrc('photos-out',media));
  }
});

test('retired photo plates and shelf moves share v163 without inventing new vinyl plates',()=>{
  const {plates}=modules();
  for(const coherentPhotos of [false,true])for(const coherentBooks of [false,true]){
    const values=plates.getShelfPlates(coherentPhotos,coherentBooks);
    assert.equal(values,plates.getShelfPlates(coherentPhotos,coherentBooks),'stable arrays preserve preload effects');
    assert.equal(values[2].still,'/room/v163/photos-still.webp');
    assert.equal(values[2].background,'/room/v163/photos-background.webp');
    assert.equal(values[1].still,'/room/v156/vinyl-still.webp?v=157');
    assert.equal(values[1].background,'/room/v156/vinyl-background.webp?v=157');
    for(const [from,to] of [[1,2],[2,1]])
      assert.equal(plates.shelfTravelClip(from,to,coherentPhotos,coherentBooks),`/room/v163/shelf-${from}-${to}.mp4`);
  }
  assert.match(read('CinematicRoom.tsx'),/initialCubby===1\?`\$\{SHELF_MEDIA\}vinyl-still.webp\?v=157`/);
});

test('reenabling books preserves the earlier media recipes',()=>{
  const {plates,cache}=modules(true);
  assert.equal(cache.sceneMedia().shelf,'/room/v155/');
  assert.equal(cache.sceneMedia(true,true).photos,'/room/v159/');
  assert.equal(cache.sceneMedia(true,true).books,'/room/v160/');
  assert.equal(plates.getShelfPlates(true,true)[2].still,'/room/v159/photos-still.webp');
  assert.equal(plates.shelfTravelClip(1,2,true,true),'/room/v159/shelf-1-2.mp4');
});
