'use strict';
const assert = require('node:assert/strict');
const {createSerialInput} = require('./serial_input');
const checks = [];
function check(name, test) { test(); checks.push(name); }
function lab(options = {}) {
    const timers = new Map(), sent = [], errors = [];
    let serialReady = true, next = 0;
    const queue = createSerialInput({
        ready: () => serialReady,
        send: byte => { assert(serialReady); sent.push(byte); serialReady = false; },
        onError: error => errors.push(error.message),
        schedule: fn => { const id = ++next; timers.set(id, fn); return id; },
        cancel: id => timers.delete(id), ...options,
    });
    return {queue, timers, sent, errors,
        consume() { serialReady = true; },
        tick() { const entry = timers.entries().next().value; assert(entry); timers.delete(entry[0]); entry[1](); },
        drain() { while (queue.pending) { this.consume(); this.tick(); } },
    };
}
check('empty-input-does-not-schedule', () => { const l=lab(); l.queue.enqueue(Buffer.alloc(0)); assert.equal(l.timers.size,0); });
check('first-byte-delivered-on-scheduled-turn', () => { const l=lab(); l.queue.enqueue(Buffer.from('ab')); assert.deepEqual(l.sent,[]); l.tick(); assert.deepEqual(l.sent,[97]); });
check('busy-uart-keeps-next-byte-outside-guest', () => { const l=lab(); l.queue.enqueue(Buffer.from('ab')); l.tick(); for(let i=0;i<20;i++)l.tick(); assert.deepEqual(l.sent,[97]); assert.equal(l.queue.pending,1); });
check('guest-consumption-releases-next-byte', () => { const l=lab(); l.queue.enqueue(Buffer.from('ab')); l.tick(); l.consume(); l.tick(); assert.deepEqual(l.sent,[97,98]); assert.equal(l.timers.size,0); });
check('all-256-byte-values-exact', () => { const l=lab(); const b=Buffer.from(Array.from({length:256},(_,i)=>i)); l.queue.enqueue(b); l.drain(); assert.deepEqual(l.sent,[...b]); });
check('input-owned-after-enqueue', () => { const l=lab(); const b=Buffer.from('abc'); l.queue.enqueue(b); b.fill(0); l.drain(); assert.deepEqual(l.sent,[97,98,99]); });
check('chunks-retain-order', () => { const l=lab(); l.queue.enqueue(Buffer.from('ab')); l.tick(); l.queue.enqueue(Buffer.from('cd')); l.drain(); assert.deepEqual(l.sent,[97,98,99,100]); });
check('only-one-outstanding-timer', () => { const l=lab(); for(let i=0;i<20;i++)l.queue.enqueue(Buffer.from([i])); assert.equal(l.timers.size,1); l.drain(); assert.equal(l.timers.size,0); });
check('ring-wrap-preserves-order', () => { const l=lab({capacity:3}); l.queue.enqueue(Buffer.from('abc')); l.tick(); l.queue.enqueue(Buffer.from('d')); l.drain(); assert.deepEqual(l.sent,[97,98,99,100]); });
check('full-chunk-rejected-atomically', () => { const l=lab({capacity:3}); l.queue.enqueue(Buffer.from('ab')); assert.throws(()=>l.queue.enqueue(Buffer.from('cd')),RangeError); l.drain(); assert.deepEqual(l.sent,[97,98]); });
check('maximum-capacity-exact', () => { const l=lab(); const b=Buffer.alloc(65536,255); l.queue.enqueue(b); assert.equal(l.queue.pending,65536); assert.throws(()=>l.queue.enqueue(Buffer.from([0])),RangeError); l.drain(); assert.equal(l.sent.length,65536); assert(l.sent.every(b=>b===255)); });
for(const value of [0,-1,65537,1.5,NaN,Infinity])check('invalid-capacity-'+value,()=>assert.throws(()=>lab({capacity:value}),RangeError));
check('strings-not-coerced-to-bytes', () => { const l=lab(); assert.throws(()=>l.queue.enqueue('abc'),TypeError); assert.equal(l.timers.size,0); });
check('close-cancels-and-drops-pending', () => { const l=lab(); l.queue.enqueue(Buffer.from('ab')); l.tick(); l.queue.close(); assert.equal(l.timers.size,0); assert.equal(l.queue.pending,0); assert.equal(l.queue.enqueue(Buffer.from('c')),false); });
check('close-idempotent', () => { const l=lab(); l.queue.close(); l.queue.close(); assert.equal(l.timers.size,0); });
check('already-running-callback-cannot-send-after-close', () => { const l=lab(); l.queue.enqueue(Buffer.from('x')); const callback=[...l.timers.values()][0]; l.queue.close(); callback(); assert.deepEqual(l.sent,[]); });
check('readiness-fault-closes-once', () => { const l=lab({ready:()=>{throw Error('read failed');}}); l.queue.enqueue(Buffer.from('ab')); l.tick(); assert.deepEqual(l.errors,['read failed']); assert.equal(l.queue.pending,0); assert.equal(l.timers.size,0); });
check('send-fault-closes-once', () => { const l=lab({send:()=>{throw Error('send failed');}}); l.queue.enqueue(Buffer.from('ab')); l.tick(); assert.deepEqual(l.errors,['send failed']); assert.equal(l.queue.pending,0); assert.equal(l.timers.size,0); });
check('enqueue-during-send-retains-order', () => { let q; const l=lab({send:b=>{l.sent.push(b); if(b===1)q.enqueue(Buffer.from([3]));}}); q=l.queue; q.enqueue(Buffer.from([1,2])); l.drain(); assert.deepEqual(l.sent,[1,2,3]); });
check('close-during-send-does-not-rearm', () => { let q; const l=lab({send:()=>q.close()}); q=l.queue; q.enqueue(Buffer.from('ab')); l.tick(); assert.equal(l.timers.size,0); assert.equal(q.pending,0); });
console.log(JSON.stringify({passed:true,checks,count:checks.length}));
