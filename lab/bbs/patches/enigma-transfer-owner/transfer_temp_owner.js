'use strict';

// Authority comes from create(), never from a caller-supplied directory string.
const fs = require('fs');
const os = require('os');
const path = require('path');
const secret = Symbol('transfer temporary owner');
const genuine = new WeakSet();
const active = new Set();

class TransferTempOwner {
    #directory;
    #kind;
    #state = 'active';
    #waiters = [];

    constructor(directory, kind, key) {
        if (key !== secret) throw new TypeError('Use TransferTempOwner.createUpload/createList');
        this.#directory = directory;
        this.#kind = kind;
        genuine.add(this);
        active.add(this);
        Object.freeze(this);
    }

    static owns(value, kind) { return genuine.has(value) && (!kind || value.#kind === kind); }
    get kind() { return this.#kind; }
    get path() { return this.#directory; }
    get state() { return this.#state; }

    static createUpload(cb) { TransferTempOwner.retryFailed(); TransferTempOwner.#create('upload', cb); }
    static createList(cb) { TransferTempOwner.retryFailed(); TransferTempOwner.#create('list', cb); }

    static #create(kind, cb) {
        let settled = false;
        const finish = (err, directory) => {
            if (settled) return;
            settled = true;
            const owner = err ? undefined : new TransferTempOwner(directory, kind, secret);
            queueMicrotask(() => cb(err || null, owner));
        };
        try {
            fs.mkdtemp(path.join(os.tmpdir(), kind === 'upload' ? 'enigul-' : 'enigtf-'), finish);
        } catch (err) {
            finish(err);
        }
    }

    cleanup(cb = () => {}) {
        if (this.#state === 'closed') {
            queueMicrotask(() => cb(null));
            return;
        }
        this.#waiters.push(cb);
        if (this.#state === 'removing') return;
        this.#state = 'removing';
        let settled = false;
        const finish = err => {
            if (settled) return;
            settled = true;
            this.#state = err ? 'failed' : 'closed';
            if (!err) active.delete(this);
            const pending = this.#waiters;
            this.#waiters = [];
            for (const done of pending) queueMicrotask(() => done(err || null));
        };
        try {
            fs.rm(this.#directory, { recursive: true, force: true }, finish);
        } catch (err) {
            finish(err);
        }
    }

    // Retry failed retirement only; an operation still using its directory is safe.
    static retryFailed(cb = () => {}) {
        const failed = [...active].filter(owner => owner.#state === 'failed');
        const results = [];
        let remaining = failed.length;
        let firstError = null;
        if (!remaining) {
            queueMicrotask(() => cb(null, results));
            return;
        }
        for (const owner of failed) owner.cleanup(err => {
            if (err && !firstError) firstError = err;
            results.push({ path: owner.path, error: err });
            if (!--remaining) cb(firstError, results);
        });
    }
}

process.prependOnceListener('exit', () => {
    for (const owner of active) {
        try {
            fs.rmSync(owner.path, { recursive: true, force: true });
            active.delete(owner);
        } catch (err) {
            // One failed removal must not prevent the other owners' retirement.
            try { process.stderr.write(`Transfer temporary cleanup failed at exit: ${err.code || 'unknown'}\n`); } catch (_) {}
        }
    }
});

module.exports = TransferTempOwner;
