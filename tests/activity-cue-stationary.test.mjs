import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

const component = readFileSync(new URL('../app/components/ActivityCues.tsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../app/components/activityCues.css', import.meta.url), 'utf8');
const compiled = ts.transpileModule(component, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
}).outputText;

// Execute the component's actual effects with deterministic frames and DOM events.
// Hook state persists across rerenders, so changing bounds/props exercises the
// same lifecycle as dragging a target while its note is on screen.
async function mount(overrides = {}) {
  let cursor = 0, dirty = false, now = 0, sequence = 0, tree, completions = 0, measurements = 0;
  let target = { x: 400, y: 300, width: 200, height: 200 };
  let props = { cues: [{ id: 'record', label: 'Drag', selector: '#record', gesture: 'drag' }],
    sceneKey: 'vinyl', ready: true, visibleMs: 2000, fadeIn: true,
    onComplete: () => completions++, ...overrides };
  const slots = [], pending = [], frames = new Map(), listeners = new Map();
  const node = { style: {}, dataset: {}, setAttribute(name, value) { this[name] = value; } };
  const react = {
    useRef(value) { const index = cursor++; return slots[index] ??= { current: value }; },
    useState(initial) {
      const index = cursor++;
      if (!(index in slots)) slots[index] = typeof initial === 'function' ? initial() : initial;
      return [slots[index], value => {
        const next = typeof value === 'function' ? value(slots[index]) : value;
        if (!Object.is(next, slots[index])) { slots[index] = next; dirty = true; }
      }];
    },
    useEffect(effect, deps) {
      const index = cursor++, previous = slots[index];
      if (!previous || deps.some((value, i) => !Object.is(value, previous.deps[i]))) {
        slots[index] = { deps, cleanup: previous?.cleanup };
        pending.push(() => { slots[index].cleanup?.(); slots[index].cleanup = effect(); });
      }
    },
  };
  const eventTarget = {
    addEventListener(type, fn, options) {
      const entries = listeners.get(type) ?? [];
      entries.push({ fn, options }); listeners.set(type, entries);
    },
    removeEventListener(type, fn) { listeners.set(type, (listeners.get(type) ?? []).filter(entry => entry.fn !== fn)); },
  };
  const jsx = (type, properties) => ({ type, props: properties });
  class KeyboardEvent { constructor(type, properties) { this.type = type; Object.assign(this, properties); } }
  const exports = {};
  vm.runInNewContext(compiled, {
    exports,
    KeyboardEvent,
    require: name => name === 'react' ? react : name === 'react/jsx-runtime' ? { jsx, jsxs: jsx } : {},
    window: { ...eventTarget, innerWidth: 1200, innerHeight: 900,
      matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }) },
    document: { ...eventTarget, hidden: false,
      fonts: { load: async () => [], ready: Promise.resolve() },
      createElement: () => ({ getContext: () => ({ measureText: () => ({ width: 25 }) }) }),
      querySelector: selector => selector === 'dialog[open]' ? null : {
        getBoundingClientRect() { measurements++; return { ...target }; },
      },
    },
    performance: { now: () => now },
    requestAnimationFrame: fn => { frames.set(++sequence, fn); return sequence; },
    cancelAnimationFrame: id => frames.delete(id),
  });
  function flush() {
    let count = 0;
    do {
      assert.ok(count++ < 20, 'effects should settle');
      dirty = false; cursor = 0; tree = exports.default(props);
      if (tree.props.ref) tree.props.ref.current = node;
      Object.assign(node.style, tree.props.style);
      for (const effect of pending.splice(0)) effect();
    } while (dirty);
  }
  flush();
  for (let i = 0; i < 8; i++) await Promise.resolve();
  flush();
  return {
    get tree() { return tree; }, get node() { return node; },
    get completions() { return completions; }, get measurements() { return measurements; },
    get frames() { return frames.size; },
    frame(time) { now = time; const batch = [...frames.values()]; frames.clear(); for (const fn of batch) fn(now); flush(); },
    update(next) { props = { ...props, ...next }; flush(); },
    move(next) { target = { ...target, ...next }; },
    event(type, details = {}) {
      const event = type === 'keydown' ? new KeyboardEvent(type, { key: 'ArrowLeft', ...details }) : { type, ...details };
      for (const { fn } of [...listeners.get(type) ?? []]) fn(event);
      const immediateOpacity = node.style.opacity;
      flush();
      return immediateOpacity;
    },
    listeners(type) { return listeners.get(type) ?? []; },
    cleanup() { for (const slot of slots) slot?.cleanup?.(); },
  };
}

test('every cue has stationary lettering and arrows in both presentation modes', () => {
  assert.doesNotMatch(css, /@keyframes|animation(?:-name|-duration|-delay)?:(?!\s*none\b)|transition[^;]*transform/);
  assert.doesNotMatch(component, /--cue-bounce-|style=\{bounce\}/);
});

test('moving a settled target never remeasures or changes its complete SVG geometry', async () => {
  const cue = await mount();
  try {
    cue.frame(100); cue.frame(1100);
    assert.equal(cue.tree.props.style.opacity, 1);
    const geometry = JSON.stringify(cue.tree.props.children), measured = cue.measurements;
    assert.ok(measured > 0);
    cue.move({ x: 600, y: 210, width: 260 });
    cue.update({ cues: [{ id: 'record', label: 'Changed', selector: '#record', gesture: 'drag' }] });
    cue.frame(1300); cue.frame(1500);
    assert.equal(cue.measurements, measured);
    assert.equal(JSON.stringify(cue.tree.props.children), geometry);
  } finally { cue.cleanup(); }
});

for (const event of ['pointerdown', 'touchstart', 'wheel', 'keydown', 'resize']) {
  test(`${event} dismisses visible cues immediately, completes once, and stops scheduled work`, async () => {
    const cue = await mount();
    try {
      cue.frame(100); cue.frame(1100);
      assert.equal(cue.tree.props.style.opacity, 1);
      const registered = cue.listeners(event);
      assert.ok(registered.length > 0);
      if (event !== 'resize') assert.ok(registered.some(({ options }) => options === true || options?.capture));
      assert.equal(cue.event(event), '0', 'DOM hides before React commits its next render');
      assert.equal(cue.tree.props.style.opacity, 0);
      assert.equal(cue.completions, 1);
      cue.event(event); cue.frame(1200); cue.frame(6000);
      assert.equal(cue.completions, 1);
      assert.equal(cue.frames, 0);
      assert.equal(cue.tree.props.style.opacity, 0);
    } finally { cue.cleanup(); }
  });
}

test('input during the initial settle prevents later appearance, while a new scene can show guidance', async () => {
  const cue = await mount();
  try {
    cue.frame(100); cue.event('pointerdown'); cue.frame(1100);
    assert.equal(cue.tree.props.style.opacity, 0);
    assert.equal(cue.completions, 1);
    cue.update({ sceneKey: 'new-vinyl' });
    cue.frame(1200); cue.frame(2200);
    assert.equal(cue.tree.props.style.opacity, 1);
    cue.frame(4000);
    assert.equal(cue.completions, 2);
    assert.equal(cue.tree.props.style.opacity, 0);
  } finally { cue.cleanup(); }
});

test('removing a cue from input removes its frozen SVG immediately', async () => {
  const cue = await mount();
  try {
    cue.frame(100); cue.frame(1100);
    assert.match(JSON.stringify(cue.tree.props.children), /"data-cue":"record"/);
    cue.update({ cues: [] });
    assert.doesNotMatch(JSON.stringify(cue.tree.props.children), /"data-cue":"record"/);
  } finally { cue.cleanup(); }
});
