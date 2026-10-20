'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const net = require('net');
const { EventEmitter } = require('events');
const Module = require('module');
const out = path.resolve(process.argv[2]);
const bytes = (...n) => Buffer.from(n);
const cat = list => Buffer.concat(list);
const tick = () => new Promise(resolve => setImmediate(resolve));
const all = Buffer.from(Array.from({ length: 256 }, (_, i) => i));
let checks = 0;
function eq(actual, expected) { assert.deepEqual(actual, expected); checks++; }
function ok(value) { assert(value); checks++; }

// Only socket transport is modeled here. Load the actual upstream/candidate
// class without overriding its methods, parser, state or configuration loader.
function load(variant, network = net) {
  const file = path.join(out, variant, 'src/telnet/TelnetProxy.js');
  const realRequire = Module.createRequire(file);
  const cfg = realRequire('../../config');
  cfg.logging.level = 'error';
  Object.assign(cfg.telnet, { terminalType: 'ANSI', terminalCols: 80, terminalRows: 25,
    idleTimeoutMs: 0, menuIdleHeartbeatMs: 0, connectTimeoutMs: 2000,
    allowedHosts: ['127.0.0.1'], blockedHosts: [], proxyEscapeByte: null,
    negotiateOptions: true });
  const module = new Module(file);
  module.filename = file;
  module.paths = Module._nodeModulePaths(path.dirname(file));
  module.require = name => name === 'net' ? network : realRequire(name);
  module._compile(fs.readFileSync(file, 'utf8'), file);
  return { Proxy: module.exports.TelnetProxy, cfg };
}

class Socket extends EventEmitter {
  constructor() { super(); this.destroyed = false; this.writes = []; }
  write(data) { ok(!this.destroyed); this.writes.push(Buffer.from(data)); return true; }
  destroy() { this.destroyed = true; setImmediate(() => this.emit('close')); }
}

async function session(variant, options = {}) {
  const sockets = [];
  const network = { connect(port, host, callback) {
    eq(host, '127.0.0.1'); eq(port, 2323);
    const socket = new Socket(); sockets.push(socket); setImmediate(callback); return socket;
  }};
  const { Proxy, cfg } = load(variant, network);
  Object.assign(cfg.telnet, options);
  const proxy = new Proxy(); const display = [];
  proxy.attach(data => display.push(Buffer.from(data)));
  proxy.receive(Buffer.from('127.0.0.1:2323\r'));
  await tick(); eq(proxy.state, 'PROXYING');
  display.length = 0;
  return { proxy, socket: sockets[0], sockets, display, cfg };
}

async function stockDefects() {
  const defects = {};
  let s = await session('stock');
  defects.dimensionsReadFromWrongConfigSection = cat(s.socket.writes).includes(bytes(255,250,31,0,0,0,0,255,240));
  const negotiation = bytes(255, 253, 24, 255, 250, 24, 1, 255, 240);
  s.socket.emit('data', negotiation);
  defects.negotiationLeaksToSerial = cat(s.display).equals(negotiation);
  s.socket.writes.length = 0;
  s.proxy.receive(bytes(255));
  defects.literalIACNotEscaped = cat(s.socket.writes).equals(bytes(255));
  s.proxy.receive(bytes(29));
  defects.singleByteMenuEscapeConsumesPayload = s.proxy.state === 'MENU';
  s.proxy.disconnect();
  s = await session('stock');
  s.socket.writes.length = 0;
  s.proxy.receive(bytes(29, 65));
  defects.coalescedSameEscapeStaysOnline = s.proxy.state === 'PROXYING' && cat(s.socket.writes).equals(bytes(29, 65));
  s.proxy.disconnect();
  ok(Object.values(defects).every(Boolean));
  return defects;
}

