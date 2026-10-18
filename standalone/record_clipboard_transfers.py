#!/usr/bin/env python3
"""Record actual DOS clipboard/prompt/protocol ownership evidence."""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def verify_sources(report):
    for path, digest in report.get('sources', {}).items():
        assert sha(path) == digest, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    folder = Path('build/clipboard-transfer-dos') / args.label
    evidence = read(folder / 'checks.json')
    runtime = sha('build/terminal/TERMINAL.EXE')
    assert evidence['passed'] and evidence['binary_sha256'] == runtime
    verify_sources(evidence)
    expected = {'xmodem-rx-single', 'xmodem-tx-single', 'ymodem-rx-tagged',
                'ymodem-tx-all', 'xmodem-rx-stale', 'xmodem-rx-prompt-cancel'}
    assert {case['case'] for case in evidence['cases']} == expected
    assert len(evidence['cases']) == len(expected)
    artifacts = [folder / 'checks.json']
    ownership = {}
    for case in evidence['cases']:
        assert case['passed'] and all(case['checks'].values())
        assert case['binary_sha256'] == runtime
        case_folder = folder / case['case']
        assert read(case_folder / 'result.json') == case
        assert read(case_folder / 'selections.json') == case['selections']
        raw = (ROOT / case_folder / 'KWATCH.BIN').read_bytes()
        assert len(raw) == 5254
        magic, count, overflow = struct.unpack_from('<3H', raw)
        assert magic == 0x4b57 and 0 < count <= 32 and overflow == 0
        events = []
        for index in range(count):
            offset = 6 + index * 164
            key, tick = struct.unpack_from('<2H', raw, offset)
            events.append(dict(key=key, tick=tick,
                               header=raw[offset + 4:offset + 84].decode('cp437'),
                               footer=raw[offset + 84:offset + 164].decode('cp437')))
        assert events == case['observed_keys'] == read(case_folder / 'key-events.json')
        prompts = [e for e in events if e['footer'].startswith((' Download:', ' Upload:', ' YMODEM'))]
        transfers = [e for e in events if e['footer'].startswith((' Receiving', ' Sending'))]
        for phase in (prompts, transfers):
            keys = {e['key'] for e in phase}
            assert 0x8300 in keys and keys & {0x8400, 0x84e0}
            assert all('Filename Clipboard' not in e['header'] for e in phase)
        assert {ord('p'), ord('s'), ord('t')} <= {e['key'] & 255 for e in transfers}
        ownership[case['case']] = dict(raw_BIOS_records_replayed=count,
                                      both_hotkeys_observed_at_local_prompt=True,
                                      both_hotkeys_and_paste_keys_observed_during_protocol=True,
                                      no_clipboard_header_during_either_phase=True)
        wire = (ROOT / case_folder / 'serial.bin').read_bytes()
        for selection in case['selections']:
            packet = bytes.fromhex(selection['packet_hex'])
            offset = selection['wire_offset']
            assert wire[offset:offset + len(packet)] == packet
        # Include observer sources/COMs, actual video/key samples, wire, DOS
        # files and invocation, rather than retaining only summarized booleans.
        artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT / case_folder).rglob('*'))
                         if p.is_file())
    manifest = read('build/terminal/manifest.json')
    assert manifest['binary_sha256'] == runtime
    verify_sources(manifest)
    regression = read('build/terminal/setup-profile-regression.json')
    commands = subprocess.check_output(['make', '-n', 'test-terminal'], cwd=ROOT,
                                       text=True).splitlines()
    assert regression['passed'] and regression['complete']
    assert regression['binary_sha256'] == runtime and len(commands) == 77
    assert [r['command'] for r in regression['commands']] == commands
    assert all(r['exit_code'] == 0 for r in regression['commands'])
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['output_count'] == 64
    assert proof['outputs']['terminal/TERMINAL.EXE']['sha256'] == runtime
    assert proof['outputs']['terminal/TERMINAL.EXE']['matches_workspace']
    artifacts.extend(map(Path, ['build/terminal/manifest.json',
                               'build/terminal/setup-profile-regression.json']))
    result = dict(
        passed=True, binary_sha256=runtime, actual_DOS=evidence,
        independent_BIOS_replay=ownership,
        runtime_sources=manifest['sources'],
        sources={'standalone/record_clipboard_transfers.py': sha('standalone/record_clipboard_transfers.py')},
        retained_artifacts={str(p): sha(p) for p in artifacts},
        terminal_regression=dict(commands=77, report='build/terminal/setup-profile-regression.json'),
        source_rebuild=dict(report=proof_path, output_count=64,
                            source_snapshot_sha256=proof['source_snapshot_sha256']),
        scope='Six production DOS clipboard filename/prompt/XMODEM/YMODEM workflows. '
              'Independent strict framing peers and BIOS key/video observers; exact '
              'received files, unchanged upload sources, post-transfer clipboard reuse, '
              'stale-name and canceled-local-prompt recovery. These are controlled peers, '
              'not stock BBS or physical RS-232 Wi-Fi modem validation. Full F11 and all '
              'whole-application gates remain open.')
    (ROOT / 'docs/validation/clipboard-transfers.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded six DOS clipboard transfer workflows', runtime)


if __name__ == '__main__':
    main()
