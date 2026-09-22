import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const root = new URL('../', import.meta.url);
const read = p => readFileSync(new URL(p, root));
const hash = p => createHash('sha256').update(read(p)).digest('hex');
const slugs = ['castingcompass','amazon-review-audit','f1-constructors-forecast','nba-odds-predictor','ttb-label-review-assistant'];

test('released covers exactly match approval, including the final smaller F1 flag', () => {
  for (const slug of slugs) for (const face of ['front','back']) {
    const approval = slug === 'f1-constructors-forecast' && face === 'front' ? 'v7' : 'v4';
    assert.equal(hash(`public/room/vinyl-art/v149/${slug}-${face}.png`), hash(`blender/outputs/cover-approval-${approval}/${slug}-${face}.png`));
  }
});

test('spines are unchanged and all fifteen textures are packed into the new scene', () => {
  for (const slug of slugs) assert.equal(hash(`public/room/vinyl-art/v149/${slug}-spine.png`), hash(`public/room/vinyl-art/${slug}-spine.png`));
  const audit = JSON.parse(read('blender/outputs/web-room-v149/cover-audit.json'));
  assert.equal(audit.assets.length, 15);
  assert.ok(audit.assets.every(image => image.packed));
});

test('interactive and review texture loaders point at the approved versioned artwork', () => {
  const source = read('app/components/ShelfScene.tsx').toString();
  assert.match(source, /\/room\/vinyl-art\/v149\//);
  assert.doesNotMatch(source, /\?v=126/);
  const review = JSON.parse(read('public/review/v138/player.json'));
  const paths = review.meshes.flatMap(mesh => mesh.materials).map(material => material.texture).filter(Boolean);
  assert.ok(paths.length > 0);
  assert.ok(paths.every(p => p.startsWith('/room/vinyl-art/v149/')));
});

test('all release cameras preserve the approved framing, not the review close-up', () => {
  const audit = JSON.parse(read('blender/outputs/web-room-v149/camera-audit.json'));
  assert.equal(new Set(audit.map(r => r.name)).size, 6);
  for (const row of audit) {
    assert.ok(row.positionError < .00001, `${row.name} at ${row.frame}`);
    assert.ok(Math.min(row.angleError, Math.abs(row.angleError-2*Math.PI)) < .001);
    assert.equal(row.lensError, 0); assert.equal(row.shiftError, 0);
  }
  const prep = read('blender/prepare_room_render_v149.py').toString();
  assert.match(prep, /PROJECT_VINYL_V126_Record_6/);
  assert.match(prep, /o.animation_data_clear\(\)/);
  assert.match(prep, /Restore approved greeting before rendering/);
});