function codecChecks() {
  const { TelnetCodec } = require(path.join(out, 'candidate/src/telnet/TelnetCodec.js'));
  function harness() {
    const wire = [], display = [];
    const codec = new TelnetCodec({ send: d => wire.push(d), display: d => display.push(d),
      terminalType: 'ANSI', terminalCols: 255, terminalRows: 511 });
    return { codec, wire, display };
  }
  function binary(h) { h.codec.feed(bytes(255, 253, 0, 255, 251, 0)); h.wire.length = 0; }
  const escaped = TelnetCodec.escape(all);
  // Every possible two-chunk partition, plus singleton chunks, both directions.
  for (let split = 0; split <= escaped.length; split++) {
    const h = harness(); binary(h);
    h.codec.feed(escaped.subarray(0, split)); h.codec.feed(escaped.subarray(split));
    eq(cat(h.display), all);
  }
  for (let split = 0; split <= all.length; split++) {
    const h = harness(); binary(h);
    eq(cat([h.codec.encode(all.subarray(0, split)), h.codec.encode(all.subarray(split))]), escaped);
  }
  let h = harness(); binary(h);
  for (const b of escaped) h.codec.feed(bytes(b));
  eq(cat(h.display), all);
  eq(cat([...all].map(b => h.codec.encode(bytes(b)))), escaped);

  // Fragmented controls, duplicate/crossed offers, option refusals, TTYPE/NAWS.
  const control = bytes(255,253,0,255,251,0,255,253,24,255,250,24,1,255,240,255,253,31);
  let baseline;
  for (let split = 0; split <= control.length; split++) {
    h = harness(); h.codec.start(); h.wire.length = 0;
    h.codec.feed(control.subarray(0, split)); h.codec.feed(control.subarray(split));
    eq(cat(h.display), Buffer.alloc(0));
    const answer = cat(h.wire);
    if (!baseline) baseline = answer;
    eq(answer, baseline);
    eq(answer, Buffer.concat([bytes(255,250,24,0), Buffer.from('ANSI'),
      bytes(255,240,255,250,31,0,255,255,1,255,255,255,240)]));
    h.wire.length = 0; h.codec.feed(bytes(255,253,0,255,251,0,255,253,31));
    eq(cat(h.wire), Buffer.alloc(0));
  }
  h = harness(); h.codec.start(); h.wire.length = 0;
  h.codec.feed(bytes(255,254,0,255,252,0)); // Refuse pending BINARY offers.
  eq(cat(h.wire), Buffer.alloc(0));
  eq(h.codec.local.has(0), false); eq(h.codec.remote.has(0), false);
  h.codec.feed(bytes(255,253,0,255,251,0));
  eq(cat(h.wire), bytes(255,251,0,255,253,0));
  h.wire.length = 0; h.codec.feed(bytes(255,254,0,255,252,0,255,254,0,255,252,0));
  eq(cat(h.wire), bytes(255,252,0,255,254,0));
  h.wire.length = 0; h.codec.feed(bytes(255,253,99,255,251,99));
  eq(cat(h.wire), bytes(255,252,99,255,254,99));

  h = harness();
  h.codec.feed(bytes(13)); h.codec.feed(bytes(0,10,13,10,65));
  eq(cat(h.display), bytes(13,10,13,10,65));
  eq(h.codec.encode(bytes(65,13,10,255)), bytes(65,13,0,10,255,255));
  h = harness();
  h.codec.feed(Buffer.concat([bytes(255,250,24), Buffer.alloc(4096,65)]));
  ok(h.codec.sub.length <= 1024); eq(cat(h.display).length, 0);
  h.codec.feed(bytes(255,240,90)); eq(cat(h.display), Buffer.from('Z'));
  h = harness(); h.codec.feed(bytes(255,250,24,255,253,65,255,240,90));
  eq(cat(h.display), Buffer.from('Z'));
  assert.throws(() => new TelnetCodec({ terminalType: 'bad\n' })); checks++;
  assert.throws(() => new TelnetCodec({ terminalRows: 0 })); checks++;
}

