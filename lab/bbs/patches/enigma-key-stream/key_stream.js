'use strict';

// Frame keyboard escape sequences before the existing key decoder. This is
// not a Telnet parser or a transfer-byte decoder. Raw owners bypass it.
class KeyStream {
    constructor(
        deliver,
        {
            timeout = 100,
            limit = 128,
            raw = () => null,
            schedule = setTimeout,
            cancel = clearTimeout,
            ignored = () => false,
        } = {},
    ) {
        if (
            !Number.isInteger(timeout) ||
            timeout < 1 ||
            timeout > 1000 ||
            !Number.isInteger(limit) ||
            limit < 6 ||
            limit > 1024
        ) {
            throw new RangeError('Invalid keyboard framing bounds');
        }
        this.deliver = deliver;
        this.ignored = ignored;
        this.raw = raw;
        this.timeout = timeout;
        this.limit = limit;
        this.schedule = schedule;
        this.cancel = cancel;
        this.pending = [];
        this.timer = null;
        this.closed = false;
    }

    reset() {
        if (this.timer !== null) this.cancel(this.timer);
        this.timer = null;
        this.pending = [];
        this.pendingIgnored = false;
    }

    close() {
        this.reset();
        this.closed = true;
    }

    emitPending() {
        const data = Buffer.from(this.pending);
        const ignored = this.pendingIgnored;
        this.reset(); // clear state before a callback changes input owners
        this.deliver(data, ignored);
    }

    start(byte, kind = 'escape') {
        this.kind = kind;
        this.pendingIgnored = !!this.ignored();
        this.pending = [byte];
        // Absolute first-byte deadline; a trickle must not extend it forever.
        this.timer = this.schedule(() => {
            this.timer = null;
            if (!this.closed && this.pending.length) this.emitPending();
        }, this.timeout);
        if (this.timer && this.timer.unref) this.timer.unref();
    }

    // Incomplete, complete, or invalid. Invalid bytes are preserved for the
    // legacy decoder, rather than synthesized as a different keyboard key.
    status() {
        let i = 0;
        while (i < this.pending.length && this.pending[i] === 0x1b) ++i;
        if (i === this.pending.length) return 'incomplete';
        const lead = this.pending[i++];
        // Preserve the existing decoder's ESC-prefixed Unicode semantics too.
        // A non-ASCII code point must reach it as one UTF-8 sequence.
        if (lead >= 0xc2 && lead <= 0xf4) {
            const length = lead < 0xe0 ? 2 : lead < 0xf0 ? 3 : 4;
            for (let j = i; j < this.pending.length; ++j) {
                if ((this.pending[j] & 0xc0) !== 0x80) return 'invalid';
            }
            return this.pending.length < i + length - 1
                ? 'incomplete'
                : 'complete';
        }
        if (lead !== 0x5b && lead !== 0x4f && lead !== 0x4e) return 'complete';
        if (i === this.pending.length) return 'incomplete';
        // Linux console F1..F5, ESC [[A..E.
        if (lead === 0x5b && this.pending[i] === 0x5b) {
            return i + 1 === this.pending.length ? 'incomplete' : 'complete';
        }
        // X10 mouse: CSI M followed by exactly three raw coordinate bytes.
        if (lead === 0x5b && this.pending[i] === 0x4d) {
            return this.pending.length < i + 4 ? 'incomplete' : 'complete';
        }
        for (; i < this.pending.length; ++i) {
            const byte = this.pending[i];
            if (byte >= 0x40 && byte <= 0x7e) return 'complete';
            if (byte < 0x20 || byte > 0x3f) return 'invalid';
        }
        return 'incomplete';
    }

    write(data) {
        if (this.closed) return;
        if (!Buffer.isBuffer(data)) data = Buffer.from(data);
        let offset = 0;
        while (!this.closed && offset < data.length) {
            // A key callback may switch to a binary handler in the middle of
            // this same TCP chunk. Forward the untouched suffix to that owner.
            const direct = this.raw();
            if (direct) {
                this.reset();
                direct(data.subarray(offset));
                return;
            }
            if (!this.pending.length) {
                const byte = data[offset++];
                if (byte === 0x1b) {
                    this.start(byte);
                } else if (byte >= 0xc2 && byte <= 0xf4) {
                    this.start(byte, 'utf8');
                    this.utf8Length = byte < 0xe0 ? 2 : byte < 0xf0 ? 3 : 4;
                } else {
                    // One key at a time: Enter may activate a raw transfer
                    // owner before the rest of this same chunk is processed.
                    this.deliver(Buffer.from([byte]), !!this.ignored());
                }
            } else if (this.kind === 'utf8') {
                if ((data[offset] & 0xc0) !== 0x80) {
                    this.emitPending();
                    continue;
                }
                this.pendingIgnored ||= !!this.ignored();
                this.pending.push(data[offset++]);
                if (this.pending.length === this.utf8Length) this.emitPending();
            } else {
                // Do not swallow a fresh escape into a malformed sequence.
                if (
                    data[offset] === 0x1b &&
                    this.pending.some(v => v !== 0x1b)
                ) {
                    this.emitPending();
                    continue;
                }
                this.pendingIgnored ||= !!this.ignored();
                this.pending.push(data[offset++]);
                if (
                    this.pending.length >= this.limit ||
                    this.status() !== 'incomplete'
                ) {
                    this.emitPending();
                }
            }
        }
    }
}

module.exports = { KeyStream };
