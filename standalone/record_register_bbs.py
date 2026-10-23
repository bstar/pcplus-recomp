#!/usr/bin/env python3
"""Bind current ASIO-v7 editor outcomes separately from decoder replay evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab/bbs'))
from modem import Telnet


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sync-label', required=True)
    parser.add_argument('--enigma-buffered-label', required=True)
    parser.add_argument('--enigma-immediate-label', action='append', required=True)
    parser.add_argument('--decoder-replay', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    terminal = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers/TERMINAL.EXE'
    runner = ROOT / 'build/aspect-register-parent/ASPECT.EXE'
    for binary in [terminal, runner]:
        manifest = json.loads((binary.parent / 'manifest.json').read_text())
        assert manifest['experimental_register_handoff']
        assert not manifest.get('original_inputs') and sha(binary) == manifest['binary_sha256']
    sources = {}
    custody = {}
    cases = []
    server = ROOT / 'build/bbs-lab/enigma/source'
    server_sources = None
    server_revision = None
    assert len(args.enigma_immediate_label) >= 3 and len(set(args.enigma_immediate_label)) == len(args.enigma_immediate_label)
    specs = [('synchronet', args.sync_label, 0, True), ('enigma', args.enigma_buffered_label, 30, True)]
    specs += [('enigma', label, 0, None) for label in args.enigma_immediate_label]
    for name, label, delay, expected in specs:
        stage = ROOT / 'build/bbs-lab/script-login' / label
        output = ROOT / 'build/bbs-lab/results' / name / label
        assert stage.resolve().is_relative_to(ROOT / 'build/bbs-lab/script-login')
        assert output.resolve().is_relative_to(ROOT / 'build/bbs-lab/results' / name)
        report = json.loads((stage / 'checks.json').read_text())
        run = json.loads((output / 'result.json').read_text())
        audit = json.loads((output / 'semantic-audit.json').read_text())
        if expected is None:
            expected = report['passed']
            assert isinstance(expected, bool)
        assert report['terminal_sha256'] == run['binary_sha256'] == audit['binary_sha256'] == sha(terminal)
        assert report['runner_sha256'] == sha(runner)
        assert run['passed'] and all(run['checks'].values())
        assert report['passed'] is expected and audit['passed'] is expected
        assert report['checks']['resumed_parent_editor'] is expected
        assert all(value for key, value in report['checks'].items() if key != 'resumed_parent_editor')
        assert run['cpu'] == '8086' and 'cputype=8086' in (output / 'dosbox.conf').read_text()
        assert run['modem_packet_delay_ms'] == audit['modem_packet_delay_ms'] == delay
        assert run['server_endpoint'] == {'address': '127.0.0.1', 'port': 23231 if name == 'synchronet' else 23233}
        assert run['serial']['com'] == 2 and run['serial']['baud'] == 19200 and run['serial']['flow'] == 'HARD'
        assert audit['keyboard_profile'] == 'network' and all(audit['observed_key_wire'].values())
        assert audit['checks']['draft_aborted' if name == 'synchronet' else 'no_post_saved']
        if name == 'enigma':
            assert server_sources is None or report['server_sources'] == server_sources
            assert server_revision is None or report['server_commit'] == server_revision
            server_sources, server_revision = report['server_sources'], report['server_commit']
            for source, digest in server_sources.items():
                assert sha(server / source) == digest, source
        if expected:
            assert all(audit['checks'].values())
        else:
            assert not (audit['checks']['home_moves_before_marker'] and audit['checks']['insert_toggled_overtype'])
            assert all(value for key, value in audit['checks'].items()
                       if key not in ('home_moves_before_marker', 'insert_toggled_overtype'))
        wire, _ = Telnet().feed((output / 'bbs-sent.bin').read_bytes())
        credentials = b'LABUSER\rLABPASS42\r' if name == 'synchronet' else b'loclab\rLoC-Lab-2026!\r'
        assert wire.count(credentials) == 1
        assert sha(stage / 'TERMINAL.EXE') == sha(terminal) and sha(stage / 'ASPECT.EXE') == sha(runner)
        for source, digest in report['sources'].items():
            assert sha(ROOT / source) == digest, source
            assert source not in sources or sources[source] == digest, source
            sources[source] = digest
        for folder in [stage, output]:
            for artifact in folder.iterdir():
                if artifact.is_file():
                    custody[str(artifact.relative_to(ROOT))] = sha(artifact)
        cases.append(dict(server=name, label=label, packet_delay_ms=delay,
                          editor_passed=expected, checks=report['checks'], editor_checks=audit['checks'],
                          serial=run['serial'], cpu=run['cpu'], no_post_saved=True))
    replay_path = args.decoder_replay.resolve() / 'report.json'
    assert replay_path.is_relative_to(ROOT / 'build')
    replay = json.loads(replay_path.read_text())
    assert replay['passed']
    assert replay['stock_client_unchanged'] and replay['stock_client_sha256'] == server_sources['core/client.js']
    assert replay['upstream_revision'] == server_revision
    assert replay['nix_lock_sha256'] == sha(ROOT / 'nix/flake.lock')
    sources['nix/flake.lock'] = replay['nix_lock_sha256']
    assert replay['upstream_package_lock_sha256'] == sha(server / 'package-lock.json')
    for name, digest in replay['inputs'].items():
        source = 'lab/bbs/patches/enigma-key-stream/' + name
        assert sha(ROOT / source) == digest, name
        sources[source] = digest
    tests = {test['name']: test for test in replay['tests']}
    for name, test in tests.items():
        assert test['exit_code'] == 0
        assert sha(replay_path.parent / (name + '.log')) == test['log_sha256']
    stock = tests['stock-counterexample']['result']
    candidate = tests['candidate-client-editor']['result']
    assert stock['passed'] and not stock['fixed']
    assert stock['demonstrated_fragmentation_failures'] == 84 and stock['editor_fragmentation_failures'] == 9
    assert candidate['passed'] and candidate['fixed']
    assert candidate['demonstrated_fragmentation_failures'] == candidate['editor_fragmentation_failures'] == 0
    for artifact in replay_path.parent.iterdir():
        if artifact.is_file():
            custody[str(artifact.relative_to(ROOT))] = sha(artifact)
    decoder = dict(source_hashes=server_sources, tests=replay['tests'], passed=True,
                   scope='Isolated actual Client replay; a successful stock test reproduces the expected fragmentation defect, not stock correctness.')
    sources['standalone/record_register_bbs.py'] = sha(Path(__file__))
    sources['docs/REGISTER_BBS.md'] = sha(ROOT / 'docs/REGISTER_BBS.md')
    target = args.output.resolve()
    assert target.is_relative_to(ROOT / 'build') or target.is_relative_to(ROOT / 'docs/validation')
    target.parent.mkdir(parents=True, exist_ok=True)
    result = dict(compatibility_complete=False, outcomes_verified=True,
                  terminal_sha256=sha(terminal), runner_sha256=sha(runner),
                  cases=cases, sources=sources, custody_sha256=custody,
                  decoder_replay=decoder,
                  scope='Actual owned local DOSBox-X 8086 directory-script login, ASIO v7 return and stock '
                        'editor interaction. Actual immediate and 30ms buffering outcomes are recorded per case; '
                        'passing live editor runs do not establish arbitrary TCP-chunk correctness. Separate '
                        'isolated stock/candidate decoder replay checks that boundary. All emitted keys and '
                        'unsaved-draft outcomes checked. No server changes, physical modem, arbitrary-network, '
                        'HOOK or full-application acceptance.')
    target.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified', len(cases), 'BBS editor outcomes and separate decoder replay')


if __name__ == '__main__':
    main()
