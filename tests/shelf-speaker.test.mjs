import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
function load(p,imports={}){const exports={};vm.runInNewContext(ts.transpileModule(read(p),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports,require:id=>imports[id]});return exports;}
const {swipeBookDirection, swipeCubbyDirection, wheelPixels}=load('app/components/shelfGestures.ts');
const {speakerIsPlaying}=load('app/components/speakerPlayback.ts',{'./spotifyRefresh':{SPOTIFY_ACTIVE_REFRESH_MS:60000}});
test('touch follows document-scroll direction and ignores taps/horizontal drags',()=>{
 assert.equal(swipeCubbyDirection(4,-90),1);assert.equal(swipeCubbyDirection(4,90),-1);
 for(const [x,y] of [[0,20],[90,50],[0,0],[90,-80]])assert.equal(swipeCubbyDirection(x,y),null);
 assert.equal(wheelPixels(3,1,800),48);assert.equal(wheelPixels(1,2,800),800);assert.equal(wheelPixels(70,0,800),70);
});
test('shelf gestures are bounded, momentum-gated, and disabled while inspecting',()=>{
 const s=read('app/components/BookshelfExperience.tsx');
 assert.match(s,/selected !== null \|\| busyRef.current/);assert.match(s,/next !== cubby/);
 assert.match(s,/state.consumed = true/);assert.match(s,/event.ctrlKey/);assert.match(s,/onPointerCancelCapture/);
 assert.match(s,/passive: false/);
});
test('book rewinds before cover closure and only then deselects/returns',()=>{
 const s=read('app/components/ShelfScene.tsx');
 assert.match(s,/prepareTurn\(next,160\)/);assert.match(s,/spread - closing.step/);assert.match(s,/Math.ceil\(spread\/5\)/);
 assert.match(s,/const firstLeft=textureCache.get\('0:true'\)/);
 assert.match(s,/if\(!pageTurn\)turnHinge.visible=false/);
 assert.match(s,/closing && !pageTurn && opening === 0/);
 assert.match(s,/closing.position/);assert.match(s,/returnToShelf: \(\) => returnItem\(true\)/);
 assert.match(s,/opening === 0 && !closing && selected === null/);
});
test('horizontal book swipes ignore taps, diagonal and vertical cubby gestures',()=>{
 assert.equal(swipeBookDirection(-90,4),1);assert.equal(swipeBookDirection(90,4),-1);
 for(const [x,y] of [[20,0],[50,90],[0,0],[-80,90]])assert.equal(swipeBookDirection(x,y),null);
 const s=read('app/components/BookshelfExperience.tsx');
 assert.match(s,/onClickCapture/);assert.match(s,/suppressClickUntil/);assert.match(s,/controls.current\?\.page\(direction\)/);
});
test('only fresh active Spotify playback emits speaker activity',()=>{
 const now=100000,feed={status:'ready',isPlaying:true,song:{id:'track'},updatedAt:now-1000};
 assert.equal(speakerIsPlaying(feed,now),true);
 for(const changed of [{status:'unavailable'},{status:'disconnected'},{isPlaying:false},{song:null},{updatedAt:now-60000},{updatedAt:now+1},{updatedAt:NaN}])assert.equal(speakerIsPlaying({...feed,...changed},now),false);
 for(const invalid of [null,undefined,{},'playing'])assert.equal(speakerIsPlaying(invalid,now),false);
});
test('production uses live playback; simulation remains confined to review controls',()=>{
 const room=read('app/components/CinematicRoom.tsx'),effect=read('app/components/RoomSpeakerActivity.tsx');
 assert.match(room,/speakerPreview = false/);assert.match(room,/!speakerPreview \|\| speakerMode === "live"/);
 assert.match(room,/speakerPreview && phase === "room" && <aside/);
 assert.match(effect,/fetch\("\/api\/spotify"/);assert.doesNotMatch(effect,/method:\s*"POST"|\/me\/player/);
 for(const s of ['document.hidden','controller !== request','request.signal.aborted','clearTimeout(expiry)','controller?.abort()','650','aria-hidden="true"'])assert.ok(effect.includes(s),s);
 assert.match(read('app/components/roomSpeakerActivity.css'),/opacity 600ms ease/);
});
