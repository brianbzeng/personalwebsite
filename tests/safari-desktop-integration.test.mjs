import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { INITIAL_DESKTOP_SESSION, safariDesktopSession, desktopWindowReducer as reduce, managedWindowTitle } from '../app/components/desktopWindowManager.ts';

const source = path => readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
test('Safari monitor and New launch stacks are atomic and leave legacy session unchanged', () => {
  const legacy = structuredClone(INITIAL_DESKTOP_SESSION);
  for (const hub of [false, true]) {
    const session = safariDesktopSession(hub);
    assert.deepEqual(session.windows.map(w => w.id), hub ? ['notes', 'terminal-1', 'hub'] : ['terminal-1']);
    assert.equal(session.active, hub ? 'hub' : 'terminal-1');
    assert.deepEqual(session.windows.map(w => w.z), hub ? [10, 11, 12] : [10]);
    assert.deepEqual(reduce(legacy, { type: 'initialize-safari', hub }), session);
  }
  assert.deepEqual(INITIAL_DESKTOP_SESSION, legacy);
});
test('Hub lifecycle restores Terminal then Notes without duplicate Hub windows', () => {
  let session = safariDesktopSession(true);
  assert.equal(managedWindowTitle(session.windows[2]), 'Safari');
  session = reduce(session, { type: 'minimize', id: 'hub' });
  assert.equal(session.active, 'terminal-1');
  session = reduce(session, { type: 'open-hub' });
  assert.equal(session.active, 'hub');
  assert.equal(session.windows.filter(w => w.id === 'hub').length, 1);
  session = reduce(session, { type: 'close', id: 'hub' });
  assert.equal(session.active, 'terminal-1');
  session = reduce(session, { type: 'close', id: 'terminal-1' });
  assert.equal(session.active, 'notes');
});
test('Safari is opt-in in staging, with independent monitor and New launch routes', () => {
  const room = source('app/components/CinematicRoom.tsx');
  assert.match(room, /safariHub = false/);
  assert.match(room, /function enterMonitor\(\) \{\s*openMonitor\(false\)/);
  assert.match(room, /onClick=\{\(\) => openMonitor\(safariHub\)\}/);
  assert.match(room, /params.set\("app", "hub"\)/);
  assert.match(room, /params.set\("hubPreview", "local"\)/);
  assert.match(source('app/review/safari-room/page.tsx'), /CinematicRoom safariHub/);
  assert.match(source('app/review/safari-desktop/page.tsx'), /MonitorDesktop safariHub/);
  assert.match(source('app/page.tsx'), /CinematicRoom safariHub/);
  assert.match(source('app/desktop/page.tsx'), /MonitorDesktop safariHub/);
  assert.match(room, /`\/desktop\$\{desktopLaunch\}`/);
});
test('Safari leaves external tab opening to the direct Hub gesture without redirect relays', () => {
  const room = source('app/components/CinematicRoom.tsx'), desktop = source('app/components/MonitorDesktop.tsx');
  assert.match(room, /event.origin !== window.location.origin \|\| event.source !== desktop.current\?\.contentWindow/);
  assert.doesNotMatch(room + desktop, /bz-hub-report|openHubReport/);
  assert.match(desktop, /aria-label="Open Safari"/);
  assert.doesNotMatch(desktop, /if \(!safariHub\) dispatch\(\{ type: "open-notes" \}\)/);
  assert.match(desktop, /id.startsWith\("local-"\)/);
  assert.match(desktop, /safariHub \|\| app.id !== "hub"/);
});
