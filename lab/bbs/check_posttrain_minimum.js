'use strict';
// Real CallSession method with modeled timer/clock boundaries, no DSP/VM start.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const {EventEmitter}=require('events');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
const config=require(path.join(runtime,'source/config.js'));config.logging.level='error';
Object.assign(config.modem.native,{postTrainIdleMs:6000,postTrainQuiescenceMs:500,postTrainAttachMaxMs:10000});
const {CallSession}=require(path.join(runtime,'source/src/session/CallSession.js'));
const saved={timeout:global.setTimeout,interval:global.setInterval,clear:global.clearInterval,now:Date.now};
const cases=[];
try {
 for(const elapsed of [5999,6000]) {
  let now=0,timer,interval,attaches=0;
  global.setTimeout=(fn,delay)=>{assert.equal(delay,6000);timer=fn;return 1;};
  global.setInterval=(fn,delay)=>{assert.equal(delay,100);interval=fn;return 2;};
  global.clearInterval=()=>{};Date.now=()=>now;
  const session=Object.create(CallSession.prototype);
  session._active=true;session._id='minimum-hold-test';session._connectInfo={protocol:'V22',bps:1200};
  session._dsp=new EventEmitter();session._dsp.write=()=>true;
  session._telnet=new EventEmitter();session._telnet.attach=()=>{attaches++;};session._telnet.receive=()=>{};
  session._onModemConnected();assert.equal(attaches,0);assert.equal(session._dsp.listenerCount('data'),1);
  now=elapsed;timer();
  // Record the baseline defect explicitly: an early timer must not attach,
  // but this retained runtime trusts callback delivery as minimum elapsed.
  assert.equal(attaches,1);interval();assert.equal(attaches,1);
  cases.push({elapsed_ms:elapsed,attached:attaches===1,minimum_satisfied:elapsed>=6000,
   counterexample_reproduced:elapsed<6000});
 }
} finally {global.setTimeout=saved.timeout;global.setInterval=saved.interval;global.clearInterval=saved.clear;Date.now=saved.now;}
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const source=path.join(runtime,'source/src/session/CallSession.js');
const result={passed:false,counterexample_reproduced:true,cases,source_path:source,source_sha256:sha(source),checker_sha256:sha(__filename),
 scope:'Actual retained CallSession._onModemConnected with modeled timer/Date boundaries and EventEmitter DSP/Telnet boundaries. Early5999ms timer attaches despite configured6000ms minimum;6000ms control attaches once. No actual clock precision, waveform, caller compatibility, new runtime or physical acceptance is established.'};
fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({passed:false,counterexample_reproduced:true,cases}));
