'use strict';
const fs = require('fs');
const path = require('path');
const {randomUUID} = require('crypto');

function atomicImageWrite(imagePath, data, io = fs) {
    const target = io.realpathSync(imagePath);
    const mode = io.statSync(target).mode & 0o777;
    const temporary = target + '.pending-' + process.pid + '-' + randomUUID();
    let fd = null, created = false, committed = false;
    try {
        fd = io.openSync(temporary, 'wx', mode);
        created = true;
        io.fchmodSync(fd, mode);
        io.writeFileSync(fd, data);
        io.fsyncSync(fd);
        io.closeSync(fd);
        fd = null;
        io.renameSync(temporary, target);
        committed = true;
        const directory = io.openSync(path.dirname(target), 'r');
        try { io.fsyncSync(directory); } finally { io.closeSync(directory); }
    } catch (error) {
        error.imageCommitted = committed;
        if (fd !== null) { try { io.closeSync(fd); } catch (_) {} }
        if (created && !committed) {
            try { io.unlinkSync(temporary); } catch (cleanup) {
                if (cleanup.code !== 'ENOENT') {
                    error.temporaryPath = temporary;
                    error.message += '; cannot remove temporary image ' + temporary + ': ' + cleanup.message;
                }
            }
        }
        throw error;
    }
}

function flushImage(entry, imagePath) {
    if (!entry) return Promise.resolve();
    // The caller observes the failed attempt; a later attempt can still retry.
    entry.flushQueue = entry.flushQueue.catch(() => {}).then(() => {
        const snapshot = Buffer.from(new Uint8Array(entry.sab));
        atomicImageWrite(imagePath, snapshot);
    });
    return entry.flushQueue;
}

module.exports = {atomicImageWrite, flushImage};
