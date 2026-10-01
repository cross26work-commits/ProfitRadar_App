// Isolated rendering of actual client components. Never loaded by Next routes.
import {build} from 'esbuild';
import {createServer} from 'node:http';
import {readFile,readdir} from 'node:fs/promises';
import {resolve} from 'node:path';
const fixture=resolve('tests/ui/fixture.jsx');
const result=await build({entryPoints:['tests/ui/entry.jsx'],bundle:true,write:false,format:'iife',jsx:'automatic',define:{'process.env':'{"NODE_ENV":"development"}'},alias:Object.fromEntries(['@/lib/api','@/providers/AuthProvider','@/lib/supabase/client','@/services/account/accountService','next/navigation','next/link'].map(k=>[k,fixture]))});
const cssNames=(await readdir('.next/static/chunks')).filter(n=>n.endsWith('.css'));
if(!cssNames.length)throw new Error('Build production CSS first');
const css=(await Promise.all(cssNames.map(n=>readFile(resolve('.next/static/chunks',n),'utf8')))).join('\n');
const files={'/bundle.js':['text/javascript',result.outputFiles[0].text],'/style.css':['text/css',css],'/':['text/html','<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Profit Radar isolated UI fixture</title><link rel="stylesheet" href="/style.css"><div id="root"></div><script src="/bundle.js"></script></html>']};
createServer((req,res)=>{const asset=files[new URL(req.url,'http://127.0.0.1:3190').pathname];res.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; form-action 'none'; base-uri 'none'");res.setHeader('Cache-Control','no-store');res.statusCode=asset?200:404;if(asset)res.setHeader('Content-Type',`${asset[0]}; charset=utf-8`);res.end(asset?.[1]||'Not found');}).listen(3190,'127.0.0.1',()=>console.log('Isolated fixture http://127.0.0.1:3190 — no Auth/DB/external transport'));
