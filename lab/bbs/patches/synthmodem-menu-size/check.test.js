'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
// The actual staged proxy runs unchanged; only its IO/config/clock boundaries
// are supplied here. The final test uses real Node TCP sockets and timers.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const net = require('node:net');
const {EventEmitter} = require('node:events');
const {createRequire} = require('node:module');
const root = process.env.SYNTH_MENU_SIZE_STAGE;
assert(root, 'run through check.py');
const {WindowSizeReply} = require(path.join(root, 'candidate/src/telnet/WindowSizeReply'));
const B = value => Buffer.from(value, 'latin1');
const cat = chunks => Buffer.concat(chunks);
const query = B('\x1b[18t');
const reply = (rows = 42, cols = 80) => B(`\x1b[8;${rows};${cols}t`);
const escape = bytes => Buffer.from([...bytes].flatMap(b => b === 255 ? [255,255] : [b]));
const naws = (rows, cols) => {
  const value = Buffer.alloc(5); value[0]=31; value.writeUInt16BE(cols,1); value.writeUInt16BE(rows,3);
  return cat([Buffer.from([255,250]),escape(value),Buffer.from([255,240])]);
};
class Clock {
  constructor() { this.id=0; this.active=new Map(); this.all=new Map(); }
  set(fn,ms) { const id=++this.id; this.active.set(id,{fn,ms}); this.all.set(id,fn); return id; }
  clear(id) { this.active.delete(id); }
  fire(id) { const item=this.active.get(id); assert(item); this.active.delete(id); item.fn(); }
}
class Socket extends EventEmitter {
  constructor() { super(); this.writes=[]; this.destroyed=false; this.pauses=0; this.resumes=0; }
  write(data) { this.writes.push(Buffer.from(data)); return true; }
  pause() { this.pauses++; }
  resume() { this.resumes++; }
  destroy() { this.destroyed=true; this.emit('close'); }
}
function harness({variant='candidate', timeout=500, clock=new Clock(), real=false, onSend=null, extra={}}={}) {
  const config=structuredClone(require('./fixture-config'));
  if (timeout !== undefined) config.telnet.terminalSizeProbeTimeoutMs=timeout;
  Object.assign(config.telnet,extra);
  const sockets=[], outputs=[];
  const file=path.join(root,variant,'src/telnet/TelnetProxy.js');
  const actualRequire=createRequire(file);
  const module={exports:{}};
  const dependencies = name => {
    if(name==='../../config') return config;
    if(name==='../logger') return {makeLogger:()=>({info(){},warn(){},debug(){},error(){}})};
    if(name==='net' && !real) return {connect(port,host,cb) { const s=new Socket(); s.host=host;s.port=port;s.once('connect',cb);sockets.push(s);return s; }};
    return actualRequire(name);
  };
  vm.runInNewContext('(function(require,module,exports,Buffer,setTimeout,clearTimeout){'+fs.readFileSync(file,'utf8')+'\n})',{}, {filename:file})(
    dependencies,module,module.exports,Buffer,real?setTimeout:clock.set.bind(clock),real?clearTimeout:clock.clear.bind(clock));
  const proxy=new module.exports.TelnetProxy();
  let disconnects=0; proxy.on('disconnect',()=>disconnects++);
  proxy.attach(data=>{ outputs.push(Buffer.from(data)); if(onSend)onSend(data,proxy); return true; });
  return {proxy,config,sockets,outputs,clock,get disconnects(){return disconnects;}};
}
function begin(h, data='loc\r') { h.proxy.receive(B(data)); return h; }
function connected(h, rows=42, cols=80) {
  const count=h.sockets.length;begin(h);h.proxy.receive(reply(rows,cols));assert.equal(h.sockets.length,count+1);
  const socket=h.sockets[count];socket.emit('connect');assert.equal(h.proxy.state,'PROXYING');return socket;
}
function binary(s) { s.emit('data',Buffer.from([255,253,0,255,251,0])); }

