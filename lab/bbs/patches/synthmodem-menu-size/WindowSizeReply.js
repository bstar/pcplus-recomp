'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
// One owned pre-TCP terminal query. Never feed proxied BBS/transfer data here.
class WindowSizeReply {
  constructor(limit = 1024) {
    if (!Number.isInteger(limit) || limit < 1 || limit > 4096) throw new RangeError('Invalid input bound');
    this.limit = limit;
    this.pending = [];
    this.input = [];
    this.dimensions = null;
  }

  append(bytes) {
    if (this.input.length + bytes.length > this.limit) throw new RangeError('Pending input limit exceeded');
    this.input.push(...bytes);
  }

  feed(data) {
    for (const byte of data) {
      if (this.dimensions) { this.append([byte]); continue; }
      if (!this.pending.length && byte !== 27) { this.append([byte]); continue; }
      this.pending.push(byte);
      const text = Buffer.from(this.pending).toString('latin1');
      const reply = /^\x1b\[8;([0-9]{1,5});([0-9]{1,5})t$/.exec(text);
      if (reply) {
        const rows = Number(reply[1]), cols = Number(reply[2]);
        if (rows < 1 || rows > 65535 || cols < 1 || cols > 65535) throw new RangeError('Invalid terminal dimensions');
        this.dimensions = { cols, rows };
        this.pending = [];
      } else if (byte !== 116 && /^\x1b(?:\[(?:8(?:;[0-9]{0,5}(?:;[0-9]{0,5})?)?)?)?$/.test(text)) {
        // At most17 bytes, regardless of receive chunking.
      } else {
        if (text.startsWith('\x1b[8;')) throw new RangeError('Malformed terminal dimensions');
        const restart = byte === 27;
        this.append(restart ? this.pending.slice(0, -1) : this.pending);
        this.pending = restart ? [27] : [];
      }
    }
    return this.dimensions;
  }

  takeInput() {
    if (!this.dimensions || this.pending.length) throw new Error('Terminal query incomplete');
    const input = Buffer.from(this.input);
    this.input = [];
    return input;
  }
}
module.exports = { WindowSizeReply };
