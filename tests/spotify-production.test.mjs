import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import ts from 'typescript';
import {SPOTIFY_CALLBACK,SPOTIFY_PRODUCTION_CALLBACK,spotifyCallbackAllowed,spotifyOAuthRequest,spotifyStateCookie,seal,unseal,digest,randomToken} from '../app/server/spotifySecurity.ts';

test('OAuth allows only the configured exact production callback or development loopback',()=>{
  for(const development of [true,false]){
    const callback=development?SPOTIFY_CALLBACK:SPOTIFY_PRODUCTION_CALLBACK;
    assert.equal(spotifyCallbackAllowed(callback,development),true);
    assert.equal(spotifyOAuthRequest(new Request(new URL('/api/spotify/connect',callback)),callback,development),true);
    for(const bad of [callback+'/',callback+'?x=1',callback+'#x',callback.replace('/callback','/connect'),undefined])assert.equal(spotifyCallbackAllowed(bad,development),false);
  }
  for(const origin of ['http://brianbzeng.com','https://brianbzeng.com:8443','https://www.brianbzeng.com','https://brianbzeng.com.evil.test','https://brian-zeng-portfolio.bzeng9099.workers.dev', 'http://127.0.0.1:3000'])assert.equal(spotifyOAuthRequest(new Request(origin),SPOTIFY_PRODUCTION_CALLBACK,false),false);
  assert.equal(spotifyCallbackAllowed(SPOTIFY_CALLBACK,false),false);
});

test('production OAuth cookies are secure even when clearing them',()=>{
  for(const value of ['nonce',''])assert.match(spotifyStateCookie(value,0,false),/HttpOnly; SameSite=Lax; Max-Age=0; Secure$/);
  assert.doesNotMatch(spotifyStateCookie('nonce',600,true),/Secure/);
});

function harness(profile={id:'attacker',account_id:'not-brian'},scope='user-read-playback-state user-read-recently-played'){
  const sql=new DatabaseSync(':memory:');sql.exec('CREATE TABLE spotify_state (key TEXT PRIMARY KEY, value TEXT NOT NULL, expires_at INTEGER NOT NULL DEFAULT 0)');
  const db={prepare(query){return {bind(...args){return {first:async()=>sql.prepare(query).get(...args)??null,run:async()=>({meta:sql.prepare(query).run(...args)})};},first:async()=>sql.prepare(query).get()??null,run:async()=>({meta:sql.prepare(query).run()})};},async batch(statements){return Promise.all(statements.map(s=>s.run()));}};
  const env={DB:db,SPOTIFY_CLIENT_ID:'test-id',SPOTIFY_CLIENT_SECRET:'test-secret',SPOTIFY_USER_ID:'12127274651',SPOTIFY_REDIRECT_URI:SPOTIFY_PRODUCTION_CALLBACK};
  let calls=0;
  const fetch=async url=>{calls++;if(url==='https://accounts.spotify.com/api/token')return Response.json({access_token:'test-access',refresh_token:'test-refresh',expires_in:3600,scope});if(url==='https://api.spotify.com/v1/me')return Response.json(profile);throw new Error('Unexpected upstream request');};
  const modules=new Map(),root=fileURLToPath(new URL('../',import.meta.url));
  function load(path){if(modules.has(path))return modules.get(path).exports;const module={exports:{}};modules.set(path,module);const source=readFileSync(path,'utf8');const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;new Function('require','module','exports','process','fetch',compiled)(id=>id==='cloudflare:workers'?{env}:load(resolve(dirname(path),id+'.ts')),module,module.exports,{env:{NODE_ENV:'production'}},fetch);return module.exports;}
  return {server:load(resolve(root,'app/server/spotify.ts')),sql,env,calls:()=>calls,
    put(key,value,expiry=0){sql.prepare('INSERT OR REPLACE INTO spotify_state VALUES(?,?,?)').run(key,value,expiry);},
    value(key){return sql.prepare('SELECT value FROM spotify_state WHERE key=?').get(key)?.value;}};
}
async function seed(h,{expiry=Date.now()+600000,state=randomToken()}={}){
  const tokens=await seal({access:'old-access',refresh:'old-refresh',expiresAt:Date.now()+600000,generation:'old-generation',accountId:'brian-stable'},'test-secret');
  h.put('tokens',tokens);h.put('feed','{"cached":"owner"}');
  h.put('oauth:'+await digest(state),await seal({verifier:'test-verifier'},'test-secret'),expiry);
  return {tokens,state,request:new Request(SPOTIFY_PRODUCTION_CALLBACK+'?code=test-code&state='+state,{headers:{Cookie:'spotify_connect_state='+state}})};
}
test('non-owner, scope failure and expired state preserve owner credentials and cache',async()=>{
  for(const kind of ['non-owner','scope','expired','mismatch','denied']){
    const h=harness(kind==='scope'?{id:'12127274651',account_id:'brian-stable'}:undefined,kind==='scope'?'user-read-recently-played':undefined);
    try{const s=await seed(h,kind==='expired'?{expiry:1}:{});
      const request=kind==='mismatch'?new Request(SPOTIFY_PRODUCTION_CALLBACK+'?state=wrong',{headers:{Cookie:'spotify_connect_state='+s.state}}):kind==='denied'?new Request(SPOTIFY_PRODUCTION_CALLBACK+'?state='+s.state+'&error=access_denied',{headers:{Cookie:'spotify_connect_state='+s.state}}):s.request;
      const response=await h.server.connectCallback(request);assert.ok(response.status>=400);assert.equal(h.value('tokens'),s.tokens);assert.equal(h.value('feed'),'{"cached":"owner"}');
    }finally{h.sql.close();}
  }
});
test('verified owner commits encrypted credentials, clears stale cache and rejects callback replay',async()=>{
  const h=harness({id:'12127274651',account_id:'brian-stable'});
  try{const s=await seed(h);const response=await h.server.connectCallback(s.request);assert.equal(response.status,303);assert.match(response.headers.get('set-cookie'),/Secure/);assert.equal(h.value('feed'),undefined);const token=h.value('tokens');assert.equal((await unseal(token,'test-secret')).refresh,'test-refresh');const calls=h.calls();assert.ok((await h.server.connectCallback(s.request)).status>=400);assert.equal(h.calls(),calls);assert.equal(h.value('tokens'),token);}finally{h.sql.close();}
});
test('production cannot disconnect, including with valid state and same-origin POST',async()=>{
  const h=harness();try{const s=await seed(h);const response=await h.server.connectPost(new Request('https://brianbzeng.com/api/spotify/connect',{method:'POST',headers:{Origin:'https://brianbzeng.com',Cookie:'spotify_connect_state='+s.state},body:new URLSearchParams({state:s.state,action:'disconnect'})}));assert.equal(response.status,404);assert.equal(h.value('tokens'),s.tokens);assert.equal(h.value('feed'),'{"cached":"owner"}');const page=await h.server.connectPage();assert.doesNotMatch(await page.text(),/<form|Disconnect and clear/);assert.match(page.headers.get('set-cookie'),/Secure/);}finally{h.sql.close();}
});
test('public setup attempts are bounded and do not touch owner connection',async()=>{
  const h=harness();try{const s=await seed(h);for(let i=1;i<64;i++)h.put('oauth:'+i,'test',Date.now()+600000);assert.equal((await h.server.connectPage()).status,429);assert.equal(h.value('tokens'),s.tokens);}finally{h.sql.close();}
});
