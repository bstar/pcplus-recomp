'use strict';
// Execute actual CallSession methods; timers/clocks and DSP/Telnet are boundaries.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const {EventEmitter}=require('events');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
const config=require(path.join(runtime,'source/config.js'));config.logging.level='error';
const {CallSession}=require(path.join(runtime,'source/src/session/CallSession.js'));
const saved={timeout:global.setTimeout,interval:global.setInterval,clear:global.clearInterval,now:Date.now,hr:process.hrtime.bigint};
const cases=[];
function session(attach){
 const s=Object.create(CallSession.prototype);s._active=true;s._id='minimum-hold-test';s._connectInfo={protocol:'V22',bps:1200};
 s._dsp=new EventEmitter();s._dsp.write=()=>true;
 s._telnet=new EventEmitter();s._telnet.attach=attach;s._telnet.receive=()=>{};return s;
}
function run(name,actions,opts={}){
 let now=0,wall=0,timer,interval,attaches=0,clears=0,attachedAt;
 Object.assign(config.modem.native,{postTrainIdleMs:6000,postTrainQuiescenceMs:500,postTrainAttachMaxMs:10000},opts);
 try {
  global.setTimeout=(fn,delay)=>{assert.equal(delay,config.modem.native.postTrainIdleMs);timer=fn;return 1;};
  global.setInterval=(fn,delay)=>{assert.equal(delay,100);interval=fn;return 2;};
  global.clearInterval=id=>{assert.equal(id,2);clears++;};Date.now=()=>wall;
  process.hrtime.bigint=()=>BigInt(Math.round(now*1e6));
  const s=session(()=>{attaches++;attachedAt=now;});s._onModemConnected();assert.equal(attaches,0);
  const check={at:ms=>{now=ms;},wall:ms=>{wall=ms;},timer:()=>timer(),interval:()=>interval(),
   data:n=>s._dsp.emit('data',Buffer.alloc(n)),inactive:()=>{s._active=false;},
   detached:()=>assert.equal(attaches,0),attached:()=>assert.equal(attaches,1)};
  actions(check);
  if(attaches){assert(attachedAt>=config.modem.native.postTrainIdleMs);assert.equal(s._dsp.listenerCount('drain'),1);}
  cases.push({case:name,passed:true,attaches,attached_ms:attachedAt??null,interval_clears:clears});
 } finally {global.setTimeout=saved.timeout;global.setInterval=saved.interval;global.clearInterval=saved.clear;Date.now=saved.now;process.hrtime.bigint=saved.hr;}
}
run('early-timeout-recovers-on-interval',t=>{t.at(5999);t.timer();t.detached();t.at(6000);t.interval();t.attached();});
run('exact-timeout',t=>{t.at(6000);t.timer();t.attached();});
run('late-timeout',t=>{t.at(6500);t.timer();t.attached();});
run('interval-before-timeout-delivery',t=>{t.at(5999);t.interval();t.detached();t.at(6000);t.interval();t.attached();});
run('short-cap-preserves-minimum',t=>{t.at(1000);t.interval();t.detached();t.at(5999);t.data(1);t.interval();t.detached();t.at(6000);t.interval();t.attached();},{postTrainAttachMaxMs:1000});
run('data-postpones-until-quiescence',t=>{t.at(5900);t.data(4);t.at(6000);t.timer();t.detached();t.at(6399);t.interval();t.detached();t.at(6400);t.interval();t.attached();});
run('continuous-data-is-capped',t=>{t.at(5900);t.data(1);t.at(6000);t.timer();t.detached();t.at(9999);t.data(2);t.interval();t.detached();t.at(10000);t.interval();t.attached();});
run('hangup-before-timeout',t=>{t.inactive();t.at(6000);t.timer();t.interval();t.detached();});
run('duplicate-callbacks-attach-once',t=>{t.at(6000);t.timer();t.timer();t.interval();t.interval();t.attached();});
run('wall-forward-does-not-shorten-hold',t=>{t.at(5999);t.wall(1e12);t.timer();t.interval();t.detached();t.at(6000);t.interval();t.attached();});
run('wall-backward-does-not-extend-hold',t=>{t.wall(-1e12);t.at(6000);t.timer();t.attached();});
run('zero-hold-and-quiescence',t=>{t.timer();t.attached();},{postTrainIdleMs:0,postTrainQuiescenceMs:0});
run('zero-hold-still-needs-quiescence',t=>{t.timer();t.detached();t.at(499);t.interval();t.detached();t.at(500);t.interval();t.attached();},{postTrainIdleMs:0});
run('submillisecond-early-timeout',t=>{t.at(5999.999);t.timer();t.detached();t.at(6000);t.interval();t.attached();});
async function main(){
 // One default6000ms run uses the real Node monotonic clock and timer queue.
 Object.assign(config.modem.native,{postTrainIdleMs:6000,postTrainQuiescenceMs:500,postTrainAttachMaxMs:10000});
 const start=saved.hr();let s,deadline;
 const elapsed=await new Promise((resolve,reject)=>{
  deadline=saved.timeout(()=>reject(Error('Real timer attach deadline')),11000);
  s=session(()=>resolve(Number(saved.hr()-start)/1e6));s._onModemConnected();
 });
 clearTimeout(deadline);assert(elapsed>=6000 && elapsed<11000);s._active=false;
 // Allow the real interval to observe inactive state and retire naturally.
 await new Promise(resolve=>saved.timeout(resolve,120));
 cases.push({case:'real-Node-default6000ms-timers',passed:true,attached_ms:elapsed});
 const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 const source=path.join(runtime,'source/src/session/CallSession.js');
 const result={passed:true,cases,source_path:source,source_sha256:sha(source),checker_sha256:sha(__filename),
  scope:'Actual candidate CallSession method with14 modeled timer/clock/DSP/Telnet boundary cases and one real default6000ms Node timer run. Early callbacks, independent intervals, minimum-over-cap, quiescence/data cap, inactive/duplicate calls, wall jumps, zero/fractional boundaries. Original runtime untouched; no SIP/audio/BBS, physical or whole-application acceptance.'};
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:cases.length,real_timer_elapsed_ms:elapsed}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
