'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
const assert = require('assert/strict'), fs = require('fs'), path = require('path');
const Module = require('module'), {EventEmitter} = require('events');
const {InputSequenceFramer} = require('./InputSequenceFramer');
const runtime = path.resolve(process.argv[2]);
const checks = {};
const cat = xs => Buffer.concat(xs), buf = s => Buffer.from(s, 'latin1');
const tick = () => new Promise(r => setImmediate(r));
function clock() {
  let now = 0, id = 0; const timers = new Map();
  return {schedule(fn, ms) {const n = id++; timers.set(n, {fn, at: now + ms}); return n;},
    cancel(n) {timers.delete(n);},
    advance(ms) {now += ms; for (const [n, v] of [...timers]) if (v.at <= now) {timers.delete(n); v.fn();}},
    get count() {return timers.size;}};
}
function harness(options = {}) {
  const c = clock(), frames = [], f = new InputSequenceFramer(b => frames.push(b), {...c, ...options});
  return {c, frames, f};
}
function unit() {
  const keys = ['\x1b[H', '\x1b[F', '\x1b[D', '\x1b[3~', '\x1b[2~', '\x1b[5~', '\x1b[6~',
    '\x1b[?1;2c', '\x1b[24;80R', '\x1bOP', '\x1b[[A', '\x1b[M !!'];
  for (const key of keys) {
    const data = buf(key);
    for (let split = 0; split <= data.length; split++) {
      const h = harness(); h.f.feed(data.subarray(0, split)); h.f.feed(data.subarray(split));
      assert.deepEqual(h.frames, [data]); assert.equal(h.c.count, 0);
    }
    const h = harness(); for (const byte of data) {h.f.feed(Buffer.from([byte])); h.c.advance(8);}
    assert.deepEqual(h.frames, [data]); assert.equal(h.c.count, 0);
  }
  checks.complete_keys_DA_CPR_all_splits_and_1200_baud_pacing = true;
  let h = harness(); h.f.feed(buf('AB')); assert.deepEqual(h.frames, [buf('AB')]);
  h.f.feed(buf('\x1b')); h.c.advance(249); assert.equal(h.frames.length, 1);
  h.c.advance(1); assert.deepEqual(h.frames, [buf('AB'), buf('\x1b')]); assert.equal(h.c.count, 0);
  checks.plain_input_immediate_and_lone_escape_deadline = true;
  h = harness(); h.f.feed(buf('\x1b[')); h.c.advance(240); h.f.feed(buf('1'));
  h.c.advance(10); assert.deepEqual(h.frames, [buf('\x1b[1')]);
  h.f.feed(buf('~')); assert.deepEqual(cat(h.frames), buf('\x1b[1~'));
  checks.trickle_does_not_extend_absolute_deadline = true;
  h = harness({limit: 4}); const malformed = buf('\x1b[123456\x1b[\x00\x1b\x1bOH\x1b\xff');
  for (const b of malformed) h.f.feed(Buffer.from([b])); h.f.flush();
  assert.deepEqual(cat(h.frames), malformed); assert.equal(h.c.count, 0);
  assert(h.frames.every(v => v.length <= 4)); checks.invalid_oversize_and_repeated_escape_preserve_bytes = true;
  const all = Buffer.from(Array.from({length: 256}, (_, i) => i));
  for (let split = 0; split <= all.length; split++) {
    h = harness(); h.f.feed(all.subarray(0, split)); h.f.feed(all.subarray(split)); h.f.flush();
    assert.deepEqual(cat(h.frames), all); assert.equal(h.c.count, 0);
  }
  h = harness(); for (const b of all) h.f.feed(Buffer.from([b])); h.f.flush();
  assert.deepEqual(cat(h.frames), all); checks.all_256_bytes_all_two_part_splits_and_singletons = true;
  h = harness(); h.f.feed(buf('\x1b[')); h.f.close(); h.c.advance(1000); h.f.feed(buf('H'));
  assert.equal(h.frames.length, 0); assert.equal(h.c.count, 0); checks.close_cancels_pending_and_rejects_later_bytes = true;
  for (const opts of [{timeout: 0}, {timeout: 2001}, {timeout: NaN}, {limit: 3}, {limit: 1025}]) {
    assert.throws(() => new InputSequenceFramer(() => {}, opts), RangeError);
  }
  checks.invalid_bounds_rejected = true;
}
class Socket extends EventEmitter {
  constructor() {super(); this.frames = []; this.destroyed = false;}
  write(b) {assert(!this.destroyed); this.frames.push(Buffer.from(b)); return true;}
  pause() {} resume() {}
  destroy() {this.destroyed = true; setImmediate(() => this.emit('close'));}
}
async function proxy(timeout) {
  const filename = path.join(runtime, 'source/src/telnet/TelnetProxy.js'), real = Module.createRequire(filename);
  const cfg = real('../../config'); cfg.logging.level = 'error';
  Object.assign(cfg.telnet, {inputSequenceTimeoutMs: timeout, terminalType: 'ANSI', terminalCols: 80, terminalRows: 25,
    idleTimeoutMs: 0, menuIdleHeartbeatMs: 0, connectTimeoutMs: 2000, allowedHosts: ['127.0.0.1'], blockedHosts: [],
    proxyEscapeByte: null, negotiateOptions: false});
  cfg.terminal.localEcho = false;
  const sockets = [], network = {connect(port, host, connected) {
    const s = new Socket(); sockets.push(s); setImmediate(connected); return s;
  }};
  const m = new Module(filename); m.filename = filename; m.paths = Module._nodeModulePaths(path.dirname(filename));
  m.require = n => n === 'net' ? network : real(n); m._compile(fs.readFileSync(filename, 'utf8'), filename);
  const p = new m.exports.TelnetProxy(); p.attach(() => {}); p.receive(buf('127.0.0.1:2323\r')); await tick();
  assert.equal(p.state, 'PROXYING'); return {p, sockets};
}
async function integration() {
  let {p, sockets} = await proxy(undefined);
  for (const byte of buf('\x1b[H')) p.receive(Buffer.from([byte]));
  assert.deepEqual(sockets[0].frames, [buf('\x1b'), buf('['), buf('H')]); p.disconnect();
  checks.actual_proxy_default_unchanged = true;
  ({p, sockets} = await proxy(250));
  for (const byte of buf('\x1b[H')) p.receive(Buffer.from([byte]));
  assert.deepEqual(sockets[0].frames, [buf('\x1b[H')]); checks.actual_proxy_opt_in_assembles_key = true;
  // Negotiate BINARY, then verify the actual codec escapes FF after framing.
  sockets[0].emit('data', Buffer.from([255, 253, 0, 255, 251, 0])); sockets[0].frames = [];
  const all = Buffer.from(Array.from({length: 256}, (_, i) => i));
  for (const byte of all) p.receive(Buffer.from([byte]));
  assert.deepEqual(cat(sockets[0].frames), Buffer.from(all.toString('latin1').replace(/\xff/g, '\xff\xff'), 'latin1'));
  checks.actual_proxy_binary_codec_preserves_every_byte = true;
  sockets[0].frames = []; p.receive(buf('\x1b[')); sockets[0].emit('close');
  p.receive(buf('127.0.0.1:2323\r')); await tick();
  p.receive(buf('H')); assert.deepEqual(sockets[1].frames, [buf('H')]);
  await new Promise(r => setTimeout(r, 275));
  assert.deepEqual(sockets[1].frames, [buf('H')]); p.disconnect();
  checks.actual_proxy_close_does_not_leak_pending_to_reconnect = true;
}
(async () => {unit(); await integration(); console.log(JSON.stringify({passed: true, checks}, null, 2));})()
  .catch(e => {console.error(e.stack); process.exitCode = 1;});
