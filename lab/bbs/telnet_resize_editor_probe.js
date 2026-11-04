'use strict';
// Owned loopback fixture only. Drafts are discarded, never saved.
const net = require('node:net');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const [codecPath, logPath, output, mode] = process.argv.slice(2);
assert(['control', 'resize'].includes(mode));
const { TelnetCodec } = require(codecPath);
const start = fs.statSync(logPath).size;
const socket = net.createConnection({ host: '127.0.0.1', port: 23233 });
const display = [], wireIn = [], wireOut = [], steps = [];
let scan = '', failure, session;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const codec = new TelnetCodec({
  terminalType: 'ANSI', terminalCols: 80, terminalRows: 24,
  send: b => { wireOut.push(Buffer.from(b)); socket.write(b); },
  display: b => {
    display.push(Buffer.from(b));
    // Explicit reference-peer home CPR, as in the existing editor reference.
    // This probe is not a PCPlus renderer or terminal-emulation proof.
    scan += b.toString('latin1');
    while (scan.includes('\x1b[6n')) {
      const at = scan.indexOf('\x1b[6n');
      scan = scan.slice(at + 4);
      send(Buffer.from('\x1b[1;1R'));
    }
    scan = scan.slice(-4);
  },
});
function send(b) { const encoded = codec.encode(b); wireOut.push(encoded); socket.write(encoded); }
function rows() {
  return fs.readFileSync(logPath).subarray(start).toString().split('\n').filter(Boolean)
    .flatMap(line => { try { return [JSON.parse(line)]; } catch { return []; } });
}
function menu() {
  const r = rows().filter(r => r.sessionId === session && r.menuName);
  return r.length ? r.at(-1).menuName : null;
}
function plain(b) { return b.toString('latin1').replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, ''); }
async function step(name, data, delay = 700) {
  if (failure) throw failure;
  const before = Buffer.concat(display).length;
  if (data) send(Buffer.from(data, 'latin1'));
  await sleep(delay);
  if (failure) throw failure;
  const chunk = Buffer.concat(display).subarray(before);
  fs.writeFileSync(path.join(output, name + '.bin'), chunk);
  steps.push({ name, menu: menu(), received: chunk.length,
    positions: [...plain(chunk).matchAll(/(INS|OVR)\s+(\d+),(\d+)/g)]
      .map(m => [m[1], Number(m[2]), Number(m[3])]) });
}
async function resize(name, height) {
  const before = Buffer.concat(display).length;
  const result = mode === 'resize' ? codec.resize(80, height) : null;
  await sleep(500);
  steps.push({ name, result, received: Buffer.concat(display).length - before, menu: menu() });
}
socket.on('data', b => { wireIn.push(Buffer.from(b)); codec.feed(b); });
socket.on('error', e => { failure = e; });
const watchdog = setTimeout(() => { failure = new Error('editor probe deadline'); socket.destroy(); }, 55000);
async function main() {
  await new Promise((resolve, reject) => { socket.once('connect', resolve); socket.once('error', reject); });
  codec.start();
  await step('matrix', null, 3000);
  const sessions = new Set(rows().filter(r => r.source === 'NAWS').map(r => r.sessionId));
  assert.equal(sessions.size, 1); session = [...sessions][0];
  await step('login', '\r'); await step('username', 'loclab\r');
  await step('password', 'LoC-Lab-2026!\r', 1500);
  for (let i = 0; i < 20 && menu() !== 'mainMenu'; ++i) {
    const m = menu();
    await step('advance-' + i, m === 'fullLoginSequenceOnelinerz' ? '\x1b' :
      m === 'fullLoginSequenceNewScanConfirm' ? 'N' : '\r', 700);
  }
  assert.equal(menu(), 'mainMenu');
  for (const [name, data] of [['messages','M\r'], ['conferences','J\r'],
    ['select-conference','\r'], ['areas','C\r'], ['select-area','\r'], ['new-post','P\r']]) await step(name, data);
  assert.equal(menu(), 'messageBaseNewPost');
  await step('to', '\r'); await step('subject', 'UNSAVED RESIZE PROBE\r');
  await step('seed', Array.from({ length: 30 }, (_, i) => `L${String(i + 1).padStart(2,'0')}:ABCD\r`).join(''), 1500);
  await resize('resize-25', 25);
  await step('after-grow-marker', 'G');
  await step('after-grow-pageup', '\x1b[5~');
  await step('after-grow-pagedown', '\x1b[6~');
  await resize('resize-24', 24);
  await step('after-shrink-marker', 'S');
  await step('after-shrink-pageup', '\x1b[5~');
  await step('after-shrink-pagedown', '\x1b[6~');
  await step('editor-menu', '\x1b');
  // Existing reference's Discard choice: one right arrow from Save.
  await step('discard-select', '\x1b[C'); await step('discard', '\r');
  assert.equal(menu(), 'messageBaseMainMenu');
  const own = rows().filter(r => r.sessionId === session);
  assert(!own.some(r => /posted message to/i.test(r.msg || '')));
  fs.writeFileSync(path.join(output, 'node-result.json'), JSON.stringify({ passed: true, mode, session, steps,
    sizes: own.filter(r => r.source === 'NAWS' && r.msg === 'Telnet: Windows size updated')
      .map(r => [r.width, r.height]) }, null, 2) + '\n');
}
main().catch(e => { process.stderr.write(e.stack + '\n'); process.exitCode = 1; }).finally(() => {
  clearTimeout(watchdog); socket.destroy();
  for (const [name, chunks] of [['display',display], ['server-wire',wireIn], ['client-wire',wireOut]])
    fs.writeFileSync(path.join(output, name + '.bin'), Buffer.concat(chunks));
});
