'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
// Isolated serial-side adapter for the actual installed SynthModem proxy.
// No SIP, DSP, modem command replies or terminal reports are generated here.
const fs = require('node:fs'), path = require('node:path');
const net = require('node:net'), crypto = require('node:crypto');
const {parseArgs} = require('node:util');
const {values} = parseArgs({options: {
  runtime: {type: 'string'}, output: {type: 'string'},
  'bbs-port': {type: 'string', default: '23233'},
  'framing-ms': {type: 'string', default: '0'},
  'byte-delay-ms': {type: 'string', default: '0'},
  'terminal-rows': {type: 'string', default: '25'},
  'screen-reference': {type: 'boolean', default: false},
  'probe-terminal-size': {type: 'boolean', default: false},
  'screen-quiet-ms': {type: 'string', default: '750'},
  'freeze-trigger': {type: 'string', default: 'UNSAVED'},
}});
if (!values.runtime || !values.output) throw new Error('--runtime and --output required');
const runtime = fs.realpathSync(values.runtime), output = path.resolve(values.output);
const root = path.resolve(__dirname, '../..');
if (!output.startsWith(root + '/build/')) throw new Error('Output must be inside ignored build/');
const port = Number(values['bbs-port']), timeout = Number(values['framing-ms']);
const delay = Number(values['byte-delay-ms']);
const rows = Number(values['terminal-rows']);
const quietMs = Number(values['screen-quiet-ms']);
const trigger = values['freeze-trigger'];
if (!/^[A-Z]{3,20}$/.test(trigger)) throw new Error('Invalid owned freeze trigger');
if (![24,25,27,28,42,43,49,50].includes(rows)) throw new Error('Unsupported owned terminal row count');
if (![150,750].includes(quietMs)) throw new Error('Only measured screen capture intervals supported');
if (![23231,23233,23234,23239].includes(port)) throw new Error('Only owned loopback BBS ports allowed');
if (![0, 250].includes(timeout) || !Number.isInteger(delay) || delay < 0 || delay > 20) {
  throw new Error('Invalid framing/delivery settings');
}
fs.mkdirSync(output, {recursive: false});
const config = require(path.join(runtime, 'config.js'));
config.logging.level = 'error';
Object.assign(config.telnet, {terminalType: 'ANSI', terminalCols: 80, terminalRows: rows,
  inputSequenceTimeoutMs: timeout, idleTimeoutMs: 0, menuIdleHeartbeatMs: 0,
  allowedHosts: ['127.0.0.1'], blockedHosts: [], proxyEscapeByte: null});
