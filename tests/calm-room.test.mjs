import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,statSync} from 'node:fs';
const read=path=>readFileSync(new URL(`../${path}`,import.meta.url),'utf8');
const room=read('app/components/CinematicRoom.tsx');
const css=read('app/components/cinematicRoom.css');
const render=read('blender/render_room_v130.py');
const prepare=read('blender/prepare_room_v130.py');

test('idle includes the authored frame-128 lightning flash in its full 240-frame cycle',()=>{
  assert.match(render,/render\('idle',list\(range\(1,241\)\),home\)/);
  assert.match(read('blender/audit_room_v130.py'),/flash\[128\]==1/);
  assert.match(read('blender/encode_room_v130.ps1'),/240/);
});
test('monitor uses two straights and a rounded bend without rightward overshoot',()=>{
  const camera=read('blender/prepare_monitor_v133.py');
  assert.match(camera,/corner = Vector\(\(0, -4.2\)\)/);
  assert.match(camera,/xy = origin.lerp\(entry, distance\/first\)/);
  assert.match(camera,/xy = leave.lerp\(finish/);
  assert.match(camera,/bisect.bisect_right\(distances, d\)/);
  assert.match(camera,/assert all\(p\[0\] <= 1e-6 for p in samples\)/);
  assert.match(camera,/assert all\(a\[2\] >= b\[2\]/);
  assert.match(camera,/originalTransformsUnchanged=True/);
  assert.match(render,/render\('monitor-in',list\(range\(1,122\)\),monitor,'Monitor'\)/);
  assert.match(render,/render\('monitor-out',list\(range\(121,242\)\),monitor,'Monitor',True\)/);
});
test('whole-room glow is masked, non-intercepting, motion-gated and fades after movement',()=>{
  assert.match(room,/phase === "room" && motion && pageVisible && <div ref=\{roomGlow\}/);
  assert.match(room,/event.pointerType === "touch"/);
  assert.match(room,/glowFade.current = setTimeout/);
  assert.match(css,/mask-image: url\('\/room\/v149\/room-outline-mask.png'\)/);
  assert.match(css,/\.cinematic-outline-glow[^}]+pointer-events: none/);
  assert.ok(statSync(new URL('../public/room/v149/room-outline-mask.png',import.meta.url)).size<350_000);
  const mask=read('blender/render_hover_mask_v130.py');
  assert.match(mask,/wire or flowing or contour/);
  assert.match(mask,/and not amber/);
  assert.match(mask,/slot.link='DATA'/);
  assert.match(mask,/CATHODE_V129_QuickFlash_/);
});
test('approved soft lamp lighting is retained while brief flashes gain spatial travel',()=>{
  const study=read('blender/preview_lamps_v129.py');
  assert.match(prepare,/v129-lamp-lighting-preview/);
  assert.match(study,/offset\+1,\.65/);
  assert.match(study,/offset\+4,0/);
  assert.match(study,/spot_blend=\.85/);
  assert.match(study,/\['Vinyl','Diploma','Monitor'\]/);
  assert.match(read('blender/prepare_room_v131.py'),/CATHODE_V129_QuickFlash_/);
  assert.match(read('blender/prepare_room_v131.py'),/CATHODE_V131_Travel_/);
});
test('floor lamp loses one third of height with its attached lights following',()=>{
  assert.match(prepare,/new_top=old_bottom\+\(old_top-old_bottom\)\*2\/3/);
  assert.match(prepare,/o.location.z-=drop/);
});
test('close-up return lighting starts at the still frame and ends at the matching idle time',()=>{
  assert.match(render,/render\('vinyl-still',\[277\],pan,'Vinyl',True,73\)/);
  assert.match(render,/73 if reverse else 1/);
  assert.match(render,/capture.data.animation_data_clear\(\)/);
  assert.match(render,/capture.matrix_world=pose/);
  assert.match(room,/idle.current.currentTime = phase === "return" \? 0 : 6/);
});
