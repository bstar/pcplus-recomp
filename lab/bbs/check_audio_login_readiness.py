#!/usr/bin/env python3
"""Actual DOS proof of readiness arriving inside a deferred art callback."""
import argparse
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'standalone'))
import test_aspect_script_serial_dos as serial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output.resolve(); assert out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True, exist_ok=False)
    # Reuse the actual UART parent, DOS ASPECT runner, compiler and cleanup
    # assertions. Only the independent peer gains two output-gated phases.
    source = Path(serial.__file__).read_text()
    old = '''                    if not sent.is_set() and (not trigger or trigger in wire):
                        if incoming:
                            connection.sendall(incoming)
                        sent.set()'''
    new = '''                    phases = model['phases']
                    index = getattr(peer, 'phase', 0)
                    if index < len(phases) and bytes.fromhex(phases[index]['after']) in wire:
                        connection.sendall(bytes.fromhex(phases[index]['send']))
                        peer.phase = index + 1
                        if peer.phase == len(phases): sent.set()'''
    assert source.count(old) == 1
    module = types.ModuleType('audio_readiness_peer'); module.__file__ = serial.__file__
    exec(compile(source.replace(old, new), serial.__file__, 'exec'), module.__dict__)
    cases = []
    for name, latch, reuse in [('MISSED', False, False), ('LATCHED', True, False), ('REUSED', True, True)]:
        text = ('integer main_seen\n' if latch else '') + 'proc main\n'
        if latch: text += 'main_seen=0\n'
        if latch and not reuse: text += 'when 1 "Main Menu" call seen\n'
        if reuse: text += 'when 0 "UNUSED" transmit "BAD"\nwhen 2 "OTHER" transmit "BAD"\nwhen 1 "PAUSE" call advance\n'
        else: text += 'when 0 "PAUSE" call advance\n'
        text += 'transmit "READY"\nwaitfor "Main Menu" 1\n'
        text += 'if ' + ('main_seen' if latch else 'waitfor') + '\ntransmit "SEEN"\nelse\ntransmit "MISSED"\nendif\nendproc\n'
        text += 'proc advance\ncwhen ' + ('1' if reuse else '0') + '\n'
        if reuse: text += 'when 1 "Main Menu" call seen\n'
        text += 'transmit "HANDLER"\nwaitquiet 1 3\nendproc\n'
        if latch: text += 'proc seen\ncwhen 1\nmain_seen=1\nendproc\n'
        cases.append({'name': name, 'source': text, 'hex': serial.compile_source(text).hex(),
                      'serial': {'input_hex': b'PAUSEMain Menu'.hex(), 'send_after_tx_hex': b'READY'.hex(),
                                 'phases': [{'after': b'READY'.hex(), 'send': b'PAUSE'.hex()},
                                            {'after': b'HANDLER'.hex(), 'send': b'Main Menu'.hex()}]},
                      'expected': {'tx_hex': (b'READYHANDLER' + (b'SEEN' if latch else b'MISSED')).hex(), 'stdout_hex': ''}})
    inputs = {str(p.relative_to(ROOT)): serial.sha(p) for p in
              [Path(__file__), Path(serial.__file__), ROOT/'src/aspect/compiler.py', ROOT/'build/aspect-runner/ASPECT.EXE']}
    (out/'predictions.json').write_text(json.dumps({'inputs': inputs, 'cases': cases}, indent=2)+'\n')
    driver = module.build_driver(out)
    results = [module.run(case, ROOT/'build/aspect-runner/ASPECT.EXE', out, driver) for case in cases]
    assert all(serial.sha(ROOT/n) == h for n, h in inputs.items())
    report = {'passed': all(r['passed'] for r in results), 'cases': results, 'inputs': inputs,
              'predictions_sha256': serial.sha(out/'predictions.json'),
              'scope': 'Actual DOS ASIOv1 UART child and independent phased peer. Main Menu arrives only after a deferred art callback starts its WAITQUIET. Immediate WAITFOR-result testing misses it; active WHEN readiness latches observe it, including reuse of an existing one-shot slot while all three native slots were occupied. This proves a script race mechanism, not the exact cause of audio editor03 or a BBS/editor/hardware pass.'}
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': report['passed'], 'cases': [{k:r[k] for k in ('name','passed','tx_hex')} for r in results]}, indent=2))
    assert report['passed']


if __name__ == '__main__': main()
