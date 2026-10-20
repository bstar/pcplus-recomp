'use strict';
// Real pool lifecycle in a separate Node process; backend startup is modeled.
const assert=require('assert/strict'),{EventEmitter}=require('events'),path=require('path');
const root=path.resolve(process.argv[2]),scenario=process.argv[3];
require(path.join(root,'config.js')).logging.level='error';
const {ModemBackendPool}=require(path.join(root,'src/backends/ModemBackendPool.js'));
const backends=[];
class Backend extends EventEmitter {
 constructor(){super();this.stops=0;backends.push(this);}
 async startAsync(){
  if(scenario==='timeout')return new Promise(()=>{});
  await new Promise(r=>setTimeout(r,10));
  if(scenario==='reject')throw Error('startup rejected');
 }
 async stop(){this.stops++;}
}
async function main(){
 const p=new ModemBackendPool({backendFactory:()=>new Backend(),warmupTimeoutMs:1500});
 if(scenario==='reject'||scenario==='timeout'){
  await assert.rejects(()=>p.start(),scenario==='reject'?/startup rejected/:/warmup timed out/);
  assert.equal(p.state,'empty');assert.equal(backends[0].stops,1);
 }else{
  await p.start();assert.equal(p.state,'ready');
  if(scenario==='recycle'){
   const b=await p.checkout();p.recycle(b);
   // Await the actual tracked replacement lifecycle, without inventing readiness.
   await p._recyclePromise;assert.equal(p.state,'ready');
   assert.equal(backends.length,2);assert.equal(backends[0].stops,1);
  }
 }
 await p.stop();assert.equal(p.state,'stopped');
 assert.equal(backends.at(-1).stops,1);
 console.log(JSON.stringify({passed:true,scenario,backends:backends.length}));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
