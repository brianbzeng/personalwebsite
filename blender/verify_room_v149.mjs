import { readFileSync, statSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../', import.meta.url));
const raw = path.join(root, 'blender/outputs/web-room-v149');
const release = path.join(root, 'public/room/v149');
const hash = p => createHash('sha256').update(readFileSync(p)).digest('hex');
const slugs = ['castingcompass','amazon-review-audit','f1-constructors-forecast','nba-odds-predictor','ttb-label-review-assistant'];
const artwork = [];
for (const slug of slugs) for (const face of ['front','back']) {
  const approval = slug === 'f1-constructors-forecast' && face === 'front' ? 'v7' : 'v4';
  const source = path.join(root, `blender/outputs/cover-approval-${approval}/${slug}-${face}.png`);
  const target = path.join(root, `public/room/vinyl-art/v149/${slug}-${face}.png`);
  assert.equal(hash(source), hash(target), `${slug} ${face}: approved artwork must remain exact`);
  artwork.push({slug, face, approval, sha256: hash(target)});
}
const videos = [];
for (const name of ['shelf-1-0','shelf-0-1','shelf-1-2','shelf-2-1','vinyl-in','vinyl-out','idle','monitor-in','monitor-out','diploma-in','diploma-out']) {
  const file = path.join(release, name+'.mp4');
  const { streams } = JSON.parse(execFileSync('ffprobe', ['-v','error','-show_streams','-of','json',file], {encoding:'utf8'}));
  assert.equal(streams.length, 1, `${name}: silent video only`);
  const s = streams[0];
  assert.equal(s.width, 1920); assert.equal(s.height, 1080); assert.equal(s.r_frame_rate, '24/1');
  const frames = name.startsWith('shelf-') ? 37 : name === 'idle' ? 240 : name.startsWith('monitor-') ? 121 : 73;
  assert.equal(Number(s.nb_frames), frames, name);
  const bytes = statSync(file).size; assert.ok(bytes < 6_000_000, `${name} exceeds 6 MB`);
  videos.push({name, frames, bytes, width:s.width, height:s.height, fps:24});
}
const pixels = new Map();
function pixelHash(name) {
  if (!pixels.has(name)) pixels.set(name, execFileSync('ffmpeg', ['-v','error','-i',path.join(raw,name+'.png'),'-map','0:v:0','-f','hash','-hash','sha256','-'], {encoding:'utf8'}).trim());
  return pixels.get(name);
}
const pairs = [
  ['photos-still/0000','photos-background/0000'],
  ['vinyl-in/0072','vinyl-still/0000'], ['vinyl-out/0000','vinyl-still/0000'],
  ['greeting-probe/0000','idle/0000'],
  ['vinyl-in/0000','idle/0000'], ['vinyl-out/0072','idle/0144'],
  ['monitor-in/0120','monitor-out/0000'], ['monitor-out/0120','idle/0000'],
  ['diploma-in/0000','idle/0000'], ['diploma-out/0072','idle/0144'],
  ['diploma-in/0072','diploma-out/0000'],
];
const plates=['books','vinyl','photos'];
for (const [a,b] of [[1,0],[0,1],[1,2],[2,1]]) {
  pairs.push([`shelf-${a}-${b}/0000`,`${plates[a]}-still/0000`]);
  pairs.push([`shelf-${a}-${b}/0036`,`${plates[b]}-still/0000`]);
}
const endpoints=pairs.map(([a,b]) => {
  const exact=pixelHash(a)===pixelHash(b);
  if (exact) return {a,b,exact,ssim:1};
  // Restoring a static camera through a matrix can introduce subpixel float
  // rounding. Measure decoded images rather than rejecting harmless 1-LSB noise.
  const compare=spawnSync('ffmpeg',['-hide_banner','-i',path.join(raw,a+'.png'),'-i',path.join(raw,b+'.png'),'-lavfi','ssim','-f','null','-'],{encoding:'utf8'});
  assert.equal(compare.status,0);
  const score=compare.stderr.match(/All:([\d.]+)/);
  assert.ok(score,`${a}: SSIM result missing`);
  return {a,b,exact,ssim:Number(score[1])};
});
const report={version:149,artwork,videos,endpoints};
writeFileSync(path.join(raw,'release-verification.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
assert.ok(endpoints.every(p=>p.ssim>=.99999), 'Inspect discontinuous endpoint pairs before release');
