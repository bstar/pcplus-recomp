#!/usr/bin/env python3
"""Independently verify DOS pause timing, whole wire and deferred native events."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESC = b'\x1b'
QUERY = ESC + b'[6n'
HEADER = b'CONNECT\r\n\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:'
PREFIX = b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?62;2cKEYREADYkeys'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def receipt(folder, filename):
    result = read(folder / filename)
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
    raise AssertionError('Missing peer token: %r' % token)


def check_case(folder, name, marker, before, after, *, window=True, fresh=False):
    case = folder / name
    events = read(case / 'peer-events.json') if (case / 'peer-events.json').exists() else read(folder / 'peer-events.json')
    assert all(a['time'] <= b['time'] for a, b in zip(events, events[1:]))
    sends = [event for event in events if event['kind'] == 'send']
    assert [bytes.fromhex(event['hex']) for event in sends] == [
        b'\r\nOK\r\n', HEADER, b'HOLD', marker + QUERY, b'END', QUERY, b'\r\nOK\r\n']
    column = 26 + len(marker)
    reply = ESC + ('[1;%dR' % column).encode()
    post = ESC + ('[1;%dR' % (column + 3)).encode()
    expected = PREFIX + before + reply + after + b'PAUSEDONE' + (b'FRESHONLY' if fresh else b'')
    expected += b'doneSynth42\r' + post + b' ready+++ATH\r'
    wire = b''.join(bytes.fromhex(event['hex']) for event in events if event['kind'] == 'receive')
    assert wire == expected == (case / 'serial.bin').read_bytes()
    hold_time, query_time = sends[2]['time'], sends[3]['time']
    response = completed(events, reply, query_time)
    pause_end = completed(events, b'PAUSEDONE', hold_time)
    delay, elapsed = response - query_time, pause_end - hold_time
    assert 0 <= delay <= 1 and 4 <= elapsed <= 5 and response < pause_end
    if before:
        assert completed(events, before, query_time) < response
    for event_token in ([b'SECOND', b'FIRST'] if after == b'SECONDFIRST' else [after] if after else []):
        # Native CALL bodies must wait until the pause completes, even though
        # their monitor/FILE/frame state was scheduled while receiving data.
        assert completed(events, event_token, hold_time) - hold_time >= 4
    screen = (case / 'SCREEN.BIN').read_bytes()
    text = b'FIRST BYTE SAFELOGIN:HOLD' + marker + b'END'
    assert len(screen) == 4000 and screen[:len(text) * 2:2] == text
    assert len((case / 'BEFORE.BIN').read_bytes()) == 42
    assert (case / 'BEFORE.BIN').read_bytes() == (case / 'AFTER.BIN').read_bytes()
    raw = (case / 'RENDER.BIN').read_bytes()
    header = struct.unpack_from('<7H', raw)
    assert header[:4] == (0x524e, 1, 1, 1) and header[6] == 0
    assert raw[14:34] == raw[34:54] and raw[54:470] == raw[470:886]
    observation = struct.unpack('<7H', raw[-14:])
    if window:
        assert observation[1:4] == (1, 1, 0) and observation[4] > 72 and observation[6] == 0
    else:
        assert observation == (0, 0, 0, 0, 0, 0, 0)
    return dict(passed=True, query_reply_seconds=delay, pause_complete_seconds=elapsed,
                open_window=window, stale_text_excluded_from_future_WAITFOR=fresh,
                wire_sha256=hashlib.sha256(wire).hexdigest(),
                parent_sha256=sha(case / 'TERMINAL.EXE'), runner_sha256=sha(case / 'ASPECT.EXE'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('query', 'when', 'cancel', 'source-proof', 'cohort', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    query, when, cancel = args.query.resolve(), getattr(args, 'when').resolve(), args.cancel.resolve()
    cohort, output, source_proof = args.cohort.resolve(), args.output.resolve(), args.source_proof.resolve()
    assert all(path.is_relative_to(ROOT / 'build') for path in [query, when, cancel, cohort, source_proof])
    assert not cohort.exists() and not output.exists() and output.is_relative_to(ROOT / 'docs/validation')
    simple = receipt(query, 'query-checks.json')
    scripted = receipt(when, 'pause-checks.json')
    cancelled = receipt(cancel, 'cancel-checks.json')
    results = {'plain-PAUSE-query': check_case(query, 'window-pause-query-4', b'', b'', b'')}
    expected_cases = [
        ('transmit', b'WAKE', b'EVENT', b''), ('call', b'WAKE', b'', b'EVENT'),
        ('framed-call', b'WAKE', b'', b'FRAME'), ('plain-terminal', b'LIVE', b'', b''),
        ('future-wait', b'STALE', b'', b''), ('two-calls', b'WAKEBELL', b'', b'SECONDFIRST'),
    ]
    assert {case['case'] for case in scripted['cases']} == {'pause-when-' + row[0] for row in expected_cases}
    for name, marker, before, after in expected_cases:
        results[name] = check_case(when, 'pause-when-' + name, marker, before, after,
                                   window=name != 'plain-terminal', fresh=name == 'future-wait')
    assert results['plain-PAUSE-query']['query_reply_seconds'] == simple['reply_delay_seconds']
    assert results['plain-PAUSE-query']['pause_complete_seconds'] == simple['pause_complete_after_hold_seconds']
    child = results['plain-PAUSE-query']['runner_sha256']
    parent = results['plain-PAUSE-query']['parent_sha256']
    assert all(row['runner_sha256'] == child and row['parent_sha256'] == parent for row in results.values())
    assert cancelled['runner_sha256'] == child and cancelled['parent_sha256'] == parent
    case = cancel / 'pause-Escape'
    raw = (case / 'RENDER.BIN').read_bytes()
    assert struct.unpack_from('<7H', raw)[6] == cancelled['child_exit'] == 13
    assert len((case / 'BEFORE.BIN').read_bytes()) == 42
    assert (case / 'BEFORE.BIN').read_bytes() == (case / 'AFTER.BIN').read_bytes()
    assert b'UNREACHABLE' not in (case / 'serial.bin').read_bytes()
    checks = {}
    reports = ['build/aspect-foreground-delay/checks.json', 'build/aspect-script-receive-dos/checks.json',
               'build/aspect-render-client/checks.json', 'build/aspect-keyboard/key-client-checks.json',
               'build/aspect-render-client-dos/checks.json']
    for name in reports:
        result = read(ROOT / name)
        assert result['passed'] and result.get('runner_sha256', result.get('binary_sha256')) == child
        checks[name] = dict(cases=len(result['cases']), sha256=sha(ROOT / name))
    proof = read(source_proof)
    assert proof['passed'] and len(proof['products']) == 26 and proof['original_inputs'] == []
    assert proof['products']['aspect-runner/ASPECT.EXE']['actual'] == child
    assert proof['products']['terminal/TERMINAL.EXE']['actual'] == parent
    for name, digest in proof['sources'].items():
        assert sha(ROOT / name) == digest, name
    paths = [query, when, cancel, source_proof.parent, ROOT / 'build/aspect-script-receive-dos',
             ROOT / 'build/aspect-render-client-dos', ROOT / 'build/aspect-foreground-delay',
             ROOT / 'build/aspect-pause-when-dos/pause-when-02',
             ROOT / 'build/aspect-pause-cancel-dos/pause-cancel-01',
             ROOT / 'build/aspect-window-pressure-dos/pause-pressure-01',
             ROOT / 'build/aspect-window-pressure-dos/pause-pressure-02']
    paths += [ROOT / name for name in reports]
    paths += [ROOT / name for name in [
        'standalone/audit_aspect_pause_live.py', 'standalone/test_aspect_pause_when_dos.py',
        'standalone/test_aspect_pause_cancel_dos.py', 'standalone/test_aspect_window_pause_query_dos.py',
        'standalone/check_aspect_foreground_delay.py', 'standalone/check_aspect_render_client.py',
        'standalone/test_aspect_keys_dos.py', 'standalone/test_aspect_renderer_dos.py',
        'standalone/test_aspect_script_window_dos.py', 'standalone/test_connection_dos.py',
        'standalone/test_aspect_script_receive_dos.py', 'standalone/test_aspect_render_client_dos.py',
        'standalone/check_aspect_key_client.py']]
    cohort.mkdir()
    for path in paths:
        target = cohort / path.relative_to(ROOT)
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copyfile(path, target)
    files = {str(path.relative_to(cohort)): sha(path) for path in cohort.rglob('*') if path.is_file()}
    (cohort / 'files.json').write_text(json.dumps(files, indent=2) + '\n')
    report = dict(passed=True, parent_sha256=parent, runner_sha256=child,
                  explicit_terminal_pause_query_accepted=True, results=results, supporting_checks=checks,
                  actual_DOS_escape_cancelled=13, original_free_products=26,
                  source_proof_sha256=sha(source_proof), auditor_sha256=sha(Path(__file__)),
                  cohort=str(cohort.relative_to(ROOT)), frozen_files=len(files),
                  files_manifest_sha256=sha(cohort / 'files.json'),
                  failed_fixtures_retained=[
                      'pause-pressure-01: per-byte full WHEN/window callbacks caused serial failure14 and corrupt/missing replies under9KB load; no assertion is made about the uncaptured serial subcode. Bounded burst scheduling passes the separate pressure03 audit.',
                      'pause-pressure-02: final burst product passed tiles, replies, duration and cleanup; the expected user wire omitted the scripted PAUSEDONE marker. Corrected fixture passes in03.',
                      'pause-when-02: the subsequent WAITFOR test used FAILURE instead of WAITFOR result; all actual DOS cleanup checks passed, exact wire showed BADSTALE. Corrected fixture passes in03.',
                      'pause-cancel-01: actual DOS exit13 and cleanup passed; collector appended label twice and could not find checks.json. Corrected collector passes in02.'],
                  scope='Selected actual DOS attached-terminal PAUSE query/duration, native WHEN TRANSMIT, CALL, framed CALL, two pending calls, ordinary terminal without help, future WAITFOR and Escape cancellation. Raw ASIO binary/tail behavior retains transport-only delays. No query parser substitute, software audio, physical UART/carrier/CTS or whole-application acceptance.',
                  compatibility_policy='An admitted terminal consumes ordinary arriving text through native translation/WHEN/rendering during explicit PAUSE. Future WAITFOR/RGET see subsequent input. Raw ASIO and generic low-level delays retain queued input. This is an intentional maintained scheduling change, not exact native delay timing.')
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, actual_DOS_positive_cases=len(results),
                         max_reply_seconds=max(row['query_reply_seconds'] for row in results.values()),
                         frozen_files=len(files))))


if __name__ == '__main__':
    main()
