#!/usr/bin/env python3
"""Stage a bounded UART input observer in a stopped private v86 fixture."""
import argparse
import json
from pathlib import Path

from enigma_key_stream_fixture import ROOT, owned, pid, sha


def stage(candidate):
    candidate = owned(candidate)
    assert not pid(candidate)
    path = candidate / 'core/v86_door/v86_worker.js'
    marker = candidate / 'v86-input-trace.json'
    assert not marker.exists()
    meta_path = candidate / 'v86-door-instance.json'
    meta = json.loads(meta_path.read_text())
    name = str(path.relative_to(candidate))
    before = sha(path)
    assert before == meta['fixture_inputs'][name]
    expected = meta.get('input_bridge', {}).get('staged_worker_sha256', meta['source_inputs'][name])
    assert before == expected
    trace = candidate / 'v86-input-trace.jsonl'
    assert not trace.exists()
    patch = r'''
// Private diagnostic observer: no injected keys, queue edits or IRQ changes.
let traceRows = [], traceCount = 0;
function traceInput(event, value) {
    if (++traceCount > 5000) return;
    const uart = emulator.v86.cpu.devices.uart0;
    traceRows.push({event, value, ms: Date.now()-t0,
        ic: emulator.get_instruction_counter(), queue: uart.input.slice(0,64),
        length: uart.input.length, ints: uart.ints, iir: uart.iir,
        ier: uart.ier, lsr: uart.lsr, fifo: uart.fifo_control,
        modem: uart.modem_control});
}
emulator.add_listener('emulator-loaded', () => {
    const uart = emulator.v86.cpu.devices.uart0;
    const receive = uart.data_received;
    uart.data_received = function(byte) {
        traceInput('receive-before', byte);
        const result = receive.call(this, byte);
        traceInput('receive-after', byte);
        return result;
    };
    const shift = uart.input.shift;
    uart.input.shift = function() {
        const byte = shift.call(this);
        traceInput('guest-read', byte);
        return byte;
    };
    traceInput('ready', null);
});
const traceTimer = setInterval(() => {
    if (traceRows.length) {
        require('fs').appendFileSync(TRACE_PATH, traceRows.map(row=>JSON.stringify(row)+'\n').join(''));
        traceRows = [];
    }
}, 250);
traceTimer.unref();
'''.replace('TRACE_PATH', json.dumps(str(trace)))
    with path.open('a') as stream:
        stream.write(patch)
    record = dict(original_worker_sha256=before, observer_worker_sha256=sha(path),
        stager_sha256=sha(Path(__file__)), trace=str(trace.relative_to(candidate)),
        scope='Instrumented diagnostic only. Observes UART receive/read and registers; no queue or IRQ repair. Timers/observation may affect timing.')
    marker.write_text(json.dumps(record, indent=2) + '\n')
    meta['fixture_inputs'][name] = sha(path)
    meta['input_trace'] = record
    meta_path.write_text(json.dumps(meta, indent=2) + '\n')
    print('Staged bounded UART input observer')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    stage(parser.parse_args().candidate)
