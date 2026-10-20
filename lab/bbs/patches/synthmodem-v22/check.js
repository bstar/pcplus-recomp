'use strict';
// Signal/timing regressions for the originating V.22 candidate.
const assert=require('assert/strict'),path=require('path');
const baseline=path.resolve(process.argv[2]),candidate=path.resolve(process.argv[3]);
const {V22:Stock}=require(path.join(baseline,'src/dsp/protocols/V22.js'));
const {V22}=require(path.join(candidate,'src/dsp/protocols/V22.js'));
let checks=0;const ok=(v,label)=>{assert(v,label);checks++;};
const tone=(hz,n,amp=.1,offset=0)=>Float32Array.from({length:n},(_,i)=>amp*Math.cos(2*Math.PI*hz*(i+offset)/8000));
const energy=b=>b.reduce((sum,v)=>sum+v*v,0);
function receive(mod,hz,n,guard=false){
 for(let at=0;at<n;at+=160){const take=Math.min(160,n-at),b=tone(hz,take,.05,at);
  if(guard){const g=tone(1800,take,.025,at);for(let i=0;i<take;i++)b[i]+=g[i];}
  mod.receiveAudio(b);
 }
}
function prepared(guard=false){const m=new V22('originate');m.generateAudio(160);receive(m,2250,1280,guard);return m;}
const stock=new Stock('originate');
ok(energy(stock.generateAudio(8000))>1,'Stock incorrectly transmits immediately');
for(const hz of [0,1800,2100,2400]){
 const m=new V22('originate');let connected=false;m.on('ready',v=>{connected ||= v.remoteDetected;});
 m.generateAudio(160);receive(m,hz,16000);
 ok(energy(m.generateAudio(16000))===0,`Remain silent for non-USB signal ${hz}`);
 ok(!connected,`No false connection for signal ${hz}`);
}
for(const guard of [false,true]){
 const m=prepared(guard),b=m.generateAudio(3648+800);
 ok(energy(b.subarray(0,3648))===0,'Exact 456ms response delay');
 ok(energy(b.subarray(3648))>0,'Respond to USB1, including guard-tone case');
}
{
 const m=new V22('originate');m.generateAudio(160);receive(m,2250,1120);
 ok(energy(m.generateAudio(8000))===0,'Short 140ms USB burst cannot start response');
}
{
 const one=prepared().generateAudio(10000),m=prepared(),split=new Float32Array(10000);
 let at=0;while(at<split.length){const n=Math.min(split.length-at,[1,17,160,511][at%4]);split.set(m.generateAudio(n),at);at+=n;}
 ok(one.every((v,i)=>v===split[i]),'Chunk-independent response waveform and delay');
}
{
 const m=prepared();m.generateAudio(3648);const b=m.generateAudio(32000);
 const mag=Math.hypot(...[0,1].map(kind=>b.reduce((sum,v,i)=>sum+v*(kind?Math.sin:Math.cos)(2*Math.PI*1800*i/8000),0)))/b.length;
 ok(mag<.001,'No 1800Hz guard emitted in low caller channel');
}
{
 const m=prepared();let connected=false;m.on('ready',v=>{connected ||= v.remoteDetected;});
 m.generateAudio(4000);receive(m,2250,32000);m.generateAudio(8000);
 ok(!connected,'USB1 alone cannot complete training without scrambled response');
}
{
 const stock=new Stock('answer'),m=new V22('answer');
 for(let i=0;i<100;i++){
  const b=stock.generateAudio(160),c=m.generateAudio(160);
  ok(b.every((v,j)=>v===c[j]),'Answer-side training waveform unchanged');
 }
}
console.log(JSON.stringify({passed:true,checks,baseline_immediate_TX_reproduced:true,
 scope:'Actual V22 signal generation/receiver with independent tones and output sample comparisons. Positive duplex training requires the separate VM test.'}));
