import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
const room = read('app/components/CinematicRoom.tsx');
const shelf = read('app/components/BookshelfExperience.tsx');
const desktop = read('app/components/MonitorDesktop.tsx');

test('approved cues and mobile layout are promoted without staging redirect suppression', () => {
  assert.match(read('app/page.tsx'), /<CinematicRoom coherentGreeting coherentPhotos coherentBooks mobileLayout activityCues refinedCues cueFadeIn fastTransitions \/>/);
  assert.doesNotMatch(read('app/page.tsx'), /shelfReview/);
  assert.match(read('app/desktop/page.tsx'), /<MonitorDesktop mobileLayout \/>/);
  assert.match(room, /activityCues && shelfReview && \(phase==='vinyls'\|\|phase==='diploma'\)/);
  assert.match(room, /activityCues = false/);
  assert.match(shelf, /activityCues=false/);
  assert.doesNotMatch(desktop, /ActivityCues/);
  assert.match(read('app/review/activity-cues/page.tsx'), /<CinematicRoom coherentPhotos coherentBooks shelfReview mobileLayout activityCues refinedCues cueFadeIn \/>/);
  assert.match(read('app/review/activity-desktop/page.tsx'), /<MonitorDesktop mobileLayout \/>/);
  assert.match(room, /mobileLayout&&shelfReview\?'\/review\/mobile-desktop':'\/desktop'/);
});

test('each activity family explicitly opts into the shared cue layer', () => {
  assert.match(room, /activityCues && phase==='room' && !greetingCuesDone && <ActivityCues/);
  assert.match(room, /activityCues && phase==='diploma' && <ActivityCues/);
  assert.match(room, /activityCues=\{activityCues && phase==='vinyls'\}/);
  assert.match(shelf, /onCueTargets=\{activityCues\?setCueTargets:undefined\}/);
  assert.match(shelf, /activityCues&&<ActivityCues/);
  assert.match(shelf, /ready=\{ready&&!busy&&!turning&&!travel&&!failed&&cueSpecs.length>0&&\(!refinedCues\|\|!visitMemory.completed.has/);
  assert.doesNotMatch(desktop, /sceneKey="workstation"/);
});

test('greeting is arrow-only, two seconds in staging and three live, consumed on leaving or completion', () => {
  assert.match(room, /visibleMs=\{refinedCues\?2000:3000\} allowReplay=\{false\}/);
  assert.match(room, /onComplete=\{\(\)=>setGreetingCuesCompleted\(true\)\}/);
  assert.match(room, /if\(phase!=='room'&&!leftRoom\)setLeftRoom\(true\)/);
  assert.match(room, /const greetingCuesDone=greetingCuesCompleted\|\|leftRoom/);
  assert.equal((room.match(/appearance:'arrow-only'/g)||[]).length, 5);
  assert.match(room, /targetInset:\{top:\.65,right:refinedCues\?\.72:\.25\}/);
  assert.match(room, /targetInset:\{bottom:\.55\}/);
});

test('desktop notes removed, other review replay never enables hover dismissal', () => {
  assert.match(room, /dispatchEvent\(new Event\('bz-replay-cues'\)\)/);
  assert.doesNotMatch(desktop, /ActivityCues|WORKSTATION_CUES|bz-cues|bz-replay-cues/);
  const cueLayer = read('app/components/ActivityCues.tsx');
  assert.match(cueLayer, /ACTIVITY_CUE_VISIBLE_MS = 4000/);
  assert.doesNotMatch(cueLayer, /onMouseEnter|onPointerEnter|onMouseOver/);
});

test('record actions have precise labels and photos have a single arrow-free caption', () => {
  assert.match(shelf, /cue\('rotate-cover','cover','Drag','Drag','top','drag'\)/);
  assert.match(shelf, /cue\('flip-cover','cover','Flip','Flip','left'\)/);
  assert.match(shelf, /cue\('play-disc','disc','Redirect','Redirect','right'\)/);
  assert.match(shelf, /id:'enlarge-photos',label:'Click to Enlarge',touchLabel:'Tap to Enlarge'[^\n]*appearance:'text-only'/);
  assert.doesNotMatch(shelf, /restore-photo/);
});

test('book mockups share room framing and can preview touch without changing device behavior', () => {
  const preview=read('app/review/book-cues/page.tsx');
  assert.match(preview, /data-viewport-fit="cover"/);
  assert.match(preview, /cueInput=\{input\}/);
  assert.match(preview, /Cue input preview/);
  assert.match(shelf, /cueInput='auto'/);
  assert.match(shelf, /inputMode=\{cueInput\}/);
});

test('approved book swipe arrow orientations point outward', () => {
  assert.match(shelf, /'previous-spread','page-left','Click','Swipe','left','point','swipe-left'/);
  assert.match(shelf, /'next-spread','page-right','Click','Swipe','right','point','swipe-x'/);
});