async function candidateProxyChecks() {
  for (const negotiateOptions of [false, true]) {
    const s = await session('candidate', { negotiateOptions });
    for (const b of bytes(255,253,0,255,251,0,255,253,24,255,250,24,1,255,240,255,253,31)) {
      s.socket.emit('data', bytes(b));
    }
    eq(cat(s.display).length, 0);
    ok(cat(s.socket.writes).includes(Buffer.concat([bytes(255,250,24,0), Buffer.from('ANSI'), bytes(255,240)])));
    ok(cat(s.socket.writes).includes(bytes(255,250,31,0,80,0,25,255,240)));
    s.socket.writes.length = 0;
    for (const b of all) s.proxy.receive(bytes(b));
    eq(s.proxy.state, 'PROXYING');
    const expected = Buffer.concat([all, bytes(255)]);
    eq(cat(s.socket.writes), expected);
    for (const b of expected) s.socket.emit('data', bytes(b));
    eq(cat(s.display), all);
    s.display.length = 0;
    s.socket.emit('close');
    eq(s.proxy.state, 'MENU'); ok(cat(s.display).includes(Buffer.from('CONNECT> ')));
    // Reconnect before the previous socket's queued close/error arrives.
    s.proxy.receive(Buffer.from('127.0.0.1:2323\r')); await tick();
    eq(s.proxy.state, 'PROXYING');
    s.socket.emit('error', new Error('stale')); s.socket.emit('close');
    s.socket.emit('data', Buffer.from('STALE'));
    eq(s.proxy.state, 'PROXYING'); ok(!cat(s.display).includes(Buffer.from('STALE')));
    s.proxy.disconnect(); eq(s.proxy._connectTimer, null); eq(s.proxy._telnet, null);
  }
  for (const split of [false, true]) {
    const s = await session('candidate', { proxyEscapeByte: 29 });
    s.socket.emit('data', bytes(255,253,0)); s.socket.writes.length = 0;
    const input = Buffer.from('A\x1dHELP\r');
    if (split) for (const b of input) s.proxy.receive(bytes(b)); else s.proxy.receive(input);
    eq(cat(s.socket.writes), Buffer.from('A')); eq(s.proxy.state, 'MENU');
    ok(cat(s.display).includes(Buffer.from('Commands:')));
    s.proxy.disconnect();
  }
}

async function until(test) {
  const end = Date.now() + 2000;
  while (!test()) {
    if (Date.now() >= end) throw new Error('Loopback observation timed out');
    await new Promise(resolve => setTimeout(resolve, 2));
  }
}

async function loopback() {
  const server = net.createServer(); const wire = [], display = []; let socket;
  server.on('connection', s => { socket = s; s.on('data', d => wire.push(d)); });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const { Proxy } = load('candidate'); const proxy = new Proxy();
  try {
    proxy.attach(d => display.push(d));
    proxy.receive(Buffer.from(`127.0.0.1:${server.address().port}\r`));
    await until(() => socket && proxy.state === 'PROXYING');
    for (const b of bytes(255,253,0,255,251,0,255,253,24,255,250,24,1,255,240,255,253,31)) {
      socket.write(bytes(b)); await tick();
    }
    const type = Buffer.concat([bytes(255,250,24,0), Buffer.from('ANSI'), bytes(255,240)]);
    await until(() => cat(wire).includes(type) &&
      cat(wire).includes(bytes(255,250,31,0,80,0,25,255,240)));
    wire.length = 0; display.length = 0;
    for (const b of all) proxy.receive(bytes(b));
    const expected = Buffer.concat([all, bytes(255)]);
    await until(() => cat(wire).length >= expected.length);
    eq(cat(wire), expected); eq(proxy.state, 'PROXYING');
    socket.write(expected);
    await until(() => cat(display).length >= all.length);
    eq(cat(display), all);
    socket.end(); await until(() => proxy.state === 'MENU');
    ok(cat(display).includes(Buffer.from('CONNECT> ')));
  } finally {
    proxy.disconnect(); if (socket) socket.destroy();
    await new Promise(resolve => server.close(resolve));
  }
}

(async () => {
  const defects = await stockDefects();
  codecChecks();
  await candidateProxyChecks();
  await loopback();
  const result = { passed: true, assertions: checks, stockDefectsObserved: defects,
    candidate: ['all 256 bytes at every two-chunk split and singleton chunks',
      'fragmented Telnet negotiation, TTYPE and escaped NAWS', 'duplicate/crossed offers and refusal',
      'NVT CR policy and bounded malformed/oversize subnegotiation',
      'default binary-safe forwarding and explicit chunk-independent escape opt-in',
      'remote close/menu/reconnect with stale-socket isolation', 'real loopback TCP full-byte duplex'] };
  fs.writeFileSync(path.join(out, 'checks.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
