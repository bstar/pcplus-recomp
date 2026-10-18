#!/usr/bin/env python3
"""Publish explicit actual-DOS BBS transfer results without copying lab data."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='append', required=True,
                        help='SERVER:LABEL; include failed attempts explicitly')
    parser.add_argument('--output', default='docs/validation/bbs-transfers.json')
    args = parser.parse_args()
    binary = digest(ROOT / 'build/terminal/TERMINAL.EXE')
    runs = []
    for selector in args.run:
        server, label = selector.split(':', 1)
        assert server in ('synchronet', 'enigma')
        assert label.replace('-', '').replace('_', '').isalnum()
        folder = ROOT / 'build/bbs-lab/results' / server / label
        result = json.loads((folder / 'result.json').read_text())
        assert result['binary_sha256'] == binary
        assert result['name'] == server and result['label'] == label
        entry = {'server': server, 'label': label, 'result': result}
        protocol = folder / 'protocol.json'
        if protocol.exists():
            entry['protocol'] = json.loads(protocol.read_text())
        metadata = folder / 'server-audit.stdout'
        if metadata.exists():
            try:
                entry['server_metadata'] = json.loads(metadata.read_text())
            except ValueError:
                entry['server_metadata_unparseable'] = True
        session = folder / 'server-session-audit.json'
        if session.exists():
            entry['server_session'] = json.loads(session.read_text())
        failure = folder / 'harness-failure.json'
        if failure.exists():
            entry['harness_failure'] = json.loads(failure.read_text())
        entry['retained_artifacts'] = {
            str(p.relative_to(ROOT)): digest(p)
            for p in sorted(folder.iterdir()) if p.is_file() and p.name != '.lock'
        }
        runs.append(entry)
    report = {
        'binary_sha256': binary,
        'all_recorded_runs_passed': all(r['result']['passed'] for r in runs),
        'passed_run_count': sum(r['result']['passed'] for r in runs),
        'failed_run_count': sum(not r['result']['passed'] for r in runs),
        'runs': runs,
        'scope': [
            'Actual source-built DOS terminal, UART and DOS files against local BBS protocol helpers.',
            'Loopback synthetic accounts/media; Hayes/Telnet modem and hardware are emulated.',
            'Protocol results do not establish editor compatibility or a complete PCPlus application.',
            'XMODEM has no original-length metadata; accepted padding remains in downloaded/uploaded files.',
            'Failed attempts remain distinct from successful retries.',
        ],
    }
    setups = {
        'synchronet': ROOT / 'build/bbs-lab/synchronet/transfers/setup.json',
        'enigma': ROOT / 'build/bbs-lab/results/enigma/transfers/setup.json',
    }
    setup_keys = (
        'server_commit', 'helpers', 'helper_original_sha256',
        'helper_patched_sha256', 'helper_manifest', 'loader',
        'file_ini_before_sha256', 'file_ini_after_sha256',
        'config_before_sha256', 'config_after_sha256',
        'existing_configuration_prefix_unchanged', 'appended_directory',
        'payload', 'area', 'file_bytes', 'file_sha256',
    )
    report['server_setup'] = {}
    for server in sorted({r['server'] for r in runs}):
        path = setups[server]
        setup = json.loads(path.read_text())
        report['server_setup'][server] = {
            'retained_setup_sha256': digest(path),
            **{key: setup[key] for key in setup_keys if key in setup},
        }
    output = (ROOT / args.output).resolve()
    assert output.parent == ROOT / 'docs/validation'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(output.relative_to(ROOT)), 'runs': len(runs),
                      'all_recorded_runs_passed': report['all_recorded_runs_passed']}))


if __name__ == '__main__':
    main()