test('collector accepts all boundaries, every split and bytewise input',()=>{
  for(const rows of [1,24,42,49,50,255,256,65535]) for(const cols of [1,80,132,255,256,65535]) {
    const wire=reply(rows,cols);
    for(let split=0;split<=wire.length;split++) {
      const c=new WindowSizeReply();c.feed(wire.subarray(0,split));c.feed(wire.subarray(split));
      assert.deepEqual(c.dimensions,{rows,cols});assert.equal(c.takeInput().length,0);
    }
    const c=new WindowSizeReply(); for(const b of wire)c.feed(Buffer.from([b]));
    assert.deepEqual(c.dimensions,{rows,cols});
  }
});
test('collector rejects invalid reserved replies and bounds retained typing',()=>{
  for(const text of ['0;80','42;0','65536;80','42;65536','123456;80',';80','-1;80','42;;80'])
    assert.throws(()=>new WindowSizeReply().feed(B(`\x1b[8;${text}t`)));
  const c=new WindowSizeReply();const prefix=B('a\x1b[A\x1b\x1b[B');c.feed(prefix);c.feed(reply());c.feed(B('z'));
  assert.deepEqual(c.takeInput(),cat([prefix,B('z')]));
  const full=new WindowSizeReply();full.feed(Buffer.alloc(1024,65));full.feed(reply());assert.equal(full.takeInput().length,1024);
  assert.throws(()=>new WindowSizeReply().feed(Buffer.alloc(1025,65)));
  const first=new WindowSizeReply();first.feed(cat([reply(),reply(49)]));assert.deepEqual(first.takeInput(),reply(49));
});
test('default absent/zero has same wire behavior as pinned stock',()=>{
  for(const timeout of [undefined,0]) {
    const a=harness({variant:'stock',timeout}),b=harness({timeout});
    // Explicitly remove the property for the absent case (destructuring has a default).
    if(timeout===undefined) {delete a.config.telnet.terminalSizeProbeTimeoutMs;delete b.config.telnet.terminalSizeProbeTimeoutMs;}
    for(const h of [a,b]) {begin(h);h.sockets[0].emit('connect');h.sockets[0].emit('data',Buffer.from([255,253,31]));h.proxy.receive(B('abc\r'));}
    assert.deepEqual(cat(a.outputs),cat(b.outputs));assert.deepEqual(cat(a.sockets[0].writes),cat(b.sockets[0].writes));
    assert(cat(b.sockets[0].writes).includes(naws(24,80)));assert(!cat(b.outputs).includes(query));
    a.proxy.disconnect();b.proxy.disconnect();
  }
});
test('single owned query, absolute deadline and all fragmented replies',()=>{
  const wire=reply();
  for(let split=0;split<=wire.length;split++) {
    const h=begin(harness({extra:{menuIdleHeartbeatMs:50}}));
    assert.equal(h.proxy.state,'PROBING');assert.equal(h.sockets.length,0);assert.equal(h.clock.active.size,1);
    const deadline=h.proxy._sizeProbe.timer;
    h.proxy.receive(wire.subarray(0,split));
    if(split<wire.length)assert(h.clock.active.has(deadline));
    h.proxy.receive(wire.subarray(split));assert.equal(h.sockets.length,1);assert.equal(h.proxy.state,'CONNECTING');
    assert.equal(cat(h.outputs).toString('latin1').split('\x1b[18t').length-1,1);
    h.sockets[0].emit('connect');h.sockets[0].emit('data',Buffer.from([255,253,31]));
    assert(cat(h.sockets[0].writes).includes(naws(42,80)));h.proxy.disconnect();assert.equal(h.clock.active.size,0);
  }
});
test('menu CRLF across every split and typing ahead is delivered once',()=>{
  const menu=B('loc\r\nuser');
  for(let split=0;split<=menu.length;split++) {
    const h=harness();h.proxy.receive(menu.subarray(0,split));h.proxy.receive(menu.subarray(split));
    h.proxy.receive(reply());h.proxy.receive(B('name'));const s=h.sockets[0];s.emit('connect');
    const wire=cat(s.writes);assert(wire.subarray(-8).equals(B('username')),`split ${split}`);
    assert.equal(wire.toString('latin1').split('username').length-1,1);h.proxy.disconnect();
  }
});
test('inline terminal reply and inline greeting typing survive callback reentry',()=>{
  const h=harness({onSend(data,proxy){
    if(data.equals(query))proxy.receive(reply());
    else if(data.toString().startsWith('Connected to '))proxy.receive(B('inline'));
  }});
  begin(h);assert.equal(h.sockets.length,1);h.sockets[0].emit('connect');
  assert(cat(h.sockets[0].writes).subarray(-6).equals(B('inline')));h.proxy.disconnect();
});
test('NAWS quotes IAC dimensions and does not send refused sizes',()=>{
  for(const [rows,cols] of [[42,80],[255,255],[65535,65535]]) {
    const h=harness(),s=connected(h,rows,cols);const count=s.writes.length;
    s.emit('data',Buffer.from([255,254,31]));assert(!cat(s.writes.slice(count)).includes(Buffer.from([255,250,31])));
    s.emit('data',Buffer.from([255,253,31]));assert(cat(s.writes).includes(naws(rows,cols)));h.proxy.disconnect();
  }
});
test('timeouts, malformed replies, overflows and invalid config close without opening TCP',()=>{
  for(const action of ['timeout','malformed','overflow']) {
    const h=begin(harness());
    if(action==='timeout')h.clock.fire(h.proxy._sizeProbe.timer);
    if(action==='malformed')h.proxy.receive(reply(0));
    if(action==='overflow')h.proxy.receive(Buffer.alloc(1025,65));
    assert.equal(h.proxy.state,'CLOSING');assert.equal(h.disconnects,1);assert.equal(h.sockets.length,0);assert.equal(h.clock.active.size,0);
    h.proxy.receive(reply());assert.equal(h.sockets.length,0);assert.equal(h.disconnects,1);
  }
  for(const timeout of [-1,10001,1.5,'500',null]) {
    const h=begin(harness({timeout}));assert.equal(h.proxy.state,'CLOSING');assert.equal(h.disconnects,1);assert.equal(h.sockets.length,0);
  }
  const h=begin(harness());h.proxy.receive(reply());h.proxy.receive(Buffer.alloc(1025,65));
  assert.equal(h.proxy.state,'CLOSING');assert(h.sockets[0].destroyed);assert.equal(h.disconnects,1);
});
test('disconnect cancels ownership; stale timer cannot cancel later connection',()=>{
  const h=begin(harness()),timer=h.proxy._sizeProbe.timer;h.proxy.receive(reply());
  h.sockets[0].emit('connect');h.sockets[0].emit('close');assert.equal(h.proxy.state,'MENU');
  begin(h);h.clock.all.get(timer)();assert.equal(h.proxy.state,'PROBING');
  h.proxy.receive(reply(49));const s=h.sockets[1];s.emit('connect');s.emit('data',Buffer.from([255,253,31]));
  assert(cat(s.writes).includes(naws(49,80)));h.proxy.disconnect();assert.equal(h.clock.active.size,0);
  const cancelled=begin(harness()),old=cancelled.proxy._sizeProbe.timer;cancelled.proxy.disconnect();cancelled.clock.all.get(old)();
  cancelled.proxy.receive(reply());assert.equal(cancelled.sockets.length,0);assert.equal(cancelled.proxy.state,'CLOSING');
});
test('old socket events and pending typing cannot escape into the next session',()=>{
  const h=begin(harness());h.proxy.receive(cat([B('private'),reply()]));const old=h.sockets[0];
  old.emit('error',new Error('synthetic failure'));assert.equal(h.proxy.state,'MENU');
  const s=connected(h,49);old.emit('data',B('stale'));old.emit('close');old.emit('error',new Error('stale'));
  assert.equal(h.proxy.state,'PROXYING');assert.equal(h.proxy._tcpSocket,s);assert(!cat(s.writes).includes(B('private')));
  old.destroy=()=>{old.emit('error',new Error('sync'));old.emit('close');};
  h.proxy.disconnect();assert.equal(h.proxy.state,'CLOSING');
});
test('disconnect detaches before synchronous socket error and close',()=>{
  const h=harness(),s=connected(h);s.destroy=()=>{s.destroyed=true;s.emit('error',new Error('sync destroy'));s.emit('close');};
  h.proxy.disconnect();assert.equal(h.proxy.state,'CLOSING');assert.equal(h.proxy._tcpSocket,null);
});
test('all 256 bytes and size lookalikes remain opaque at every split while proxying',()=>{
  const payload=cat([Buffer.from(Array.from({length:256},(_,i)=>i)),reply(),query]);
  const h=harness(),s=connected(h);binary(s);
  for(let split=0;split<=payload.length;split++) {
    let start=s.writes.length;h.proxy.receive(payload.subarray(0,split));h.proxy.receive(payload.subarray(split));
    assert.deepEqual(cat(s.writes.slice(start)),escape(payload));
    assert.equal(h.proxy.state,'PROXYING');assert.equal(h.proxy._telnet.rows,42);
  }
  const wire=escape(payload);
  for(let split=0;split<=wire.length;split++) {
    const start=h.outputs.length;
    s.emit('data',wire.subarray(0,split));s.emit('data',wire.subarray(split));assert.deepEqual(cat(h.outputs.slice(start)),payload);
    assert.equal(h.proxy.state,'PROXYING');assert.equal(h.proxy._telnet.rows,42);
  }
  h.proxy.disconnect();
});
test('ACL denial never emits query or opens socket',()=>{
  const h=begin(harness({extra:{blockedHosts:['127.0.0.1']}}));assert.equal(h.proxy.state,'MENU');
  assert.equal(h.sockets.length,0);assert(!cat(h.outputs).includes(query));h.proxy.disconnect();
});
test('real loopback TCP: fragmented terminal reply, NAWS and bidirectional binary data', {timeout:8000},async()=>{
  const peers=new Set(),received=[];let peer;
  const server=net.createServer(s=>{peer=s;peers.add(s);s.on('close',()=>peers.delete(s));s.on('data',d=>received.push(Buffer.from(d)));s.write(Buffer.from([255,253,31,255,253,0,255,251,0]));});
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  const h=harness({real:true,timeout:2000,onSend(data,proxy){if(data.equals(query))queueMicrotask(()=>{proxy.receive(B('\x1b[8;4'));proxy.receive(B('2;80t'));});}});
  const waitFor=async predicate=>{
    const end=Date.now()+2500;while(!predicate()) {assert(Date.now()<end,'loopback condition deadline');await new Promise(r=>setTimeout(r,5));}
  };
  try {
    h.proxy.receive(B(`127.0.0.1:${server.address().port}\r`));
    await waitFor(()=>cat(received).includes(naws(42,80)) && h.proxy._telnet?.local.has(0) && h.proxy._telnet?.remote.has(0));
    // Wait for the wire NAWS acknowledgment first; payload checks exclude negotiation.
    const payload=cat([Buffer.from(Array.from({length:256},(_,i)=>i)),reply(49),query]);
    const start=cat(received).length;h.proxy.receive(payload);
    await waitFor(()=>cat(received).length>=start+escape(payload).length);
    assert.deepEqual(cat(received).subarray(start),escape(payload));
    const mark=h.outputs.length;peer.write(escape(payload));
    await waitFor(()=>cat(h.outputs.slice(mark)).length>=payload.length);
    assert.deepEqual(cat(h.outputs.slice(mark)),payload);
    peer.end();await waitFor(()=>h.proxy.state==='MENU');
    assert.equal(h.disconnects,0);
  } finally {h.proxy.disconnect();for(const s of peers)s.destroy();await new Promise(r=>server.close(r));}
});

