'use strict';
const fs = require('fs');

// Validate the structures consumed by this pinned ifvms restore implementation.
// This does not prove that every variable in a structurally valid save is sane.
function validSave(data, story, stackLimit) {
    if (!Buffer.isBuffer(data) || !Buffer.isBuffer(story) || story.length < 64 ||
        !Number.isSafeInteger(stackLimit) || stackLimit < 8 || data.length < 12 ||
        data.length > 128 * 1024 || data.toString('latin1', 0, 4) !== 'FORM' ||
        data.readUInt32BE(4) + 8 !== data.length || data.toString('latin1', 8, 12) !== 'IFZS') return false;
    const chunks = new Map();
    let at = 12;
    while (at < data.length) {
        if (data.length - at < 8) return false;
        const type = data.toString('latin1', at, at + 4), size = data.readUInt32BE(at + 4);
        const end = at + 8 + size, padded = end + (size & 1);
        if (padded > data.length) return false;
        if (['IFhd', 'CMem', 'UMem', 'Stks'].includes(type)) {
            if (chunks.has(type)) return false;
            chunks.set(type, data.subarray(at + 8, end));
        }
        at = padded;
    }
    const identity = chunks.get('IFhd'), stack = chunks.get('Stks');
    const compressed = chunks.has('CMem'), memory = chunks.get(compressed ? 'CMem' : 'UMem');
    if (!identity || identity.length !== 13 || !stack || stack.length < 8 || stack.length > stackLimit ||
        !memory || compressed === chunks.has('UMem') ||
        !identity.subarray(0, 2).equals(story.subarray(2, 4)) ||
        !identity.subarray(2, 8).equals(story.subarray(0x12, 0x18)) ||
        !identity.subarray(8, 10).equals(story.subarray(0x1c, 0x1e)) ||
        identity.readUIntBE(10, 3) >= story.length) return false;
    const dynamic = story.readUInt16BE(0x0e);
    if (!dynamic || dynamic > story.length) return false;
    if (!compressed && memory.length !== dynamic) return false;
    if (compressed) {
        let decoded = 0;
        for (let index = 0; index < memory.length; ++index) {
            if (memory[index] === 0) {
                if (++index === memory.length) return false;
                decoded += 1 + memory[index];
            } else ++decoded;
            if (decoded > dynamic) return false;
        }
    }
    for (let index = 0; index < stack.length;) {
        if (stack.length - index < 8 || stack[index + 3] & 0xe0 ||
            stack.readUIntBE(index, 3) >= story.length) return false;
        const extent = 8 + (stack[index + 3] & 15) * 2 + stack.readUInt16BE(index + 6) * 2;
        index += extent;
        if (index > stack.length) return false;
    }
    return true;
}

class SnapshotRead {
    #data;
    #position = 0;
    constructor(data) { this.#data = Buffer.from(data); this.BufferClass = Buffer; }
    fread(target, length = target.length) {
        if (!this.#data) return 0;
        if (!Number.isSafeInteger(length) || length < 0 || length > target.length) throw new RangeError('Invalid read extent');
        const count = Math.max(0, Math.min(length, this.#data.length - this.#position));
        if (count) this.#data.copy(target, 0, this.#position, this.#position + count);
        this.#position += count;
        return count;
    }
    ftell() { return this.#position; }
    fseek(offset, mode) {
        if (!Number.isSafeInteger(offset)) throw new RangeError('Invalid seek');
        const position = Math.max(0, offset + (mode === 1 ? this.#position : mode === 2 ? this.#data.length : 0));
        if (!Number.isSafeInteger(position)) throw new RangeError('Invalid seek extent');
        this.#position = position;
    }
    fflush() {}
    fclose() { this.#data = null; }
}

function openSave(filename, story, stackLimit) {
    const fd = fs.openSync(filename, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    let data;
    try {
        const before = fs.fstatSync(fd);
        if (!before.isFile() || before.size > 128 * 1024) throw new Error('Invalid save file');
        data = Buffer.alloc(before.size);
        let offset = 0;
        while (offset < data.length) {
            const count = fs.readSync(fd, data, offset, data.length - offset, offset);
            if (!count) throw new Error('Incomplete save file');
            offset += count;
        }
        const after = fs.fstatSync(fd);
        if (before.size !== after.size || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs) throw new Error('Save file changed');
    } finally { fs.closeSync(fd); }
    if (!validSave(data, story, stackLimit)) throw new Error('Invalid save file');
    return new SnapshotRead(data);
}

module.exports = { validSave, openSave, SnapshotRead };
