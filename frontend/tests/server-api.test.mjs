// Node unit tests with synthetic Auth/fetch; no browser, DB or network.
import {test,after} from 'node:test';
import assert from 'node:assert/strict';
import {build} from 'esbuild';
const previousFetch=globalThis.fetch;
const previousEnv={...process.env};
after(()=>{globalThis.fetch=previousFetch;process.env=previousEnv;delete globalThis.__serverFixture;});
const stubs={
 'server-only':'export {};',
 'next/navigation':'export function redirect(){throw new Error("FIXTURE_REDIRECT_LOGIN")};export function notFound(){throw new Error("FIXTURE_NOT_FOUND")};',
 '@/lib/supabase/server':'export async function createSupabaseServerClient(){return globalThis.__serverFixture};',
 '@supabase/ssr':'export function createServerClient(){return globalThis.__serverFixture};',
 'next/headers':'export async function cookies(){return {getAll:()=>[],set:()=>{}}};',
};
for(const [entry,exportName] of [['src/lib/api.server.ts','apiGetServer'],['src/lib/server-api.ts','serverApiGet']]){
 const output=await build({entryPoints:[entry],bundle:true,write:false,platform:'node',format:'esm',plugins:[{name:'synthetic-auth',setup(b){b.onResolve({filter:/.*/},args=>args.path in stubs?{path:args.path,namespace:'fixture'}:undefined);b.onLoad({filter:/.*/,namespace:'fixture'},args=>({contents:stubs[args.path]}));}}]});
 const loadedApi=await import('data:text/javascript;base64,'+Buffer.from(output.outputFiles[0].text).toString('base64'));
 const get=loadedApi[exportName];
 test(entry+' uses current JWT, rejects unauthenticated and redacts errors',async()=>{
   process.env.NEXT_PUBLIC_SUPABASE_URL='http://fixture.invalid';process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY='synthetic';
   const setSession=(session,error=null)=>{globalThis.__serverFixture={auth:{getSession:async()=>({data:{session},error})}};};
   let calls=0;
   setSession(null);globalThis.fetch=async()=>{calls++;throw new Error('Must not call')};
   await assert.rejects(()=>get('/leads/fixture'),/FIXTURE_REDIRECT_LOGIN/);assert.equal(calls,0);
   setSession({access_token:'synthetic-current-session'});
   globalThis.fetch=async(url,options)=>{calls++;assert.equal(options.headers.Authorization,'Bearer synthetic-current-session');assert.equal(options.cache,'no-store');return {ok:true,json:async()=>({id:'fixture'})};};
   assert.deepEqual(await get('/leads/fixture'),{id:'fixture'});
   for(const [status,expected] of [[401,/FIXTURE_REDIRECT_LOGIN/],[403,/FIXTURE_NOT_FOUND/],[404,/FIXTURE_NOT_FOUND/],[500,/Data temporarily unavailable/]]){
     globalThis.fetch=async()=>({status,ok:false,text:()=>assert.fail('Raw error body must not be read')});
     await assert.rejects(()=>get('/leads/fixture'),expected);
   }
   globalThis.fetch=async()=>({ok:true,json:async()=>{throw new Error('synthetic-private-response')}});
   await assert.rejects(()=>get('/leads/fixture'),/Invalid data response/);
   globalThis.fetch=async()=>{throw new Error('synthetic-private-transport')};
   await assert.rejects(()=>get('/leads/fixture'),/Data temporarily unavailable/);
 });
}
