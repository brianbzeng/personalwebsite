import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL(`../${p}`,import.meta.url),'utf8');

test('white interaction revision targets the shared live emitter, not black fade branches',()=>{
  const source=read('blender/white_interactives_v134.py');
  assert.match(source,/shared = bpy.data.node_groups\['INTERACT_SharedAmberRhythm_v119'\]/);
  assert.match(source,/assert sorted\(users\) == sorted\(m.name for m in materials\)/);
  assert.match(source,/color.default_value = \(1, 1, 1, rgba\[3\]\)/);
  assert.match(source,/assert drivers ==/);
  assert.match(source,/assert before ==/);
  assert.match(source,/min\(strengths\) < .21 and max\(strengths\) > 1.39/);
  assert.doesNotMatch(source,/\.links\.(remove|new)|driver_remove|\.location\s*=|\.rotation_euler\s*=/);
});

test('white footage retains the approved rounded monitor camera and full ambient loop',()=>{
  const source=read('blender/render_room_v130.py');
  assert.match(source,/'134' if '--v134' in sys.argv/);
  assert.match(source,/CAM_MonitorRounded_v133' if revision in \('133','134','136'\)/);
  assert.match(source,/if revision not in \('130','133'\):render\('idle',list\(range\(1,241\)\),home\)/);
  assert.match(source,/min\(1,ease\(t\)\*2\)/);
});

test('room and shelf use white media consistently with neutral interaction controls',()=>{
  const room=read('app/components/CinematicRoom.tsx');
  const shelf=read('app/components/BookshelfExperience.tsx');
  const media=read('app/components/panHandoff.ts');
  const css=read('app/components/cinematicRoom.css')+read('app/components/vinylShelf.css');
  assert.match(room,/white highlights/);
  assert.doesNotMatch(room+shelf+media,/\/room\/v13[2345]\//);
  assert.match(shelf,/const shelfPlates=getShelfPlates\(coherentPhotos,coherentBooks\)/);
  assert.match(media,/still:'\/room\/v156\/vinyl-still.webp\?v=157'/);
  assert.match(media,/BOOK_CONSISTENCY_MEDIA='\/room\/v160\/'/);
  assert.match(css,/--room-highlight: #eee/);
  assert.doesNotMatch(css,/room-amber|edb369/);
  assert.match(css,/\/room\/v149\/room-outline-mask.png/);
});
