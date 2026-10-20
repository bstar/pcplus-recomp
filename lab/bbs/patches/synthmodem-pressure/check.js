'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
const assert = require('assert/strict'), fs = require('fs'), path = require('path');
const net = require('net'), Module = require('module'), crypto = require('crypto');
const { EventEmitter } = require('events');
const root = path.resolve(process.argv[2]);
let assertions = 0;
const eq = (a,b) => { assert.deepEqual(a,b); assertions++; };
const ok = a => { assert(a); assertions++; };
const tick = () => new Promise(r => setImmediate(r));
const telnetEncode = b => Buffer.from(b.toString('latin1').replace(/\xff/g,'\xff\xff'),'latin1');
async function until(test, ms=3000) {
  const end=Date.now()+ms;
  while (!test()) { assert(Date.now()<end,'Observation deadline'); await new Promise(r=>setTimeout(r,2)); }
}
function load(variant, name, network=net) {
  const file=path.join(root,variant,name), real=Module.createRequire(file);
  const cfg=real(path.join(root,variant,'config.js'));
  cfg.logging.level='error';
  Object.assign(cfg.modem.native,{postTrainIdleMs:0,postTrainQuiescenceMs:0,postTrainAttachMaxMs:100});
  Object.assign(cfg.telnet,{terminalType:'ANSI',terminalCols:80,terminalRows:25,allowedHosts:['127.0.0.1'],blockedHosts:[],
    connectTimeoutMs:2000,idleTimeoutMs:0,menuIdleHeartbeatMs:0,proxyEscapeByte:null,negotiateOptions:false});
  cfg.terminal.banner=''; cfg.terminal.prompt=''; cfg.terminal.localEcho=false;
  const resources=new Set(['../tunnel/UdpTcpTunnel','../sip/SipUacInternal','../sip/VmRegistrar',
    '../rtp/RtpBridge','../rtp/RtpSession','../dsp/AudioCapture']);
  const m=new Module(file);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));
  m.require=n=> {
    if(n==='net') return network;
    if(resources.has(n)) return new Proxy({}, {get:()=>function(){throw Error('Unrequested VM/SIP/RTP resource');}});
    return real(n);
  };
  m._compile(fs.readFileSync(file,'utf8'),file);
  return m.exports;
}
class Socket extends EventEmitter {
  constructor(){super();this.frames=[];this.ready=true;this.destroyed=false;this.writableLength=0;this.paused=false;}
  write(b){ok(!this.destroyed);if(this.throwOnWrite)throw Error('Modeled socket failure');this.frames.push(Buffer.from(b));this.writableLength=this.ready?0:this.writableLength+b.length;return this.ready;}
  drain(ready=true){this.ready=ready;this.writableLength=0;this.emit('drain');}
  pause(){this.paused=true;}
  resume(){this.paused=false;}
  destroy(){this.destroyed=true;this.emit('close');}
}
function decode(frames){
  const out=[];
  for(const f of frames){eq(f[2],0x14);eq(f.readUInt16LE(0)+2,f.length);ok(f.length<=4096);out.push(f.subarray(3));}
  return Buffer.concat(out);
}
function backend(variant,socket){
  const {PjsipBackend}=load(variant,'src/backends/PjsipBackend.js');
  const b=new PjsipBackend({qemuPath:'unused',kernelPath:'unused',initrdPath:'unused'});
  // Only physical negotiation and the control transport are supplied by the
  // fixture. Actual constructor/write/stop and session ownership methods run.
  b._connected=true;b.state='READY';b.controlSocket=socket;
  b.on('error',e=>{b.observedError=e;});return b;
}
async function session(variant,b,network){
  const {CallSession}=load(variant,'src/session/CallSession.js');
  const {TelnetProxy}=load(variant,'src/telnet/TelnetProxy.js',network);
  const c=Object.create(CallSession.prototype);EventEmitter.call(c);
  Object.assign(c,{_active:true,_dsp:b,_id:'flow-lab',_telnet:new TelnetProxy(),_mode:'b2bua',
    _dialog:{canBye:()=>false},_capture:null,_rtpSock:null,_rtpPort:0,_dspIsPooled:false});
  c._onModemConnected();await until(()=>c._telnet._txCallback);return c;
}
async function modeled(){
  let sock=new Socket(),b=backend('baseline',sock);
  assert.throws(()=>b.write(Buffer.alloc(8192)),RangeError);assertions++;
  sock.ready=false;eq(b.write(Buffer.from('x')),undefined);
  const stock={oversize_throws:true,write_pressure_not_returned:true};
  let s=await session('baseline',b);sock.ready=true;sock.frames=[];
  s._telnet._send(Buffer.alloc(8192));eq(sock.frames.length,0);eq(s._active,true);
  stock.session_swallows_oversize_failure=true;s.hangup('test');await tick();

  sock=new Socket();b=backend('candidate',sock);const data=Buffer.from(Array.from({length:65536},(_,i)=>i&255));
  eq(b.write(data),true);eq(decode(sock.frames),data);
  sock.frames=[];eq(b.write(new Uint8Array([0,255])),true);eq(b.write('é'),true);
  eq(decode(sock.frames),Buffer.from([0,255,0xc3,0xa9]));
  assert.throws(()=>b.write({bad:true}),TypeError);assertions++;
  sock.frames=[];sock.ready=false;let drains=0;b.on('drain',()=>drains++);
  const mutable=Buffer.from(data);eq(b.write(mutable),false);mutable.fill(0);
  ok(b._dataWriter.length>0 && b._dataWriter.length<=262144);
  sock.drain();eq(decode(sock.frames),data);eq(drains,1);
  sock.frames=[];const expected=[];
  for(let i=0;i<40;i++){const part=Buffer.alloc(8191,i);expected.push(part);eq(b.write(part),true);}
  eq(decode(sock.frames),Buffer.concat(expected)); // Cross the ring boundary.
  sock.frames=[];sock.ready=false;eq(b.write(Buffer.alloc(262144,42)),false);
  const retained=b._dataWriter.length;
  assert.throws(()=>b.write(Buffer.from('overflow')),RangeError);assertions++;
  eq(b._dataWriter.length,retained);sock.drain();eq(decode(sock.frames),Buffer.alloc(262144,42));
  await b.stop();eq(sock.listenerCount('drain'),0);
  // Failure during asynchronous drain retires the queue and reports an error.
  sock=new Socket();b=backend('candidate',sock);sock.ready=false;
  eq(b.write(data),false);sock.throwOnWrite=true;sock.drain();
  eq(b.observedError.message,'Modeled socket failure');eq(b._dataWriter.closed,true);
  eq(sock.listenerCount('drain'),0);await b.stop();
  // An unexpected socket replacement must not silently reuse/discard ownership.
  sock=new Socket();b=backend('candidate',sock);sock.ready=false;eq(b.write(data),false);
  const replacement=new Socket();b.controlSocket=replacement;
  assert.throws(()=>b.write(Buffer.from('new')),/replaced/);assertions++;
  eq(replacement.frames.length,0);eq(sock.listenerCount('drain'),0);await b.stop();

  let bbs;
  const network={connect(port,host,fn){eq(host,'127.0.0.1');bbs=new Socket();queueMicrotask(fn);return bbs;}};
  sock=new Socket();b=backend('candidate',sock);s=await session('candidate',b,network);
  s._telnet.receive(Buffer.from('127.0.0.1:2323\r'));await tick();eq(s._telnet.state,'PROXYING');
  bbs.emit('data',Buffer.from([255,251,0]));sock.frames=[];sock.ready=false;
  bbs.emit('data',telnetEncode(data.subarray(0,4093)));eq(bbs.paused,true);eq(s._telnet._outputBlocked,true);
  // false accepted the bytes. A single drain must not replay that frame.
  sock.drain();eq(decode(sock.frames),data.subarray(0,4093));eq(bbs.paused,false);
  sock.ready=false;bbs.emit('data',telnetEncode(data.subarray(0,4093)));
  const oldWriter=b._dataWriter;s.hangup('test');await tick();
  eq(b.listenerCount('drain'),0);eq(sock.listenerCount('drain'),0);eq(oldWriter.closed,true);
  sock.emit('drain');eq(s._telnet.state,'CLOSING');eq(s._telnet._outputBlocked,false);

  // A banner/menu write can block before a BBS TCP socket even exists.
  sock=new Socket();b=backend('candidate',sock);s=await session('candidate',b,network);
  sock.ready=false;s._telnet._send(Buffer.alloc(4093,65));eq(s._telnet._outputBlocked,true);
  eq(s._telnet._tcpSocket,null);
  s._telnet.receive(Buffer.from('127.0.0.1:2323\r'));await tick();
  eq(bbs.paused,true);eq(s._telnet.state,'PROXYING');
  sock.drain();eq(bbs.paused,false);eq(s._telnet._outputBlocked,false);s.hangup('test');

  sock=new Socket();b=backend('candidate',sock);s=await session('candidate',b);
  let ended;s.once('ended',e=>ended=e.reason);
  s._telnet._send(Buffer.alloc(262145));await tick();
  eq(s._active,false);eq(s._telnet.state,'CLOSING');eq(ended,'modem-write');
  eq(b._dataWriter,null);eq(sock.listenerCount('drain'),0);

  // Native's legacy undefined return remains supported, without claiming that
  // native DSP has acquired flow credit. No native modulation is run here.
  const native=new EventEmitter();let count=0;
  native.write=buf=>{count+=buf.length;};native.stop=()=>{};
  s=await session('candidate',native);s._telnet._send(Buffer.from('native'));
  ok(count>=6);eq(s._telnet._outputBlocked,false);s.hangup('test');
  return stock;
}
async function loopback(){
  const vmServer=net.createServer(),bbsServer=net.createServer();let vmPeer,bbsPeer;
  const frames=[];let wire=Buffer.alloc(0),decoded=0;
  vmServer.on('connection',p=>{vmPeer=p;p.pause();p.on('data',chunk=>{
    wire=Buffer.concat([wire,chunk]);
    while(wire.length>=3){const len=wire.readUInt16LE(0)+2;if(wire.length<len)break;
      const f=Buffer.from(wire.subarray(0,len));eq(f[2],0x14);ok(len<=4096);frames.push(f.subarray(3));decoded+=len-3;wire=wire.subarray(len);}
  });});
  const marker=Buffer.from('PAYLOAD-BEGIN\r\n');const payload=Buffer.alloc(16*1024*1024);
  for(let i=0;i<payload.length;i++)payload[i]=i&255;
  const escaped=Buffer.from(payload.toString('latin1').replace(/\xff/g,'\xff\xff'),'latin1');
  bbsServer.on('connection',p=>{bbsPeer=p;p.write(Buffer.from([255,251,0]));p.write(marker);p.write(escaped);});
  await new Promise(r=>vmServer.listen(0,'127.0.0.1',r));await new Promise(r=>bbsServer.listen(0,'127.0.0.1',r));
  const control=net.connect(vmServer.address().port,'127.0.0.1');await new Promise(r=>control.once('connect',r));
  const b=backend('candidate',control);const s=await session('candidate',b);
  let drains=0;b.on('drain',()=>drains++);
  try{
    s._telnet.receive(Buffer.from(`127.0.0.1:${bbsServer.address().port}\r`));
    await until(()=>s._telnet._outputBlocked,5000);
    ok(s._telnet._tcpSocket.isPaused());ok(b._dataWriter.length<=262144);
    const queued=b._dataWriter.length,buffered=control.writableLength;
    vmPeer.resume();
    await until(()=>decoded>=payload.length+marker.length,8000);
    // Initial bridge status is retained; isolate the remote source's sentinel.
    let all=Buffer.concat(frames),at=all.indexOf(marker);
    await until(()=>{all=Buffer.concat(frames);at=all.indexOf(marker);return at>=0 && all.length>=at+marker.length+payload.length;},8000);
    const received=all.subarray(at+marker.length,at+marker.length+payload.length);
    eq(received,payload);ok(drains>0);
    return {payload_size:payload.length,payload_sha256:crypto.createHash('sha256').update(received).digest('hex'),
      drain_events:drains,retained_payload_when_paused:queued,node_wire_bytes_when_paused:buffered};
  }finally{
    s.hangup('test');if(vmPeer)vmPeer.destroy();if(bbsPeer)bbsPeer.destroy();control.destroy();
    await Promise.all([new Promise(r=>vmServer.close(r)),new Promise(r=>bbsServer.close(r))]);
  }
}
(async()=>{
  const stock=await modeled();const tcp=await loopback();
  const result={passed:true,assertions,stock_defects:stock,loopback:tcp};
  fs.writeFileSync(path.join(root,'checks.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exitCode=1;});
