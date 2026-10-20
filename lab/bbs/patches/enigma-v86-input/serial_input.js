'use strict';

// v86 accepts a string instantaneously, even with the guest UART FIFO disabled.
// Keep wire bytes outside that UART until its previous character is consumed.
// ready() must inspect the pinned UART receive queue; send() injects ONE byte.
function createSerialInput({ready, send, onError, capacity = 65536,
    schedule = fn => setTimeout(fn, 1), cancel = clearTimeout}) {
    if (!Number.isSafeInteger(capacity) || capacity < 1 || capacity > 65536) {
        throw new RangeError('Invalid serial input capacity');
    }
    const bytes = new Uint8Array(capacity);
    let head = 0, tail = 0, pending = 0, timer = null, closed = false;
    function close() {
        closed = true;
        pending = 0;
        if (timer !== null) cancel(timer);
        timer = null;
    }
    function arm() {
        if (!closed && pending && timer === null) timer = schedule(pump);
    }
    function pump() {
        timer = null;
        if (closed) return;
        try {
            if (pending && ready()) {
                const byte = bytes[head];
                head = (head + 1) % capacity;
                --pending;
                send(byte);
            }
            arm();
        } catch (error) {
            close();
            onError(error);
        }
    }
    return {
        enqueue(data) {
            if (closed) return false;
            if (!(data instanceof Uint8Array)) throw new TypeError('Serial input must be bytes');
            // Reject the whole chunk; never retain a silently truncated command.
            if (data.length > capacity - pending) throw new RangeError('DOS door serial input queue is full');
            for (const byte of data) {
                bytes[tail] = byte;
                tail = (tail + 1) % capacity;
            }
            pending += data.length;
            arm();
            return true;
        },
        close,
        get pending() { return pending; },
    };
}

module.exports = {createSerialInput};
