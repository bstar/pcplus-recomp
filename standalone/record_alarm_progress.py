#!/usr/bin/env python3
"""Bind progress-budget ALARM models, product gates, cold rebuild and BBS regressions."""
import json
import struct
from pathlib import Path
from build_context_help import ROOT, sha


def main():
    sources, receipts = {}, {}

    def load(name, source_field=None):
        path = ROOT / name
        result = json.loads(path.read_text())
        assert result['passed'], name
        receipts[name] = sha(path)
        if source_field:
            for key, value in result[source_field].items():
                assert sha(ROOT / key) == value, key
                sources[key] = value
        return result

    parent = ROOT / 'build/terminal-alarm-policy-admission-20261106'
    child = ROOT / 'build/aspect-alarm-progress-20261106'
    products = {'TERMINAL.EXE':sha(parent / 'TERMINAL.EXE'), 'ASPECT.EXE':sha(child / 'ASPECT.EXE')}
    assert products['ASPECT.EXE'] == '12c5f77e9eaeda8bec6643478b6d04819272dd57b625060c8c5619c8f2ff6ea2'
    for folder in (parent, child):
        path = folder / 'manifest.json'
        manifest = json.loads(path.read_text())
        assert manifest['binary_sha256'] in products.values()
        for name, digest in manifest['sources'].items():
            assert sha(ROOT / name) == digest, name
            sources[name] = digest
        receipts[str(path.relative_to(ROOT))] = sha(path)
    legacy = load('build/alarm-progress-legacy-final-20261106/result.json', 'sources')
    assert (legacy['cases'], legacy['checks']) == (94, 1701)
    model = load('build/alarm-progress-model-production-limit-20261106/result.json', 'sources')
    assert (model['cases'], model['checks']) == (33, 1457099)
    assert 'TOTAL_LIMIT services2000000' in model['output']
    assert len(model['modeled_fast_clock_cases']) == 2
    assert all(c['service_calls'] > 2000000 for c in model['modeled_fast_clock_cases'])
    for label, count in (('progress-when-20261106',5), ('progress-sound-keys-20261106',3)):
        folder = ROOT / 'build/aspect-alarm-vm-dos' / label
        for filename in ('checks.json', 'pause-checks.json'):
            report = load(str((folder / filename).relative_to(ROOT)))
            assert len(report['cases']) == count and all(all(c['checks'].values()) for c in report['cases'])
            assert report['runner_sha256'] == products['ASPECT.EXE']
            if filename == 'checks.json':
                assert report['terminal_sha256'] == products['TERMINAL.EXE']
            else:
                assert report['parent_sha256'] == products['TERMINAL.EXE']
                for name, digest in report['captures_sha256'].items():
                    path = folder / name
                    assert sha(path) == digest, path
                    receipts[str(path.relative_to(ROOT))] = digest
        if count == 3:
            report = load(str((folder / 'speaker-checks.json').relative_to(ROOT)))
            assert report['enabled'] and len(report['cases']) == 3
            assert all(all(c['checks'].values()) for c in report['cases'])
    capacity = load('build/alarm-progress-capacity-20261106/result.json', 'sources')
    assert capacity['binary_sha256'] == products['TERMINAL.EXE'] and capacity['interpreter_sha256'] == products['ASPECT.EXE']
    assert len(capacity['checks']) == 27 and all(capacity['checks'].values())
    assert capacity['held_streams'] and capacity['streams_around_child'] and capacity['nested_child_count'] == 3
    capacity8086 = load('build/alarm-progress-capacity-8086-20261106/result.json', 'sources')
    assert capacity8086['interpreter_sha256'] == products['ASPECT.EXE'] and capacity8086['binary_sha256'] == products['TERMINAL.EXE']
    assert capacity8086['cpu'] == '8086' and len(capacity8086['checks']) == 26 and all(capacity8086['checks'].values())
    cold = load('build/alarm-progress-cold-final-20261106/result.json', 'overlay_sources')
    assert cold['products'] == products
    inventory = ROOT / 'build/alarm-progress-cold-final-20261106/inventory.json'
    assert sha(inventory) == cold['inventory_sha256'] and len(json.loads(inventory.read_text())) == cold['source_files']
    assert cold['results']['legacy']['cases'] == 94 and cold['results']['progress']['cases'] == 33
    assert cold['results']['unit']['cases'] == 33341 and cold['results']['numeric']['cases'] == cold['results']['strings']['cases'] == 512
    assert cold['results']['ALARM']['cases'] == 1
    sync = load('build/bbs-lab/results/synchronet/alarm-progress-sync-20261106/proxy-integration.json')
    assert sync['binary_sha256'] == products['TERMINAL.EXE'] and sync['interpreter_sha256'] == products['ASPECT.EXE']
    assert all(sync['checks'].values()) and sync['external_viewer']['passed']
    for name, digest in sync['product_inputs'].items():
        assert sha(ROOT / name) == digest, name
        sources[name] = digest
    carrier = load('build/bbs-lab/results/enigma/alarm-progress-carrier-20261106/carrier-checks.json', 'sources')
    assert all(carrier['checks'].values()) and carrier['transfer_wait_ms'] == 150000
    audit = load('build/alarm-progress-carrier-audit-20261106/result.json', 'sources')
    assert audit['exact_retry_bytes'] == 65539
    for name, digest in audit['captures'].items():
        assert sha(ROOT / name) == digest, name
        receipts[name] = digest
    for name, digest in products.items():
        assert audit['products'][name]['sha256'] == digest
    default = ROOT / 'build/aspect-runner/ASPECT.EXE'
    assert sha(default) == '91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b'
    for name, digest in json.loads(default.with_name('manifest.json').read_text())['sources'].items():
        assert sha(ROOT / name) == digest, name
    for name in ('standalone/record_alarm_progress.py','standalone/test_aspect_alarm_vm_dos.py',
                 'standalone/alarm_speaker_observer.py','standalone/alarm_error_fixtures.py'):
        sources[name] = sha(ROOT / name)
    words = struct.unpack_from('<14H', (child / 'ASPECT.EXE').read_bytes())
    module = words[2]*512-(512-words[1] if words[1] else 0)-words[4]*16
    minimum = (((module+15)//16)+words[5]+16)*16
    assert minimum == 131152
    result = dict(passed=True, release_accepted=False, products=products, sources=sources, receipts=receipts,
                  model_cases=model['modeled_duration_cases'], fast_model_cases=model['modeled_fast_clock_cases'],
                  cold_source_files=cold['source_files'], child_minimum_including_PSP=minimum, original_inputs=[],
                  scope=__doc__, limitations=[
                      'Modeled clocks advance per callback, not nine wall-clock hours. New policy renews only at distinct valid seconds already observed by native flow; tone/tick/service failures remain bounded. Not physical long-duration acceptance.',
                      'New child is208 bytes above the preceding minimum, retaining all bank/stack/stream/buffer capacities.386 held-stream27 checks and8086 stream-around-child26 checks pass; these are emulator capacity gates.',
                      'Five native WHEN/render cases plus three sounding completion-key cases use UMB observers and actual emulated BIOS/UART/PIT. No injected active-alert carrier/service failure yet.',
                      'Cold export repeats modeled legacy/progress suites, bank API/1024slot/fourdeep cases and one actual-parent ALARM case, not whole root BBS/key/capacity matrices. Initial completed cold run failed only while aggregating integer case counts; corrected fresh run is accepted.',
                      'Synchronet/Enigma are isolated stock loopback laboratories with staged SynthModem Telnet code. No physical SPA2102/SIP/DSP/analog/CTS acceptance. Installed RCC859D7/selector/private history remain unchanged; package/physical/full-parity gates stay open.'
                  ])
    (ROOT / 'docs/validation/aspect-alarm-progress.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS ALARM progress watchdog/product/cold/BBS checkpoint')


if __name__ == '__main__':
    main()
