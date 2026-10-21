'use strict';
const assert = require('assert/strict'), net = require('net'), fs = require('fs'), path = require('path');
const {SerialIoEvidence} = require('./serial_io_evidence');
const out = path.resolve(process.argv[2]); fs.mkdirSync(out, {recursive: false});
const checks = {};
function unit() {
  let phase = 'online', callbacks = [], writes = [], errors = [];
  const io = new SerialIoEvidence({phase: () => phase, error: e => errors.push(e.code), now: () => 1});
  const s = {destroyed: false, write(data, callback) {writes.push(Buffer.from(data)); callbacks.push(callback); return false;}};
  const bytes = Buffer.from([0, 13, 27, 255]); assert.equal(io.write(s, bytes), false);
  assert.deepEqual(writes, [bytes]); assert.equal(io.snapshot().pendingBytes, 4);
  bytes[0] = 5; assert.equal(io.records[0].buffer[0], 0); callbacks.shift()(null);
  assert.equal(io.snapshot().completedBytes, 4); checks.one_verbatim_write_return_and_snapshot_owned = true;
  phase = 'teardown'; io.write(s, Buffer.from('E')); callbacks.shift()(Object.assign(new Error('failure'), {code: 'EPIPE'}));
  assert.deepEqual(errors, ['EPIPE']); assert.equal(io.snapshot().failedCallbackBytes, 1);
  s.destroyed = true; io.write(s, Buffer.from('X')); io.write(null, Buffer.from('Y'));
  assert.equal(writes.length, 2); assert.equal(io.snapshot().skippedBytes, 2);
  assert.equal(io.snapshot().pendingBytes, 0); checks.failures_and_skipped_closed_writes_distinct = true;
  const throwing = {destroyed: false, write() {throw Object.assign(new Error('sync'), {code: 'SYNC'});}};
  assert.throws(() => io.write(throwing, Buffer.from('S')), /sync/);
  assert.equal(io.snapshot().failedCallbackBytes, 2); checks.synchronous_failure_observed_and_rethrown = true;
  io.save(out);
  assert.deepEqual(fs.readFileSync(path.join(out, 'serial-submitted.bin')), Buffer.from([0, 13, 27, 255, 69, 83]));
  assert.deepEqual(fs.readFileSync(path.join(out, 'serial-completed.bin')), Buffer.from([0, 13, 27, 255]));
  assert.deepEqual(fs.readFileSync(path.join(out, 'serial-skipped.bin')), Buffer.from('XY'));
  const records = fs.readFileSync(path.join(out, 'serial-write-events.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
  assert.deepEqual(records.map(r => r.offset), [0, 4, 5, 6, 7]);
  assert.equal(records[1].phase, 'teardown'); checks.artifacts_preserve_offsets_and_ownership = true;
}
async function reset() {
  let peer, error, closeHadError, ended = false; const events = [];
  const io = new SerialIoEvidence({phase: () => 'online', error: e => events.push({type: 'write-error', code: e.code})});
  const server = net.createServer(s => {
    peer = s; s.on('error', e => {error = e; events.push({type: 'frontend-error', code: e.code});});
    s.on('end', () => {ended = true;}); s.on('close', hadError => {closeHadError = hadError;});
    io.write(s, Buffer.from('LOCAL-RESET-PROBE'));
  });
  let client;
  try {
    await new Promise(r => server.listen(0, '127.0.0.1', r));
    client = net.connect(server.address().port, '127.0.0.1');
    client.on('data', () => client.resetAndDestroy()); client.on('error', () => {});
    const deadline = Date.now()+3000;
    while (closeHadError === undefined) {assert(Date.now()<deadline, 'Owned reset observation deadline'); await new Promise(r => setTimeout(r, 2));}
    assert.equal(error.code, 'ECONNRESET'); assert.equal(closeHadError, true); assert.equal(ended, false);
    checks.real_TCP_reset_has_error_close_without_FIN = true;
    io.write(peer, Buffer.from('AFTER-CLOSE')); assert.equal(io.snapshot().skippedBytes, 11);
    checks.real_closed_peer_is_not_written = true;
    return {events, closeHadError, ended, io: io.snapshot()};
  } finally {client?.destroy(); peer?.destroy(); await new Promise(r => server.close(r));}
}
(async () => {unit(); const observed = await reset(); const result = {passed: true, checks, observed,
  scope: 'Observer ownership/byte tests plus an explicit real loopback TCP RST. No inference that historical DOS/audio resets had the same source; no error suppression or peer-consumption claim.'};
  fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2)+'\n'); console.log(JSON.stringify(result, null, 2));
})().catch(e => {console.error(e.stack); process.exitCode = 1;});
