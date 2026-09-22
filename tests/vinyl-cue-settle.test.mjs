import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import * as T from 'three';
import ts from 'typescript';

const source = readFileSync(new URL('../app/components/ShelfScene.tsx', import.meta.url), 'utf8');
const ast = ts.createSourceFile('ShelfScene.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
function findNodes(predicate, root = ast) {
  const found = [];
  function visit(node) { if (predicate(node)) found.push(node); ts.forEachChild(node, visit); }
  visit(root);
  return found;
}
const declaration = name => findNodes(node => ts.isFunctionDeclaration(node) && node.name?.text === name)[0];
const transpile = code => ts.transpileModule(code, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;

// Run the real publisher and selection transition with actual world transforms.
// Frames beyond the cue's 600ms delay must still wait for extraction to finish.
function fixture() {
  const scene = new T.Scene(), camera = new T.OrthographicCamera(-5, 5, 3, -3, .1, 100);
  camera.position.z = 10;
  const group = new T.Group();
  const cover = new T.Mesh(new T.BoxGeometry(1, 1, .1));
  const disc = new T.Mesh(new T.BoxGeometry(.8, .8, .05));
  disc.userData.disc = true; disc.position.x = .7;
  group.add(cover, disc); scene.add(group); group.position.set(-3, -1, 0);
  const publications = [], selections = [];
  const latest = { current: {
    onCueTargets: targets => publications.push(structuredClone(targets)),
    onSelect: value => selections.push({ value, targets: publications.at(-1) }),
    onBook() {}, onSpread() {}, onTurning() {},
  } };
  const create = new Function('T', 'scene', 'camera', 'group', 'latest', `
    const props={cubby:1}, canvas={getBoundingClientRect:()=>({left:0,top:0,width:1000,height:600})};
    const items=[{id:0,group}], gallery=null, eligible=()=>true, turnHinge={visible:false};
    let playback=null,selected=null,opening=0,locked=false,hover=null,turn=0,tilt=0,open=false,corner=null,pageTurn=null,spread=0,needsPaint=false;
    let lastCueTime=-Infinity,lastCueKey='',lastCueListener;
    ${transpile(declaration('publishCueTargets').getText(ast))}
    ${transpile(declaration('select').getText(ast))}
    return {publish:publishCueTargets,select,setPlayback:value=>playback=value};
  `);
  const controls = create(T, scene, camera, group, latest);
  return { ...controls, group, publications, selections,
    get targets() { return publications.at(-1); },
    dispose() { cover.geometry.dispose(); disc.geometry.dispose(); cover.material.dispose(); disc.material.dispose(); },
  };
}

test('selection immediately clears shelf bounds before reporting the selected record', () => {
  const f = fixture();
  try {
    f.publish(0, true);
    assert.ok(f.targets.records);
    f.select(0);
    assert.deepEqual(f.targets, {});
    assert.deepEqual(f.selections.at(-1), { value: 0, targets: {} });
  } finally { f.dispose(); }
});

test('intermediate extraction frames never publish cover or disc, even after the fade delay', () => {
  const f = fixture();
  try {
    f.publish(0, true); f.select(0);
    for (const time of [100, 300, 600, 900, 1200]) {
      f.group.position.x += .5;
      f.publish(time, false);
      assert.deepEqual(f.targets, {}, `unsettled frame ${time} must not seed frozen cue geometry`);
    }
    f.group.position.set(1, 0, 0);
    f.publish(1400, true);
    assert.deepEqual(f.targets.cover, { x: 550, y: 250, width: 100, height: 100 });
    assert.deepEqual(f.targets.disc, { x: 650, y: 260, width: 60, height: 80 });
    const count = f.publications.length;
    f.publish(1600, true);
    assert.equal(f.publications.length, count, 'identical settled geometry does not churn React state');
  } finally { f.dispose(); }
});

test('shelf discovery remains available and playback clears inspection projections', () => {
  const f = fixture();
  try {
    f.publish(0, false);
    assert.ok(f.targets.records, 'unselected shelf targets do not require extraction readiness');
    f.select(0); f.publish(200, true);
    assert.ok(f.targets.cover);
    f.setPlayback({}); f.publish(400, false);
    assert.deepEqual(f.targets, {});
    f.setPlayback(null); f.select(null); f.publish(600, true);
    assert.ok(f.targets.records);
    assert.equal(f.targets.cover, undefined);
    assert.equal(f.targets.disc, undefined);
  } finally { f.dispose(); }
});

test('render supplies readiness only after extraction, opening, curl, locks and gallery motion settle', () => {
  const render = declaration('render');
  const calls = findNodes(node => ts.isCallExpression(node) && node.expression.getText(ast) === 'publishCueTargets', render);
  const settled = calls.at(-1)?.arguments[1];
  assert.ok(settled, 'normal render must explicitly supply projection readiness');
  const moving = findNodes(node => ts.isVariableDeclaration(node) && node.name.getText(ast) === 'moving', render)[0];
  const evaluate = new Function('distance', 'opening', 'open', 'curlMoving', 'locked', 'galleryMoving',
    `const moving=${moving.initializer.getText(ast)};return ${settled.getText(ast)};`);
  assert.equal(evaluate(0, 0, false, false, false, false), true);
  for (const args of [
    [.02, 0, false, false, false, false],
    [0, .5, true, false, false, false],
    [0, 0, false, true, false, false],
    [0, 0, false, false, true, false],
    [0, 0, false, false, false, true],
  ]) assert.equal(evaluate(...args), false, `must wait while ${JSON.stringify(args)}`);
});
