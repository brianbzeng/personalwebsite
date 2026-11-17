import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const desktop = readFileSync(new URL('../app/components/MonitorDesktop.tsx', import.meta.url), 'utf8');

test('championship widget is benched behind a reversible disabled flag', () => {
  assert.match(desktop, /const F1_CHAMPIONSHIP_WIDGET_ENABLED = false;/);
  assert.match(desktop, /\{F1_CHAMPIONSHIP_WIDGET_ENABLED && <section className="f1-driver-widget"/);
  assert.match(desktop, /driverLeader\.name/);
  assert.match(desktop, /driverLeader\.points/);
  assert.match(desktop, /import driverLeader from "\.\.\/data\/f1-driver-leader\.json"/);
});

test('benching the standings card preserves the F1 app and other widgets', () => {
  assert.match(desktop, /<SpotifyWidget \/><GitHubPulse variant="widget" \/>/);
  assert.match(desktop, /if \(app === "f1"\).*type: "open-f1"/);
  assert.match(desktop, /\{f1Window && <DesktopF1/);
});
