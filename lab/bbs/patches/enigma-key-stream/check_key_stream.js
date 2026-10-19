'use strict';
const assert = require('assert/strict');
const { KeyStream } = require('./key_stream.js');
let checks = 0;
function fixture() {
    let now = 0,
        next = 0,
        raw = null;
    const timers = new Map(),
        out = [],
        binary = [];
    const stream = new KeyStream(b => out.push(Buffer.from(b)), {
        raw: () => raw,
        schedule: fn => {
            const id = ++next;
            timers.set(id, { at: now + 100, fn });
            return id;
        },
        cancel: id => timers.delete(id),
    });
    return {
        stream,
        out,
        binary,
        raw: () => {
            raw = b => binary.push(Buffer.from(b));
            stream.reset();
        },
        tick: n => {
            now = n;
            for (const [id, t] of [...timers])
                if (t.at <= now) {
                    timers.delete(id);
                    t.fn();
                }
        },
        timers,
    };
}
const sequences = [
    '\x1b[A',
    '\x1b[B',
    '\x1b[C',
    '\x1b[D',
    '\x1b[H',
    '\x1b[2~',
    '\x1b[1;5A',
    '\x1bOA',
    '\x1bOP',
    '\x1b[[A',
    '\x1b[25;80R',
    '\x1b[?63;1;2c',
    '\x1b[=6;1n',
    '\x1b[M !!',
    '\x1b[<0;12;3M',
    '\x1b\x1b[A',
    'é',
    '€',
    '😀',
    '\x1bé',
    '\x1b€',
    '\x1b😀',
];
for (const value of sequences) {
    const bytes = Buffer.from(value);
    for (let mask = 0; mask < 1 << (bytes.length - 1); ++mask) {
        const f = fixture();
        let start = 0;
        for (let i = 0; i < bytes.length - 1; ++i)
            if (mask & (1 << i)) {
                f.stream.write(bytes.subarray(start, i + 1));
                start = i + 1;
            }
        f.stream.write(bytes.subarray(start));
        assert.deepEqual(f.out, [bytes], value + ' ' + mask);
        assert.equal(f.timers.size, 0);
        ++checks;
    }
}
for (let split = 0; split <= 256; ++split) {
    const f = fixture(),
        data = Buffer.from(Array.from({ length: 256 }, (_, i) => i));
    f.stream.write(data.subarray(0, split));
    f.stream.write(data.subarray(split));
    f.tick(100);
    assert.deepEqual(Buffer.concat(f.out), data);
    ++checks;
}
{
    const f = fixture();
    f.stream.write(Buffer.from('\x1b'));
    f.tick(99);
    assert.equal(f.out.length, 0);
    f.tick(100);
    assert.deepEqual(f.out, [Buffer.from('\x1b')]);
    ++checks;
}
{
    const f = fixture();
    f.stream.write(Buffer.from('\x1b['));
    for (let i = 1; i < 10; ++i) {
        f.tick(i * 10);
        f.stream.write(Buffer.from('1'));
    }
    f.tick(100);
    assert.equal(f.timers.size, 0);
    assert.equal(Buffer.concat(f.out).toString(), '\x1b[' + '1'.repeat(9));
    ++checks;
}
{
    const f = fixture();
    f.stream.write(Buffer.from('\x1b[' + '1'.repeat(500)));
    assert.ok(f.stream.pending.length < 128);
    f.tick(100);
    assert.equal(Buffer.concat(f.out).length, 502);
    ++checks;
}
{
    const f = fixture();
    f.stream.write(Buffer.from('\x1b['));
    f.raw();
    f.tick(100);
    const payload = Buffer.from(Array.from({ length: 256 }, (_, i) => i));
    f.stream.write(payload);
    assert.equal(f.out.length, 0);
    assert.deepEqual(Buffer.concat(f.binary), payload);
    ++checks;
}
{
    const f = fixture();
    f.stream.deliver = b => {
        f.out.push(b);
        if (b[0] === 13) f.raw();
    };
    const payload = Buffer.from(Array.from({ length: 256 }, (_, i) => i));
    f.stream.write(Buffer.concat([Buffer.from('\r'), payload]));
    assert.deepEqual(f.out, [Buffer.from('\r')]);
    assert.deepEqual(Buffer.concat(f.binary), payload);
    ++checks;
}
{
    const f = fixture();
    f.stream.write(Buffer.from('\x1b'));
    f.stream.close();
    f.tick(100);
    f.stream.write(Buffer.from('A'));
    assert.equal(f.out.length, 0);
    assert.equal(f.timers.size, 0);
    ++checks;
}
{
    const f = fixture();
    f.stream.deliver = b => {
        f.out.push(b);
        f.stream.close();
    };
    f.stream.write(Buffer.from('ABC'));
    assert.deepEqual(f.out, [Buffer.from('A')]);
    assert.equal(f.timers.size, 0);
    ++checks;
}
console.log(
    JSON.stringify({
        passed: true,
        checks,
        scope: 'Deterministic key-framing oracle: all partitions, UTF8, byte conservation, bounded first-byte deadlines, raw takeover and close. Not a stock-server or DOS-client fix.',
    }),
);
