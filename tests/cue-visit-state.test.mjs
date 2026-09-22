import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import ts from 'typescript';
const read=path=>readFileSync(new URL(`../${path}`,import.meta.url),'utf8');
const compiled=ts.transpile(read('app/components/cueVisitState.ts'),{module:ts.ModuleKind.ESNext});
const {createCueVisitState,rememberCueVisit,learnShelfNavigation}=await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

test('a room visit remembers completed cubbies across shelf remounts, not page refresh',()=>{
  const room=createCueVisitState();
  rememberCueVisit(room,'cubby-1');
  rememberCueVisit(room,'cubby-2');
  assert.equal(room.completed.has('cubby-1'),true);
  assert.equal(room.completed.has('cubby-0'),false);
  const refreshedRoom=createCueVisitState();
  assert.equal(refreshedRoom.completed.size,0);
  assert.notEqual(refreshedRoom.completed,room.completed);
});
test('successful shelf navigation suppresses learned hover and scroll cues',()=>{
  const memory=createCueVisitState();
  assert.equal(memory.navigated,false);
  learnShelfNavigation(memory);
  rememberCueVisit(memory,'cubby-0');
  assert.equal(memory.navigated,true);
  const source=read('app/components/BookshelfExperience.tsx');
  assert.match(source,/if\(next !== cubby\)|if \(next !== cubby\)/);
  assert.match(source,/!refinedCues\|\|!visitMemory\.navigated\)cue\('hover-records'/);
  assert.match(source,/!refinedCues\|\|!visitMemory\.navigated\)cueSpecs\.push\(\{id:'shelf-scroll'/);
});
test('approved refinements are promoted, book target is stable, labels distinguish photos from gallery',()=>{
  const home=read('app/page.tsx');
  assert.match(home,/coherentBooks.*refinedCues/);
  assert.doesNotMatch(home,/shelfReview/);
  assert.match(read('app/review/activity-cues/page.tsx'),/coherentBooks.*refinedCues/);
  const shelf=read('app/components/BookshelfExperience.tsx');
  assert.match(shelf,/freezeTarget:refinedCues&&id==='choose-book'/);
  assert.match(shelf,/label:refinedCues\?'Click':'Click to Enlarge'/);
  assert.match(shelf,/id:'enlarge-photos',label:'Click to Enlarge'/);
  assert.match(shelf,/viewportAnchor:\{x:\.955,y:\.5\},scale:1\.35/);
  assert.match(shelf,/visibleMs=\{refinedCues\?2000:undefined\}/);
  const room=read('app/components/CinematicRoom.tsx');
  assert.match(room,/cueMemory=\{shelfCueMemory\.current\}/);
  assert.match(room,/visibleMs=\{refinedCues\?2000:3000\}/);
});
