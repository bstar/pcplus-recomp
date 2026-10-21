'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
// Optional serial-to-Telnet keyboard framing. Never edits or invents bytes.
// A TCP receiver must still parse streams: write boundaries are not a guarantee.
class InputSequenceFramer {
  constructor(deliver, {timeout = 250, limit = 128, schedule = setTimeout, cancel = clearTimeout} = {}) {
    if (typeof deliver !== 'function' || !Number.isInteger(timeout) || timeout < 1 || timeout > 2000 ||
        !Number.isInteger(limit) || limit < 4 || limit > 1024) throw new RangeError('Invalid input framing bounds');
    Object.assign(this, {deliver, timeout, limit, schedule, cancel});
    this.pending = []; this.timer = null; this.closed = false;
  }

  flush() {
    if (this.timer !== null) this.cancel(this.timer);
    this.timer = null;
    const data = Buffer.from(this.pending); this.pending = [];
    if (!this.closed && data.length) this.deliver(data);
  }

  close() {
    // This connection is gone; pending bytes must never enter a later session.
    this.closed = true;
    this.flush();
  }

  complete() {
    const p = this.pending;
    if (p.length === 1) return false;
    if (p[1] !== 0x5b && p[1] !== 0x4f) return true; // ordinary ESC-prefixed key
    if (p.length === 2) return false;
    if (p[1] === 0x5b && p[2] === 0x5b) return p.length >= 4; // Linux F1..F5
    if (p[1] === 0x5b && p[2] === 0x4d) return p.length >= 6; // X10 mouse
    const last = p[p.length - 1];
    return last < 0x20 || last >= 0x40; // final or invalid; preserve either
  }

  feed(data) {
    if (this.closed) return;
    for (let at = 0; at < data.length && !this.closed;) {
      if (!this.pending.length) {
        const end = data.indexOf(0x1b, at);
        if (end !== at) {
          const stop = end < 0 ? data.length : end;
          this.deliver(Buffer.from(data.subarray(at, stop))); at = stop;
          continue;
        }
        this.pending.push(data[at++]);
        // Absolute first-byte deadline: slow trickles cannot retain indefinitely.
        this.timer = this.schedule(() => { this.timer = null; this.flush(); }, this.timeout);
        this.timer?.unref?.();
      } else if (data[at] === 0x1b) {
        this.flush(); // restart without swallowing consecutive Escape keys
      } else {
        this.pending.push(data[at++]);
        if (this.pending.length >= this.limit || this.complete()) this.flush();
      }
    }
  }
}

module.exports = {InputSequenceFramer};
