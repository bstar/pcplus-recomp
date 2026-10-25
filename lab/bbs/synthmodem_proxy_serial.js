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
}});
if (!values.runtime || !values.output) throw new Error('--runtime and --output required');
const runtime = fs.realpathSync(values.runtime), output = path.resolve(values.output);
const root = path.resolve(__dirname, '../..');
if (!output.startsWith(root + '/build/')) throw new Error('Output must be inside ignored build/');
const port = Number(values['bbs-port']), timeout = Number(values['framing-ms']);
const delay = Number(values['byte-delay-ms']);
if (![23233, 23234].includes(port)) throw new Error('Only isolated ENiGMA lab ports allowed');
if (![0, 250].includes(timeout) || !Number.isInteger(delay) || delay < 0 || delay > 20) {
  throw new Error('Invalid framing/delivery settings');
}
fs.mkdirSync(output, {recursive: false});
const config = require(path.join(runtime, 'config.js'));
config.logging.level = 'error';
Object.assign(config.telnet, {terminalType: 'ANSI', terminalCols: 80, terminalRows: 25,
  inputSequenceTimeoutMs: timeout, idleTimeoutMs: 0, menuIdleHeartbeatMs: 0,
  allowedHosts: ['127.0.0.1'], blockedHosts: [], proxyEscapeByte: null});
config.terminal.aliases = {loc: `127.0.0.1:${port}`, '1': `127.0.0.1:${port}`};
const {TelnetProxy} = require(path.join(runtime, 'src/telnet/TelnetProxy.js'));
const sources = ['config.js', 'src/telnet/TelnetProxy.js', 'src/telnet/TelnetCodec.js',
  'src/telnet/InputSequenceFramer.js', 'src/logger.js'];
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const identities = Object.fromEntries(sources.map(f => [f, hash(path.join(runtime, f))]));
const sessions = new Set(); let count = 0;
const server = net.createServer(socket => {
  const id = ++count, proxy = new TelnetProxy(), sent = [], received = [];
  let chain = Promise.resolve(), closed = false;
  sessions.add(socket);
  proxy.attach(data => {if (!closed) {received.push(Buffer.from(data)); socket.write(data);}});
  socket.on('data', data => {
    sent.push(Buffer.from(data));
    chain = chain.then(async () => {
      if (!delay) {if (!closed) proxy.receive(data); return;}
      for (const byte of data) {
        if (closed) break;
        proxy.receive(Buffer.from([byte]));
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }).catch(error => {console.error(error); socket.destroy(); process.exitCode = 1;});
  });
  socket.on('error', error => {console.error(error.message); process.exitCode = 1;});
  socket.on('close', () => {
    closed = true; proxy.disconnect(); sessions.delete(socket);
    fs.writeFileSync(path.join(output, `${id}-serial-input.bin`), Buffer.concat(sent));
    fs.writeFileSync(path.join(output, `${id}-serial-output.bin`), Buffer.concat(received));
    fs.writeFileSync(path.join(output, `${id}-closed.json`), JSON.stringify({closed: true,
      source_unchanged: sources.every(f => hash(path.join(runtime, f)) === identities[f])}, null, 2));
  });
});
server.listen(0, '127.0.0.1', () => {
  fs.writeFileSync(path.join(output, 'ready.json'), JSON.stringify({pid: process.pid,
    endpoint: server.address(), bbsPort: port, inputSequenceTimeoutMs: timeout,
    inputByteDelayMs: delay, installed_sources: identities,
    scope: 'Actual SynthModem proxy with loopback-only configuration overrides; no DSP/audio or hardware.'}, null, 2));
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => {
  for (const socket of sessions) socket.destroy();
  server.close();
});
