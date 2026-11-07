#!/usr/bin/env python3
"""Bind ALARM speaker policy, completion-key cleanup and duration restoration."""
import json
import struct
from build_context_help import ROOT, sha


def main():
    previous = ROOT / 'docs/validation/aspect-alarm-policy.json'
    base = json.loads(previous.read_text())
    assert base['passed'] and not base['release_accepted']
    products = base['products']
    sources, receipts, cases = {}, {str(previous.relative_to(ROOT)): sha(previous)}, []
    for folder in ('terminal-alarm-policy-admission-20261106',
                   'aspect-alarm-numeric-groups-final-20261106'):
        path = ROOT / 'build' / folder / 'manifest.json'
        for name, digest in json.loads(path.read_text())['sources'].items():
            assert sha(ROOT / name) == digest, name
            sources[name] = digest
        receipts[str(path.relative_to(ROOT))] = sha(path)
    for label, count, enabled in (('sound-natural-groups-20261106', 2, True),
                                  ('sound-keys-groups-20261106', 3, True),
                                  ('quiet-observer-groups-20261106', 1, False)):
        folder = ROOT / 'build/aspect-alarm-vm-dos' / label
        for filename in ('checks.json', 'pause-checks.json', 'speaker-checks.json'):
            path = folder / filename
            report = json.loads(path.read_text())
            assert report['passed'] and len(report['cases']) == count
            receipts[str(path.relative_to(ROOT))] = sha(path)
            for case in report['cases']:
                assert case['passed'] and all(case['checks'].values())
            if filename == 'checks.json':
                assert report['terminal_sha256'] == products['TERMINAL.EXE']
                assert report['runner_sha256'] == products['ASPECT.EXE']
                for case in report['cases']:
                    target = folder / case['case']
                    assert sha(target / 'TERMINAL.EXE') == products['TERMINAL.EXE']
                    assert sha(target / 'ASPECT.EXE') == products['ASPECT.EXE']
                    assert case['checks']['keys_during_script_before_continuation']
                    assert case['passive_observer_header'][6] == 0
                    if 'keys-' in case['case']:
                        text = (target / 'LOGIN.ASP').read_text()
                        assert text.count('alarm ') == 1 and 'alarm 32767\n' in text
            elif filename == 'pause-checks.json':
                assert report['parent_sha256'] == products['TERMINAL.EXE']
                assert report['runner_sha256'] == products['ASPECT.EXE']
                for name, digest in report['captures_sha256'].items():
                    path = folder / name
                    assert sha(path) == digest, path
                    receipts[str(path.relative_to(ROOT))] = digest
            else:
                assert report['enabled'] == enabled
                for case in report['cases']:
                    raw = (folder / case['case'] / 'RENDER.BIN').read_bytes()
                    on, edges, last, port, owned, duration, abi = struct.unpack('<7H', raw[-28:-14])
                    assert (on > 0 and edges >= 2) if enabled else on == edges == 0
                    assert (port, owned, duration, abi) == (0, 0, 4, 1)
                    assert case['speaker_on_ticks'] == on and case['speaker_gate_edges'] == edges
                    cases.append(dict(case, sound_enabled=enabled, label=label))
    for name in ('standalone/test_aspect_alarm_vm_dos.py',
                 'standalone/alarm_speaker_observer.py',
                 'standalone/test_aspect_pause_when_dos.py',
                 'standalone/test_aspect_keys_dos.py',
                 'standalone/test_aspect_script_window_dos.py',
                 'standalone/test_aspect_renderer_dos.py',
                 'standalone/test_connection_dos.py',
                 'standalone/test_aspect_window_query_dos.py',
                 'standalone/record_alarm_speaker.py'):
        sources[name] = sha(ROOT / name)
    assert len(cases) == 6
    result = dict(passed=True, release_accepted=False, products=products,
                  sources=sources, receipts=receipts, cases=cases, original_inputs=[],
                  scope=__doc__, limitations=[
                      'Passive port61 samples show enabled gate activity and cleanup, not exact PIT frequency, cadence, acoustic output or physical speaker condition.',
                      'Duration restoration is sampled at DOS child exit under DS=SS after a single explicit32767 ALARM; it does not observe the duration word at each intervening instruction.',
                      'Quiet control and sounding tests use standard BIOS/ANSI and a UMB observer. No real serial/SIP/audio/CTS acceptance, new cold build, package selection or deployment.',
                      'Malformed operands, full-duration service budgets and carrier/error cleanup remain open. Early completion of32767 alerts does not prove nine-hour operation.'
                  ])
    (ROOT / 'docs/validation/aspect-alarm-speaker.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS six ALARM speaker/cleanup/restoration cases')


if __name__ == '__main__':
    main()