test('inline overflow during connection messages cannot open or resurrect TCP',()=>{
  for(const prefix of ['Connecting to ','Connected to ']) {
    const h=harness({onSend(data,proxy){if(data.toString().startsWith(prefix))proxy.receive(Buffer.alloc(1025,65));}});
    begin(h);h.proxy.receive(reply());
    if(prefix==='Connected to ')h.sockets[0].emit('connect');
    assert.equal(h.proxy.state,'CLOSING');assert.equal(h.disconnects,1);
    assert.equal(h.proxy._tcpSocket,null);assert.equal(h.proxy._telnet,null);assert.equal(h.clock.active.size,0);
    if(prefix==='Connecting to ')assert.equal(h.sockets.length,0);
  }
});
test('cancelled connect deadline cannot cancel a newer TCP connection',()=>{
  const h=begin(harness());h.proxy.receive(reply());const deadline=h.proxy._connectTimer;
  h.sockets[0].emit('connect');h.sockets[0].emit('close');const current=connected(h,49);
  h.clock.all.get(deadline)();assert.equal(h.proxy.state,'PROXYING');assert.equal(h.proxy._tcpSocket,current);h.proxy.disconnect();
});

test('solicited NAWS works without initial offers; query backpressure survives until resume',()=>{
  const h=harness({extra:{negotiateOptions:false}});
  h.proxy.attach(data=>{h.outputs.push(Buffer.from(data));return !data.equals(query);});
  begin(h);h.proxy.receive(reply());const socket=h.sockets[0];
  assert.equal(socket.pauses,1);socket.emit('connect');assert.equal(socket.writes.length,0);
  h.proxy.resumeOutput();assert.equal(socket.resumes,1);
  socket.emit('data',Buffer.from([255,253,31]));assert(cat(socket.writes).includes(naws(42,80)));h.proxy.disconnect();
});
