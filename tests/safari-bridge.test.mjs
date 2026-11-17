import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HUB_CHANNEL, REPORT_URL, isHubPath, readHubState, hubOriginForPreview} from '../app/components/safariBridge.ts';
test('Safari only accepts known gallery routes and bounded state messages',()=>{
  for(const path of ['/','/about','/index']) assert.equal(isHubPath(path),true);
  for(const path of ['/featured','//evil.example','https://evil.example',null,{}]) assert.equal(isHubPath(path),false);
  const state={channel:HUB_CHANNEL,type:'state',path:'/',title:'Research Work',canBack:false,canForward:true};
  assert.equal(readHubState(state)?.path,'/');
  for(const bad of [{...state,channel:'other'},{...state,path:'/featured'},{...state,title:'a'.repeat(161)},{...state,canBack:'true'},null]) assert.equal(readHubState(bad),null);
  assert.equal(REPORT_URL,'https://gallery.brianbzeng.com/featured');
});
test('local preview cannot replace the deployed Hub on a public host',()=>{
  assert.equal(hubOriginForPreview('127.0.0.1','?hubPreview=local'),'http://127.0.0.1:4178');
  assert.equal(hubOriginForPreview('localhost','?hubPreview=local'),'http://127.0.0.1:4178');
  assert.equal(hubOriginForPreview('brianbzeng.com','?hubPreview=local'),'https://gallery.brianbzeng.com');
  assert.equal(hubOriginForPreview('127.0.0.1',''),'https://gallery.brianbzeng.com');
});
test('Safari validates sender and links its current page to an isolated browser tab',()=>{
  const src=readFileSync(new URL('../app/components/DesktopSafari.tsx',import.meta.url),'utf8');
  assert.match(src,/event.origin !== origin \|\| event.source !== frame.current\?\.contentWindow/);
  assert.match(src,/sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"/);
  assert.doesNotMatch(src,/allow-top-navigation|onReport|location.assign/);
  assert.match(readFileSync(new URL('../app/components/desktopSafari.css',import.meta.url),'utf8'),/\.safari-page-container iframe[^}]*filter:grayscale\(1\)/);
  assert.match(src,/href=\{HUB_ORIGIN \+ page.path\} target="_blank" rel="noopener noreferrer"/);
  assert.doesNotMatch(src,/safari-tabstrip|safari-current-tab|Show tab overview|New tab unavailable|setOverview/);
  assert.match(src,/if \(ready\) \{ send\('reload'\); return; \}/);
});

test('photo inspection removes visible captions but preserves accessible descriptions',()=>{
  const src=readFileSync(new URL('../app/components/BookshelfExperience.tsx',import.meta.url),'utf8');
  assert.doesNotMatch(src, /<p>\{photo===null\?'':PHOTO_LABELS\[photo\]\}<\/p>/);
  assert.match(src, /aria-label=\{`Enlarge photo/);
});
