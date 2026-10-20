'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
const { EventEmitter } = require('events');
const wire = require('../../vm/qemu-runner/wire');

class ControlWriter extends EventEmitter {
  constructor(socket) {
    super();
    this.socket = socket;
    this.buffer = Buffer.alloc(262144);
    this.head = 0;
    this.length = 0;
    this.blocked = false;
    this.closed = false;
    this.onDrain = () => {
      if (this.closed) return;
      this.blocked = false;
      try {
        if (this.flush()) this.emit('drain');
      } catch (error) { this.destroy(); this.emit('error', error); }
    };
    this.onClose = () => this.destroy();
    socket.on('drain', this.onDrain);
    socket.on('close', this.onClose);
  }

  write(data) {
    if (this.closed || this.socket.destroyed) throw new Error('Modem control channel closed');
    // Retain wire.encode's accepted input types and byte representation.
    if (data == null) data = Buffer.alloc(0);
    else if (typeof data === 'string') data = Buffer.from(data, 'utf8');
    else if (data instanceof Uint8Array && !Buffer.isBuffer(data)) {
      data = Buffer.from(data.buffer, data.byteOffset, data.byteLength);
    }
    if (!Buffer.isBuffer(data)) throw new TypeError('Unsupported modem payload type');
    if (data.length + this.length + (this.socket.writableLength || 0) > this.buffer.length) {
      throw new RangeError('Modem control queue capacity exceeded');
    }
    const tail = (this.head + this.length) % this.buffer.length;
    const first = Math.min(data.length, this.buffer.length - tail);
    data.copy(this.buffer, tail, 0, first);
    data.copy(this.buffer, 0, first);
    this.length += data.length;
    return this.flush();
  }

  flush() {
    while (this.length && !this.blocked && !this.closed) {
      const count = Math.min(this.length, wire.WIRE_MAX_PAYLOAD, this.buffer.length - this.head);
      const frame = wire.encode(wire.TYPE.DATA_TX, this.buffer.subarray(this.head, this.head + count));
      // false means accepted by Node, then wait for drain. Never resend it.
      const ready = this.socket.write(frame);
      if (this.closed) return false;
      this.head = (this.head + count) % this.buffer.length;
      this.length -= count;
      if (ready === false) this.blocked = true;
    }
    return !this.closed && !this.blocked && this.length === 0;
  }

  destroy() {
    if (this.closed) return;
    this.closed = true;
    this.socket.off('drain', this.onDrain);
    this.socket.off('close', this.onClose);
    this.head = this.length = 0;
  }
}

module.exports = { ControlWriter };
