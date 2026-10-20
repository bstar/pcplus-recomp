#!/usr/bin/env python3
"""Stage an explicit UART-consumption bridge in a stopped private v86 fixture."""
import argparse
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from enigma_key_stream_fixture import owned, pid, sha


def stage(candidate):
    candidate = owned(candidate)
    assert not pid(candidate)
    meta_path = candidate / 'v86-door-instance.json'
    meta = json.loads(meta_path.read_text())
    assert 'input_bridge' not in meta and 'input_trace' not in meta
    name = 'core/v86_door/v86_worker.js'
    worker = candidate / name
    before = sha(worker)
    assert before == meta['fixture_inputs'][name] == meta['source_inputs'][name]
    text = worker.read_text()
    changes = [
        ("const { readFileSync } = require('fs');", "const { readFileSync } = require('fs');\nconst { createSerialInput } = require('./serial_input');"),
        ("// ─── Lifecycle", """let serialLoaded = false;
const serialInput = createSerialInput({
    ready: () => serialLoaded && emulator.v86.cpu.devices.uart0.input.length === 0,
    send: byte => emulator.serial0_send(String.fromCharCode(byte)),
    onError: error => {
        parentPort.postMessage({type: 'error', message: error.message});
        shutdown();
    },
});

// ─── Lifecycle"""),
        ("parentPort.postMessage({ type: 'ready' });", "serialLoaded = true;\n    parentPort.postMessage({ type: 'ready' });"),
        ("emulator.serial0_send(Buffer.from(msg.data).toString('binary'));", """try {
                serialInput.enqueue(Buffer.from(msg.data));
            } catch (error) {
                parentPort.postMessage({type: 'error', message: error.message});
                shutdown();
            }"""),
        ("shutdownStarted = true;", "shutdownStarted = true;\n    serialInput.close();"),
    ]
    for old, new in changes:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    helper = candidate / 'core/v86_door/serial_input.js'
    assert not helper.exists()
    shutil.copyfile(HERE / 'serial_input.js', helper)
    worker.write_text(text)
    record = dict(original_worker_sha256=before, staged_worker_sha256=sha(worker),
        helper_sha256=sha(helper), stager_sha256=sha(Path(__file__)),
        scope='Explicit candidate: bounded byte-exact host input ring; inject one byte after prior UART input is consumed. Uses pinned v86 internal UART input queue. No live modification.')
    meta['input_bridge'] = record
    meta['fixture_inputs'][name] = sha(worker)
    meta['fixture_inputs']['core/v86_door/serial_input.js'] = sha(helper)
    meta_path.write_text(json.dumps(meta, indent=2) + '\n')
    (candidate / 'v86-input-bridge.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Staged UART-consumption input bridge')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    stage(parser.parse_args().candidate)
