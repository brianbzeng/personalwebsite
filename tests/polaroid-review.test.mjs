import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
const read=p=>JSON.parse(readFileSync(new URL(p,import.meta.url),'utf8'));
test('four ordered grayscale photos are packed into unchanged Polaroid frames',{skip:!existsSync(new URL('../blender/outputs/review-v147/polaroid-audit.json',import.meta.url))},()=>{
  const audit=read('../blender/outputs/review-v147/polaroid-audit.json');
  assert.ok(audit.existingTransformsUnchanged&&audit.existingFramesPreserved);
  assert.deepEqual(audit.orderedPhotos.map(p=>p.object),['D','C','B','A'].map(c=>`SHELF_Polaroid_${c}_Photo`));
  const model=read('../public/review/v138/photos.json');
  for(const item of audit.orderedPhotos){
    assert.ok(item.packed&&item.grayscale);
    const mesh=model.meshes.find(m=>m.name===item.object);assert.ok(mesh);
    const mat=mesh.materials.find(m=>m.texture===item.path);assert.ok(mat&&mat.grayscale&&mat.unlit);
    assert.ok(existsSync(new URL(`../public${item.path}`,import.meta.url)));
    assert.ok(mesh.uvs.every(v=>v>=0&&v<=1));
  }
});
