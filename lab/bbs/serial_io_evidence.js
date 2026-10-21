'use strict';
// Observes frontend write ownership; callback success means local submission,
// never proof that a DOS UART or application consumed the bytes.
const fs = require('fs'), path = require('path');
class SerialIoEvidence {
  constructor({phase, error, now = () => process.uptime()}) {
    Object.assign(this, {phase, error, now}); this.records = []; this.offset = 0;
  }
  write(socket, data) {
    const r = {offset: this.offset, length: data.length, phase: this.phase(), attemptedAt: this.now(),
      buffer: Buffer.from(data), submittedAt: null, completedAt: null, error: null};
    this.offset += r.length; this.records.push(r);
    if (!socket || socket.destroyed) {r.skipped = socket ? 'destroyed' : 'no-socket'; return;}
    r.submittedAt = this.now();
    try {
      return socket.write(data, e => {
        r.completedAt = this.now();
        if (e) {r.error = {message: e.message, code: e.code ?? null}; this.error(e, r);}
      });
    } catch (e) {
      r.completedAt = this.now(); r.error = {message: e.message, code: e.code ?? null};
      this.error(e, r); throw e;
    }
  }
  snapshot() {
    const sum = predicate => this.records.reduce((n, r) => n + (predicate(r) ? r.length : 0), 0);
    return {attemptedBytes: this.offset, submittedBytes: sum(r => r.submittedAt !== null),
      completedBytes: sum(r => r.submittedAt !== null && r.completedAt !== null && !r.error),
      failedCallbackBytes: sum(r => !!r.error), skippedBytes: sum(r => !!r.skipped),
      pendingBytes: sum(r => r.submittedAt !== null && r.completedAt === null),
      writeCalls: this.records.filter(r => r.submittedAt !== null).length,
      scope: 'Frontend write attempts, actual write calls and local callbacks only; no peer-read/UART-drain acknowledgment.'};
  }
  save(out) {
    const select = predicate => Buffer.concat(this.records.filter(predicate).map(r => r.buffer));
    fs.writeFileSync(path.join(out, 'serial-submitted.bin'), select(r => r.submittedAt !== null));
    fs.writeFileSync(path.join(out, 'serial-completed.bin'), select(r => r.submittedAt !== null && r.completedAt !== null && !r.error));
    fs.writeFileSync(path.join(out, 'serial-skipped.bin'), select(r => !!r.skipped));
    fs.writeFileSync(path.join(out, 'serial-write-events.jsonl'), this.records.map(({buffer, ...r}) => JSON.stringify(r)+'\n').join(''));
  }
}
module.exports = {SerialIoEvidence};
