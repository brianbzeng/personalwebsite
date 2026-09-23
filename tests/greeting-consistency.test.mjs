import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read=path=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
const room=read('app/components/CinematicRoom.tsx');

test('approved greeting correction is promoted while retaining legacy source defaults',()=>{
  assert.match(room,/coherentGreeting = false/);
  assert.match(room,/const MEDIA = "\/room\/v149\/"/);
  assert.match(room,/const MONITOR_MEDIA = "\/room\/v149\/"/);
  assert.match(room,/greetingMedia=coherentGreeting\?'\/room\/v161\/':MEDIA/);
  assert.match(room,/monitorMedia=coherentGreeting\?'\/room\/v161\/':MONITOR_MEDIA/);
  assert.match(read('app/page.tsx'),/<CinematicRoom coherentGreeting coherentPhotos coherentBooks/);
  assert.match(read('app/review/greeting-consistency/page.tsx'),/<CinematicRoom coherentGreeting coherentPhotos coherentBooks mobileLayout activityCues refinedCues cueFadeIn fastTransitions \/>/);
});

test('greeting still, ambient video, handoff decoding and corrected pans share the version',()=>{
  assert.match(room,/image.src=`\$\{greetingMedia\}greeting.webp`/);
  assert.match(room,/src=\{`\$\{greetingMedia\}idle.mp4`\}/);
  assert.match(room,/: `\$\{greetingMedia\}greeting.webp`\}/);
  assert.match(room,/room: greetingMedia, monitor: monitorMedia, shelf: SHELF_MEDIA, books: booksMedia, photos: photosMedia/);
  assert.match(room,/image.src = `\$\{greetingMedia\}diploma.webp`/);
  assert.match(room,/ref=\{diplomaImage\} src=\{`\$\{greetingMedia\}diploma.webp`\}/);
  assert.match(room,/releaseHandoff,greetingMedia\]/);
  assert.doesNotMatch(room,/\$\{MEDIA\}(?:greeting.webp|idle.mp4|diploma.webp)/);
});

test('staging includes every corrected still and camera clip',()=>{
  for(const name of ['greeting.webp','idle.mp4','monitor-in.mp4','monitor-out.mp4','diploma-in.mp4','diploma-out.mp4','diploma.webp']){
    const bytes=readFileSync(new URL('../public/room/v161/'+name,import.meta.url));
    assert.ok(bytes.length>1000,`${name} must be a complete encoded asset`);
    if(name.endsWith('.mp4'))assert.equal(bytes.toString('ascii',4,8),'ftyp');
    else assert.equal(bytes.toString('ascii',8,12),'WEBP');
  }
});