config.terminal.aliases = {loc: `127.0.0.1:${port}`, '1': `127.0.0.1:${port}`};
const {TelnetProxy} = require(path.join(runtime, 'src/telnet/TelnetProxy.js'));
const sources = ['config.js', 'src/telnet/TelnetProxy.js', 'src/telnet/TelnetCodec.js',
  'src/telnet/InputSequenceFramer.js', 'src/logger.js'];
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const identities = Object.fromEntries(sources.map(f => [f, hash(path.join(runtime, f))]));
if (values['probe-terminal-size']) {
  config.telnet.terminalSizeProbeTimeoutMs = 3000;
  sources.push('src/telnet/WindowSizeReply.js', 'COPYING');
  for (const f of sources) identities[f] = hash(path.join(runtime, f));
}
// Optional byte-transparent loopback relay captures what the real BBS receives.
// It neither negotiates Telnet nor manufactures terminal replies.
const relaySockets = new Set(); let relayCount = 0;
const relay = values['probe-terminal-size'] ? net.createServer(client => {
  const id = ++relayCount, sent = [], received = [];
  const upstream = net.createConnection({host: '127.0.0.1', port});
  relaySockets.add(client); relaySockets.add(upstream);
  client.on('data', b => sent.push(Buffer.from(b)));
  upstream.on('data', b => received.push(Buffer.from(b)));
  client.pipe(upstream); upstream.pipe(client);
  client.on('error', e => {console.error(e); upstream.destroy(); process.exitCode = 1;});
  upstream.on('error', e => {console.error(e); client.destroy(); process.exitCode = 1;});
  client.on('close', () => {
    upstream.destroy(); relaySockets.delete(client);
    fs.writeFileSync(path.join(output, `${id}-telnet-input.bin`), Buffer.concat(sent));
    fs.writeFileSync(path.join(output, `${id}-telnet-output.bin`), Buffer.concat(received));
  });
  upstream.on('close', () => {client.end(); relaySockets.delete(upstream);});
}) : null;
const sessions = new Set(); let count = 0;
const server = net.createServer(socket => {
  const id = ++count, proxy = new TelnetProxy(), sent = [], received = [];
  let chain = Promise.resolve(), closed = false;
  let armed = false, frozen = false, timer = null, prefix = null;
  let probePending = false, probeBuffer = Buffer.alloc(0), probeTimer = null;
  const held = [], passed = [], replyWire = [], proxyInput = [];
  const oracle = {enabled: values['screen-reference'], terminalRows: rows,
    trigger, quietMs, reply: null, probeReplyConsumed: false};
  function freeze() {
    if (!armed || frozen || closed) return;
    frozen = true;
    probePending = true;
    probeTimer = setTimeout(() => {
      oracle.probeTimeout = true; probePending = false;
      enqueue(probeBuffer); probeBuffer = Buffer.alloc(0);
    },2000);
    const query = Buffer.from('\x1b[6n');
    received.push(query); socket.write(query);
    prefix = Buffer.concat(received);
    oracle.prefixBytes = prefix.length;
    oracle.prefixSha256 = crypto.createHash('sha256').update(prefix).digest('hex');
  }
  function schedule() {
    if (!values['screen-reference'] || !armed || frozen || closed) return;
    clearTimeout(timer); timer = setTimeout(freeze, oracle.quietMs);
  }
  function inputPassed(data) {
    if (!values['screen-reference'] || armed) return;
    passed.push(...data);
    if (Buffer.from(passed).includes(Buffer.from(trigger))) {
      armed = true; schedule();
    }
  }
  sessions.add(socket);
  proxy.attach(data => {
    if (closed) return;
    if (frozen) {held.push(Buffer.from(data)); return;}
    received.push(Buffer.from(data)); socket.write(data); schedule();
  });
  function enqueue(data) {
    if (!data.length) return;
    chain = chain.then(async () => {
      if (!delay) {if (!closed) {proxyInput.push(Buffer.from(data)); proxy.receive(data); inputPassed(data);} return;}
      for (const byte of data) {
        if (closed) break;
        proxyInput.push(Buffer.from([byte])); proxy.receive(Buffer.from([byte]));
        inputPassed(Buffer.from([byte]));
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }).catch(error => {console.error(error); socket.destroy(); process.exitCode = 1;});
  }
  socket.on('data', data => {
    sent.push(Buffer.from(data));
    if (frozen) replyWire.push(Buffer.from(data));
    if (probePending) {
      probeBuffer = Buffer.concat([probeBuffer,data]);
      const match = /\x1b\[(\d+);(\d+)R/.exec(probeBuffer.toString('latin1'));
      if (!match) {
        if (probeBuffer.length>128) {
          oracle.probeOverflow = true; clearTimeout(probeTimer); probePending = false;
          enqueue(probeBuffer); probeBuffer = Buffer.alloc(0);
        }
        return;
      }
      oracle.reply = [Number(match[1]),Number(match[2])];
      oracle.probeReplyHex = Buffer.from(match[0],'latin1').toString('hex');
      oracle.probeReplyConsumed = true;
      clearTimeout(probeTimer); probePending = false;
      // The query originated here. Consume only its real reply here; never
      // inject it as editor input into the stock BBS. Preserve all other TX.
      enqueue(Buffer.concat([probeBuffer.subarray(0,match.index),probeBuffer.subarray(match.index+match[0].length)]));
      probeBuffer = Buffer.alloc(0);
      return;
    }
    enqueue(data);
  });
  socket.on('error', error => {console.error(error.message); process.exitCode = 1;});
  socket.on('close', () => {
    clearTimeout(timer); clearTimeout(probeTimer);
    closed = true; proxy.disconnect(); sessions.delete(socket);
    fs.writeFileSync(path.join(output, `${id}-serial-input.bin`), Buffer.concat(sent));
    fs.writeFileSync(path.join(output, `${id}-serial-output.bin`), Buffer.concat(received));
    fs.writeFileSync(path.join(output, `${id}-closed.json`), JSON.stringify({closed: true,
      source_unchanged: sources.every(f => hash(path.join(runtime, f)) === identities[f])}, null, 2));
    if (values['screen-reference']) {
      oracle.armed = armed; oracle.frozen = frozen;
      oracle.heldBytes = Buffer.concat(held).length;
      fs.writeFileSync(path.join(output, `${id}-screen-prefix.bin`), prefix || Buffer.alloc(0));
      fs.writeFileSync(path.join(output, `${id}-held-output.bin`), Buffer.concat(held));
      fs.writeFileSync(path.join(output, `${id}-probe-input.bin`), Buffer.concat(replyWire));
      fs.writeFileSync(path.join(output, `${id}-proxy-input.bin`), Buffer.concat(proxyInput));
      fs.writeFileSync(path.join(output, `${id}-screen-reference.json`), JSON.stringify(oracle,null,2));
    }
  });
});
function listenSerial() {
 server.listen(0, '127.0.0.1', () => {
  fs.writeFileSync(path.join(output, 'ready.json'), JSON.stringify({pid: process.pid,
    endpoint: server.address(), bbsPort: port, inputSequenceTimeoutMs: timeout,
    inputByteDelayMs: delay, installed_sources: identities,
    terminalRows: rows, screenReference: values['screen-reference'],
    terminalSizeProbe: values['probe-terminal-size'],
    scope: 'Actual SynthModem proxy with loopback-only configuration overrides; no DSP/audio or hardware.'}, null, 2));
 });
}
if (relay) relay.listen(0, '127.0.0.1', () => {
  config.terminal.aliases = {loc: `127.0.0.1:${relay.address().port}`, '1': `127.0.0.1:${relay.address().port}`};
  listenSerial();
}); else listenSerial();
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => {
  for (const socket of sessions) socket.destroy();
  server.close();
  for (const socket of relaySockets) socket.destroy();
  relay?.close();
});
