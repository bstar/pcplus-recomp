#!/usr/bin/env python3
"""Audit raw DOS confirmation captures independently of their producer modules."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESC = b'\x1b'
QUERY = ESC + b'[6n'
BANNER = b'CONNECT\r\n' + ESC + b'[2J' + ESC + b'[HFIRST BYTE SAFE' + QUERY + ESC + b'[0cLOGIN:'
OK = b'\r\nOK\r\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def receipt(folder):
    result = read(folder / 'confirmation-checks.json')
    assert result['passed']
    for name, digest in result['captures_sha256'].items():
        path = (folder / name).resolve()
        assert path.is_relative_to(folder) and sha(path) == digest, name
    return result


def completed(events, token, since):
    stream = b''
    for event in events:
        if event['kind'] == 'receive' and event['time'] >= since:
            stream += bytes.fromhex(event['hex'])
            if token in stream:
                return event['time']
    raise AssertionError('Missing token: %r' % token)


def packets():
    # Reconstruct the declared44 distinct ANSI tiles without importing the
    # workload generator or its receipt expectations.
    result = []
    for index in range(44):
        row, col = index // 2 + 2, (41 if index % 2 else 1)
        text = ('PKT%02d:' % index + ''.join(chr(65 + (index * 7 + n * 11) % 26) for n in range(26))).encode()
        payload = ESC + ('[%d;%dH' % (row, col)).encode()
        payload += b''.join(ESC + (b'[31m' if n % 2 == 0 else b'[32m') + bytes([byte]) for n, byte in enumerate(text))
        payload += ESC + b'[0m' + QUERY
        result.append((row, col, text, payload, ESC + ('[%d;%dR' % (row, col + 32)).encode()))
    assert sum(len(p[3]) for p in result) == 9114
    return result


def check_case(folder, name, kind, *, enhanced=False):
    target = folder / name
    events_file = target / 'peer-events.json'
    events = read(events_file if events_file.exists() else folder / 'peer-events.json')
    assert all(a['time'] <= b['time'] for a, b in zip(events, events[1:]))
    sends = [e for e in events if e['kind'] == 'send']
    replies = []
    before = b''
    expected_sends = [OK, BANNER]
    if kind == 'pressure':
        workload = packets()
        expected_sends += [p[3] for p in workload] + [b'END', QUERY, OK]
        replies = [(p[3], p[4]) for p in workload]
        middle = b''.join(p[4] for p in workload) + b'DECLINEDdone'
        post = ESC + b'[23;76R'
    else:
        marker = b'DATA' if kind == 'rget' else b'WAKE' if kind in ('tx', 'call') else b''
        packet = marker + QUERY
        reply = ESC + (b'[1;26R' if marker else b'[1;22R')
        expected_sends += [packet]
        replies = [(packet, reply)]
        if kind == 'yes':
            middle, post = reply, b''
        else:
            expected_sends += [b'FRESH', b'END', QUERY]
            before = b'EVENT' if kind == 'tx' else b''
            following = b'FRAMEDECLINED' if kind == 'call' else b'RGETEMPTY' if kind == 'rget' else b'DECLINED'
            middle = before + reply + following + b'FRESHOKdone'
            post = ESC + (b'[1;34R' if marker else b'[1;30R')
        expected_sends += [OK]
    assert [bytes.fromhex(e['hex']) for e in sends] == expected_sends, name
    expected = b'ATZ\rATDCaseTest:23\r' + ESC + b'[1;16R'
    expected += ESC + (b'[?1;2c' if enhanced else b'[?62;2c') + b'KEYREADY' + middle
    if kind != 'yes':
        expected += b'Synth42\r' + post
    expected += b' ready+++ATH\r'
    wire = b''.join(bytes.fromhex(e['hex']) for e in events if e['kind'] == 'receive')
    assert wire == expected == (target / 'serial.bin').read_bytes(), name
    delays = []
    for packet, reply in replies:
        sent = [e for e in sends if bytes.fromhex(e['hex']) == packet]
        # Post-script CPR is identical in the simple cases. Select the query
        # after CONNECT; its completion must precede No/Yes script return.
        start = sent[0]['time']
        end = completed(events, reply, start)
        assert 0 <= end - start <= 1
        delays.append(end - start)
        tail = b' ready' if kind == 'yes' else b'RGETEMPTY' if kind == 'rget' else b'DECLINED'
        assert end <= completed(events, tail, start)
        if before:
            assert completed(events, before, start) < end
        if kind == 'call':
            assert completed(events, b'FRAME', start) > end
    raw = (target / 'RENDER.BIN').read_bytes()
    header = struct.unpack_from('<7H', raw)
    assert header[:4] == (0x524e, 1, 1, 1)
    assert header[6] == (13 if kind == 'yes' else 0)
    assert raw[14:34] == raw[34:54] and raw[54:470] == raw[470:886]
    observation = struct.unpack('<4H', raw[-8:])
    assert observation[1:3] == (1, 1) and observation[3] > (72 if kind == 'pressure' else 18)
    hardware = (target / 'BEFORE.BIN').read_bytes()
    assert len(hardware) == 42 and hardware == (target / 'AFTER.BIN').read_bytes()
    screen = (target / 'SCREEN.BIN').read_bytes()
    assert len(screen) == 4000
    if kind != 'yes':
        marker = b'DATA' if kind == 'rget' else b'WAKE' if kind in ('tx', 'call') else b''
        text = b'FIRST BYTE SAFELOGIN:' + marker + (b'' if kind == 'pressure' else b'FRESHEND')
        assert screen[:len(text)*2:2] == text
    if kind == 'pressure':
        for row, col, text, _, _ in workload:
            at = 2 * ((row - 1) * 80 + col - 1)
            assert screen[at:at+64:2] == text
            assert screen[at+1:at+64:2] == bytes([4, 2] * 16)
    return dict(passed=True, query_reply_seconds=delays, prompt_ticks=observation[3], child_exit=header[6],
                parent_sha256=sha(target/'TERMINAL.EXE'), runner_sha256=sha(target/'ASPECT.EXE'),
                whole_wire_sha256=sha(target/'serial.bin'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('decline', 'yes', 'events', 'pressure', 'source-proof', 'stack', 'process', 'cohort', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    paths = {name: getattr(args, name.replace('-', '_')).resolve() for name in
             ('decline', 'yes', 'events', 'pressure', 'source-proof', 'stack', 'process', 'cohort', 'output')}
    assert all(p.is_relative_to(ROOT/'build') for n, p in paths.items() if n != 'output')
    assert paths['output'].is_relative_to(ROOT/'docs/validation')
    assert not paths['output'].exists() and not paths['cohort'].exists()
    results = {}
    specs = {
        'decline': [('abort-'+n, 'no') for n in ('No', 'Enter', 'Escape', 'invalid-extended')],
        'yes': [('abort-Yes-'+n, 'yes') for n in ('WAITFOR', 'PAUSE')],
        'events': [('abort-WHEN-TX', 'tx'), ('abort-WHEN-CALL', 'call'), ('abort-RGET', 'rget')],
        'pressure': [('abort-pressure', 'pressure')],
    }
    for group, cases in specs.items():
        producer = receipt(paths[group])
        checker = 'confirm' if group == 'decline' else group
        assert producer['checker_sha256'] == sha(ROOT/'standalone'/('test_aspect_abort_' + checker + '_dos.py'))
        for name, kind in cases:
            results[name] = check_case(paths[group], name, kind, enhanced=name == 'abort-Escape')
    parents = {r['parent_sha256'] for r in results.values()}
    children = {r['runner_sha256'] for r in results.values()}
    assert len(parents) == len(children) == 1
    parent, child = parents.pop(), children.pop()
    proof = read(paths['source-proof'])
    assert proof['passed'] and proof['original_inputs'] == [] and len(proof['products']) == 26
    assert proof['products']['terminal/TERMINAL.EXE']['actual'] == parent
    assert proof['products']['aspect-runner/ASPECT.EXE']['actual'] == child
    for name, digest in proof['sources'].items():
        assert sha(ROOT/name) == digest, name
    stack = read(paths['stack'])
    assert stack['passed'] and stack['corpus_cases'] == 2043 and len(stack['depth_cases']) == 18
    assert stack['candidate_CLI_stack_bytes'] == 24576 and stack['checked_API_stack_bytes'] == 16384
    assert stack['compiler_sha256'] == proof['products']['aspect-compiler-dos/ASPCOMP.EXE']['actual']
    assert stack['checker_sha256'] == sha(ROOT/'standalone/check_aspect_compiler_stack.py')
    assert stack['reused_corpus_checker_sha256'] == sha(ROOT/'standalone/check_aspect_compiler_dos.py')
    process = read(paths['process'])
    assert process['passed'] and len(process['cases']) == 13
    assert all(case['passed'] and all(case['checks'].values()) for case in process['cases'])
    assert process['parent_sha256'] == proof['products']['terminal-process/TERMINAL.EXE']['actual']
    assert process['child_sha256'] == proof['products']['aspect-process-parent/ASPECT.EXE']['actual']
    for name, digest in process['source_hashes'].items():
        assert sha(ROOT/name) == digest, name
    supports = {}
    support_paths = [ROOT/'build'/n/f for n, f in [
        ('aspect-abort-owner','checks.json'), ('terminal-abort-confirm','checks.json'),
        ('terminal-abort-confirm-mouse','checks.json'), ('aspect-foreground-delay','checks.json'),
        ('aspect-render-client','checks.json'), ('aspect-keyboard','key-client-checks.json'),
        ('aspect-script-receive-dos','checks.json'), ('aspect-render-client-dos','checks.json')]]
    for path in support_paths:
        result = read(path)
        assert result['passed']
        identity = result.get('runner_sha256', result.get('binary_sha256', result.get('terminal_sha256')))
        expected = sha(ROOT/'build/terminal-mouse/TERMINAL.EXE') if 'mouse' in str(path) else parent if path.parent.name == 'terminal-abort-confirm' else child
        assert identity == expected, path
        supports[str(path.relative_to(ROOT))] = dict(cases=len(result['cases']), sha256=sha(path))
    # Preserve source inputs with the raw observations. Results and artifacts
    # stay local; only this textual acceptance receipt belongs in public Git.
    freeze = [paths[n] for n in specs] + [paths[n].parent for n in ('source-proof','stack','process')]
    freeze += support_paths + [Path(__file__)]
    freeze += [ROOT/n for n in proof['sources']]
    freeze += list((ROOT/'standalone').glob('*abort*.py'))
    freeze += [ROOT/'standalone'/n for n in ('check_aspect_compiler_stack.py', 'check_aspect_compiler_dos.py', 'compiler_heap_snapshot.c', 'compiler_heap_snapshot.h')]
    cohort = paths['cohort'];cohort.mkdir()
    for path in freeze:
        target = cohort/path.relative_to(ROOT)
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)
    files = {str(p.relative_to(cohort)):sha(p) for p in cohort.rglob('*') if p.is_file()}
    (cohort/'files.json').write_text(json.dumps(files, indent=2)+'\n')
    result = dict(passed=True, parent_sha256=parent, runner_sha256=child, results=results,
                  supporting_checks=supports, original_free_products=26, compiler_stack_cases=2043,
                  attached_PROGRAM_cases=13, source_proof_sha256=sha(paths['source-proof']),
                  compiler_stack_proof_sha256=sha(paths['stack']), PROGRAM_proof_sha256=sha(paths['process']),
                  retained_failed_experiments=[
                      'build/aspect-abort-confirm-dos/immediate-cancel-01: old pair cancels instead of declining; counterexample only',
                      'build/aspect-abort-confirm-dos/cooperative-02: fixture sent END before fresh wait; unaccepted',
                      'build/aspect-abort-confirm-dos/cooperative-04: combined timing events crossed session boundaries; unaccepted',
                      'build/aspect-abort-events-dos/cooperative-01: unsupported string comparison fixture; unaccepted',
                      'build/abort-confirm-external-overflow-01: near TEXT overflow before PROGRAMCODE placement',
                      'build/abort-confirm-compiler-control-01/tree/build/aspect-parent-process/old-control: original baseline repeats heap exhaustion',
                      'build/abort-confirm-compiler-memory-diagnostic-01: private allocator and heap-growth candidates failed; not adopted',
                      'build/aspect-compiler-stack/guard16-01: stderr did not observe CRT console overflow; unaccepted'],
                  auditor_sha256=sha(Path(__file__)), cohort=str(cohort.relative_to(ROOT)), frozen_files=len(files),
                  files_manifest_sha256=sha(cohort/'files.json'),
                  scope='Ten actual DOS confirmation workflows: defaultNo/Enter/Esc, invalid extended key, Yes WAITFOR/PAUSE, native WHEN TRANSMIT/deferred framed CALL, suspended RGET, and9114 ANSI bytes/44 CPRs. Exact wires, prompt ownership/render progress, frame/attributes and sampled cleanup. No actual CTS/RTS/XOFF/XON, software audio, physical hardware or whole-application acceptance.')
    paths['output'].write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=True, actual_DOS_cases=len(results), max_reply_seconds=max(max(r['query_reply_seconds']) for r in results.values()), frozen_files=len(files))))


if __name__ == '__main__':
    main()
