'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
// Actual TCP sockets and staged proxy/codec; no replacement parser or transport.
const assert = require('assert/strict'), fs = require('fs'), path = require('path'), net = require('net');
const runtime = path.resolve(process.argv[2]), output = path.resolve(process.argv[3]);
const base = path.join(runtime, 'source');
const cfg = require(path.join(base, 'config.js'));
const {TelnetProxy} = require(path.join(base, 'src/telnet/TelnetProxy.js'));
const {TelnetCodec} = require(path.join(base, 'src/telnet/TelnetCodec.js'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(fn) {const end = Date.now() + 5000; while (!fn()) {assert(Date.now() < end, 'Observation deadline'); await sleep(2);}}
const cat = xs => Buffer.concat(xs), key = Buffer.from('\x1b[H', 'latin1');
async function run(timeout) {
  const application = [], serial = [], events = []; let peer, codec, proxy;
  const server = net.createServer(socket => {
    peer = socket; socket.setNoDelay(true);
    codec = new TelnetCodec({send: b => socket.write(b), display: b => {
      application.push(Buffer.from(b)); events.push({hex: b.toString('hex')});
      socket.write(codec.encode(b));
    }});
    socket.on('data', b => codec.feed(b)); socket.on('error', e => {throw e;}); codec.start();
  });
  try {
    await new Promise(r => server.listen(0, '127.0.0.1', r));
    cfg.logging.level = 'error';
    Object.assign(cfg.telnet, {inputSequenceTimeoutMs: timeout, terminalType: 'ANSI', terminalCols: 80, terminalRows: 25,
      idleTimeoutMs: 0, menuIdleHeartbeatMs: 0, connectTimeoutMs: 2000, allowedHosts: ['127.0.0.1'], blockedHosts: [],
      proxyEscapeByte: null, negotiateOptions: true});
    Object.assign(cfg.terminal, {banner: '', prompt: '', localEcho: false});
    proxy = new TelnetProxy(); proxy.attach(b => serial.push(Buffer.from(b)));
    proxy.receive(Buffer.from(`127.0.0.1:${server.address().port}\r`));
    await until(() => codec?.local.has(0) && codec?.remote.has(0) && proxy._telnet?.local.has(0) && proxy._telnet?.remote.has(0));
    await sleep(20); serial.length = 0;
    for (const b of key) {proxy.receive(Buffer.from([b])); await sleep(8);}
    await until(() => cat(application).length === key.length && cat(serial).length === key.length);
    assert.deepEqual(cat(application), key); assert.deepEqual(cat(serial), key);
    const homeEvents = events.slice();
    const all = Buffer.from(Array.from({length: 256}, (_, i) => i));
    for (const b of all) {proxy.receive(Buffer.from([b])); await sleep(1);}
    const expected = Buffer.concat([key, all]);
    await until(() => cat(application).length === expected.length && cat(serial).length === expected.length);
    assert.deepEqual(cat(application), expected); assert.deepEqual(cat(serial), expected);
    const result = {timeout_ms: timeout, application_bytes: expected.length, echo_bytes: cat(serial).length,
      upstream_exact: true, downstream_exact: true, Home_delivery_events: homeEvents,
      Home_in_one_actual_TCP_delivery: homeEvents.length === 1 && homeEvents[0].hex === key.toString('hex')};
    proxy.disconnect(); peer.destroy(); return result;
  } finally {
    proxy?.disconnect(); peer?.destroy(); await new Promise(r => server.close(r));
  }
}
(async () => {
  const baseline = await run(0), candidate = await run(250);
  assert(!baseline.Home_in_one_actual_TCP_delivery); assert(candidate.Home_in_one_actual_TCP_delivery);
  const result = {passed: true, baseline, candidate,
    scope: 'Actual local TCP/codec readback of paced Home and all256 bytes in both directions. Local event boundaries are observed, never guaranteed for arbitrary networks. No modem, DOS, BBS editor or physical hardware claim.'};
  fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify(result, null, 2));
})().catch(e => {console.error(e.stack); process.exitCode = 1;});
