import assert from 'node:assert/strict';
import test from 'node:test';
import {build} from 'esbuild';
const output = await build({entryPoints:['config/backend-origin.ts'],bundle:true,write:false,format:'esm',platform:'node'});
const {backendOrigin} = await import('data:text/javascript;base64,'+Buffer.from(output.outputFiles[0].text).toString('base64'));

test('development keeps local proxy and accepts an explicit override',()=>{
  assert.equal(backendOrigin({NODE_ENV:'development'}),'http://127.0.0.1:8000');
  assert.equal(backendOrigin({NODE_ENV:'development',BACKEND_ORIGIN:'http://localhost:8001/'}),'http://localhost:8001');
});
test('production fails closed for missing or unsafe destinations without disclosing them',()=>{
  for(const value of [undefined,'http://127.0.0.1:8000','https://localhost','/backend-api','https://user:synthetic@api.example.invalid','https://api.example.invalid/path','https://api.example.invalid?key=synthetic']){
    assert.throws(()=>backendOrigin({NODE_ENV:'production',BACKEND_ORIGIN:value,NEXT_PUBLIC_API_BASE_URL:'https://api.example.invalid'}),error=>!error.message.includes('synthetic')&&error.message.includes('configuration'));
  }
  assert.throws(()=>backendOrigin({NODE_ENV:'production',BACKEND_ORIGIN:'https://api.example.invalid'}));
});
test('production uses explicit HTTPS origins and preserves the proxy path',()=>{
  assert.equal(backendOrigin({NODE_ENV:'production',BACKEND_ORIGIN:'https://api.example.invalid/',NEXT_PUBLIC_API_BASE_URL:'https://api.example.invalid'}),'https://api.example.invalid');
});
