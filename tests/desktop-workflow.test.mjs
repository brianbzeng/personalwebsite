import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolveTerminalCommand } from '../app/components/terminalContent.ts';
import { publicPushes } from '../app/components/githubPushes.ts';
const read = name => readFileSync(new URL(`../app/components/${name}`, import.meta.url),'utf8');

test('exit returns a navigation action; contact has explicit safe redirect links',()=>{
  assert.equal(resolveTerminalCommand(' EXIT ').exit,true);
  assert.match(resolveTerminalCommand('help').lines.join('\n'),/exit.*return to the room/);
  assert.deepEqual(resolveTerminalCommand('python contact.txt').links.map(link=>link.href),[
    'mailto:bzeng0000@gmail.com','https://www.linkedin.com/in/brianbzeng','https://github.com/brianbzeng',
  ]);
  assert.match(read('DesktopTerminal.tsx'),/if \(result\?\.exit\) \{ onExit\(\)/);
  assert.match(read('CinematicRoom.tsx'),/event.origin !== window.location.origin \|\| event.source !== desktop.current\?\.contentWindow/);
  assert.match(read('MonitorDesktop.tsx'),/else window.location.assign\("\/"\)/);
});

test('push directory preserves repeated pushes, links commits, sorts dates and rejects unsafe data',()=>{
  const push = (id,date,payload={})=>({id,type:'PushEvent',public:true,created_at:date,repo:{name:'brianbzeng/test'},payload});
  const older=push('1','2026-09-01T01:00:00Z');
  const newer=push('2','2026-09-02T01:00:00Z',{ref:'refs/heads/main',head:'a'.repeat(40),commits:[{sha:'b'.repeat(40),message:'A real commit\nBody'}]});
  const result=publicPushes([older,newer,newer,{...newer,id:'3',public:false},{...newer,repo:{name:'evil.test/a?x'}}]);
  assert.deepEqual(result.map(x=>x.id),['2','1']);
  assert.equal(result[0].url,`https://github.com/brianbzeng/test/commit/${'a'.repeat(40)}`);
  assert.equal(result[0].commits[0].message,'A real commit');
  assert.equal(result[1].commits.length,0);
  const headOnly=publicPushes([push('4','2026-09-03T01:00:00Z',{head:'c'.repeat(40)})]);
  assert.equal(headOnly[0].commits[0].sha,'c'.repeat(40));
  assert.equal(publicPushes(null).length,0);
});

test('widget replaces only Notes card and the directory no longer displays an ASCII chart',()=>{
  assert.match(read('MonitorDesktop.tsx'),/<GitHubPulse variant="widget"/);
  assert.doesNotMatch(read('MonitorDesktop.tsx'),/<NotesWidget/);
  assert.match(read('MonitorDesktop.tsx'),/<DesktopNotes/);
  assert.doesNotMatch(read('TerminalPulse.tsx'),/formatPulseGraph|<pre/);
  assert.match(read('GitHubPulse.tsx'),/Promise.allSettled/);
  assert.match(read('GitHubPulse.tsx'),/if \(inFlight\) return inFlight/);
});

test('terminal pushes are oldest-first without changing the shared feed, widget has no terminal shortcut',()=>{
  const terminal=read('TerminalPulse.tsx');
  assert.match(terminal,/const pushes = \[\.\.\.activity.pushes\]\.reverse\(\)/);
  assert.match(terminal,/pushes.map\(\(push\)/);
  assert.match(terminal,/Public pushes · oldest first/);
  assert.doesNotMatch(read('GitHubPulse.tsx')+read('MonitorDesktop.tsx'),/onOpenActivity/);
  assert.doesNotMatch(read('GitHubPulse.tsx'),/>Recent pushes /);
  assert.match(read('GitHubPulse.tsx'),/aria-label="Open Brian’s GitHub profile"/);
});

test('brief launches share a delay and cursor state, preserve popup gestures, and clear timers',()=>{
  const source=read('MonitorDesktop.tsx');
  assert.match(source,/APP_LAUNCH_DELAY = 333/);
  assert.match(source,/launchTimers.current.has\(key\)/);
  assert.match(source,/setPendingApps\(launchTimers.current.size\)/);
  assert.match(source,/function closeWindow\(id: DesktopWindowId\) \{ cancelPendingLaunch\(id\)/);
  assert.match(source,/for \(const timer of launchTimers.current.values\(\)\) clearTimeout\(timer\)/);
  assert.match(source,/window.open\(SPOTIFY_PROFILE_URL/);
  assert.match(read('MacDock.tsx'),/<a key=\{id\}.*href=\{SPOTIFY_PROFILE_URL\}/);
  assert.match(read('githubWidget.css'),/pointer-events:none/);
  assert.match(read('githubWidget.css'),/prefers-reduced-motion:reduce/);
});

test('commands share a 200ms cancellable delay and an accessible gray line spinner',()=>{
  const source=read('DesktopTerminal.tsx');
  assert.match(source,/const COMMAND_LOADING_MS = 200/);
  assert.match(source,/useState<string \| null>\(initialCommand\?\.trim\(\) \? initialCommand : null\)/);
  assert.match(source,/finishCommand.current\?\.\(pendingCommand\)/);
  assert.match(source,/return \(\) => \{ if \(commandTimer.current !== null\) clearTimeout\(commandTimer.current\)/);
  assert.match(source,/const interrupted = pendingRef.current \?\? input/);
  assert.match(source,/readOnly=\{pendingCommand !== null\}/);
  assert.match(source,/role="status" aria-label="Running command"/);
  assert.match(source,/terminal-command-spinner" aria-hidden="true"/);
  assert.match(read('windowsDesktop.css'),/terminal-command-spin 200ms steps\(4, end\)/);
  assert.match(read('windowsDesktop.css'),/\.terminal-command-loading \{ color: #aaa/);
  assert.match(read('windowsDesktop.css'),/prefers-reduced-motion: reduce\) \{ \.terminal-command-spinner > span \{ animation: none/);
});
