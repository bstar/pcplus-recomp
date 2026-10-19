'use strict';
const assert = require('assert/strict');
const path = require('path');
const { PassThrough } = require('stream');
const root = path.resolve(process.argv[2]);
require(path.join(root, 'test/setup.js'));
require(path.join(root, 'core/config.js')).get().logging = {
    traceUserKeyboardInput: false,
};
const { Client } = require(path.join(root, 'core/client.js'));
const fixed = process.argv.includes('--fixed');
let checks = 0;
const baselineFlag = process.argv.indexOf('--baseline');
const baseline =
    baselineFlag < 0
        ? null
        : JSON.parse(
              require('fs').readFileSync(
                  process.argv[baselineFlag + 1],
                  'utf8',
              ),
          ).stock_baselines;
if (fixed)
    assert.ok(baseline, '--fixed requires --baseline from the stock run');
const stockBaselines = {};
function reference(value, run) {
    const observed = run();
    stockBaselines[value] = JSON.parse(JSON.stringify(observed));
    if (fixed)
        assert.deepEqual(
            stockBaselines[value],
            baseline[value],
            'Unfragmented parity: ' + value,
        );
    return observed;
}
function fixture() {
    const client = new Client(),
        events = [];
    client.setInputOutput(new PassThrough(), new PassThrough());
    client.user.isAuthenticated = () => false;
    client.disconnect = () => {};
    client.dataHandler = b => client.emit('data', b);
    client.on('key press', (ch, key) =>
        events.push({ ch, name: key && key.name, seq: key && key.seq }),
    );
    client.on('cursor position report', v => events.push({ cpr: v }));
    return {
        client,
        events,
        write: b => client.emit('data', Buffer.from(b)),
        close: () => client.end(),
    };
}
function decode(parts) {
    const f = fixture();
    for (const part of parts) f.write(part);
    const events = f.events.slice();
    f.close();
    return events;
}
const vectors = [
    ['\x1b[A', 'up arrow'],
    ['\x1b[B', 'down arrow'],
    ['\x1b[D', 'left arrow'],
    ['\x1b[H', 'home'],
    ['\x1b[2~', 'insert'],
    ['\x1b[4~', 'end'],
    ['\x1b[5~', 'page up'],
    ['\x1bOA', 'up arrow'],
    ['\x1b[1;5A', 'ctrl + up arrow'],
    ['\x1b[[A', 'f1'],
];
let demonstrated = 0;
for (const [text, name] of vectors) {
    const bytes = Buffer.from(text),
        expected = reference(text, () => decode([bytes]));
    assert.equal(expected.length, 1);
    assert.equal(expected[0].name, name);
    for (let mask = 1; mask < 1 << (bytes.length - 1); ++mask) {
        const parts = [];
        let start = 0;
        for (let i = 0; i < bytes.length - 1; ++i)
            if (mask & (1 << i)) {
                parts.push(bytes.subarray(start, i + 1));
                start = i + 1;
            }
        parts.push(bytes.subarray(start));
        const got = decode(parts);
        if (fixed) assert.deepEqual(got, expected, text + ' ' + mask);
        else if (JSON.stringify(got) !== JSON.stringify(expected))
            ++demonstrated;
        ++checks;
    }
}
for (const value of [
    'é',
    '€',
    '😀',
    '\x1bé',
    '\x1b€',
    '\x1b😀',
    '\x1b[25;80R',
]) {
    const bytes = Buffer.from(value),
        expected = reference(value, () => decode([bytes]));
    for (let i = 1; i < bytes.length; ++i) {
        const got = decode([bytes.subarray(0, i), bytes.subarray(i)]);
        if (fixed) assert.deepEqual(got, expected, value + ' ' + i);
        ++checks;
    }
}
if (fixed) {
    const f = fixture(),
        binary = [];
    f.client.on('key press', (_, key) => {
        if (key && key.name === 'return')
            f.client.setTemporaryDirectDataHandler(b =>
                binary.push(Buffer.from(b)),
            );
    });
    const data = Buffer.from(Array.from({ length: 256 }, (_, i) => i));
    f.write(Buffer.concat([Buffer.from('\r'), data]));
    assert.deepEqual(Buffer.concat(binary), data);
    assert.equal(f.events.length, 1);
    f.client.restoreDataHandler();
    f.write(Buffer.from('\x1b[D'));
    assert.equal(f.events.at(-1).name, 'left arrow');
    f.close();
    ++checks;
}
if (fixed) {
    const f = fixture();
    f.client.ignoreInput = true;
    f.write(Buffer.from('\x1b'));
    f.client.ignoreInput = false;
    f.write(Buffer.from('[D'));
    assert.equal(f.events.length, 0);
    f.client.ignoreInput = true;
    f.write(Buffer.from('\x1b[25;80R'));
    assert.deepEqual(f.events, [{ cpr: [25, 80] }]);
    f.close();
    ++checks;
}
// Real Client -> real editor, without a network session or saved message.
const { MultiLineEditTextView } = require(
    path.join(root, 'core/multi_line_edit_text_view.js'),
);
function edit(parts) {
    const f = fixture();
    const view = new MultiLineEditTextView({
        client: f.client,
        dimens: { width: 40, height: 5 },
    });
    view.setText('ABCD', { scrollMode: 'top' });
    view.topVisibleIndex = 0;
    view.cursorPos = { row: 0, col: 4 };
    // Call the real implementation directly so swallowed UI exceptions cannot
    // turn a broken editor setup into a passing no-op test.
    f.client.on('key press', (ch, key) => view._handleKeyPress(ch, key));
    for (const part of parts) f.write(part);
    const result = {
        text: view.buffer.lines.map(l => l.chars),
        cursor: { ...view.cursorPos },
        mode: view.getTextEditMode(),
    };
    f.close();
    return result;
}
let editorFailures = 0;
for (const [wire, text] of [
    ['\x1b[DZ', 'ABCZD'],
    ['\x1b[HZ', 'ZABCD'],
    ['\x1b[H\x1b[2~Z', 'ZBCD'],
]) {
    const bytes = Buffer.from(wire),
        expected = reference(wire, () => edit([bytes]));
    assert.deepEqual(expected.text, [text]);
    for (let split = 1; split < bytes.length; ++split) {
        const got = edit([bytes.subarray(0, split), bytes.subarray(split)]);
        if (fixed) assert.deepEqual(got, expected, wire + ' ' + split);
        else if (JSON.stringify(got) !== JSON.stringify(expected))
            ++editorFailures;
        ++checks;
    }
}
if (!fixed) assert.ok(editorFailures > 0);
async function finish() {
    if (fixed) {
        const f = fixture();
        f.write(Buffer.from('\x1b'));
        assert.equal(f.events.length, 0);
        await new Promise(resolve => setTimeout(resolve, 150));
        assert.equal(f.events[0].name, 'escape');
        f.write(Buffer.from('\x1b'));
        f.close();
        const n = f.events.length;
        await new Promise(resolve => setTimeout(resolve, 150));
        assert.equal(f.events.length, n);
        ++checks;
    } else assert.ok(demonstrated > 0);
    console.log(
        JSON.stringify({
            passed: true,
            stock_baselines: stockBaselines,
            fixed,
            checks,
            demonstrated_fragmentation_failures: demonstrated,
            editor_fragmentation_failures: editorFailures,
            scope: 'Actual pinned ENiGMA Client with synthetic stream/config, key and CPR events, raw takeover, restore and close. No stock-server mutation or DOS-client fix claim.',
        }),
    );
}
finish().catch(e => {
    console.error(e);
    process.exitCode = 1;
});
