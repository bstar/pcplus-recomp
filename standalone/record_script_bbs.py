#!/usr/bin/env python3
"""Bind actual script/editor outcomes without replacing failed modem trials."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    terminal = sha('build/terminal/TERMINAL.EXE')
    runner = sha('build/aspect-runner/ASPECT.EXE')
    cases = {}
    for name, label, filename, expected in (
        ('enigma', 'render-v4-dac-enigma-immediate', 'experiment.json', False),
        ('enigma', 'render-v4-dac-enigma-script02', 'checks.json', False),
        ('enigma', 'render-v4-dac-enigma-script-buffer30', 'checks.json', True),
        ('synchronet', 'render-v4-dac-sync', 'checks.json', True),
    ):
        folder = f'build/bbs-lab/results/{name}/{label}'
        path = (folder + '/' + filename if filename == 'experiment.json'
                else f'build/bbs-lab/script-login/{label}/{filename}')
        result = json.loads((ROOT / path).read_text())
        run_path = folder + '/result.json'
        audit_path = folder + '/semantic-audit.json'
        run = json.loads((ROOT / run_path).read_text())
        audit = json.loads((ROOT / audit_path).read_text())
        assert run['binary_sha256'] == audit['binary_sha256'] == terminal
        assert run['passed'] and audit['passed'] is expected
        assert audit['checks']['draft_aborted' if name == 'synchronet' else 'no_post_saved']
        assert all(audit['observed_key_wire'].values())
        if filename == 'checks.json':
            assert result['terminal_sha256'] == terminal and result['runner_sha256'] == runner
            assert result['passed'] is expected
            assert all(v for k, v in result['checks'].items() if k != 'resumed_parent_editor')
            assert result['checks']['resumed_parent_editor'] is expected
        if name == 'enigma' and not expected:
            assert not audit['checks']['home_moves_before_marker']
            assert not audit['checks']['insert_toggled_overtype']
        # The corrected buffering run binds the current complete probe source.
        # Earlier attempts retain their own exact sources and frozen hashes.
        if label.endswith('buffer30'):
            assert run['modem_packet_delay_ms'] == 30 and audit['keyboard_profile'] == 'network'
            for source, digest in result['sources'].items():
                assert sha(source) == digest, source
        if label.endswith('script02'):
            source_path = f'build/bbs-lab/script-login/{label}/probe-source.py'
            assert sha(source_path) == result['sources']['lab/bbs/enigma_directory_script_probe.py']
        cases[label] = dict(
            server=name, terminal_sha256=terminal,
            runner_sha256=result.get('runner_sha256'),
            automatic_script_login=filename == 'checks.json',
            editor_passed=audit['passed'], checks=audit['checks'],
            keyboard_profile=audit['keyboard_profile'],
            modem_packet_delay_ms=run.get('modem_packet_delay_ms', 0),
            workflow_checks=result.get('checks'),
            evidence={p: sha(p) for p in (path, run_path, audit_path)},
        )
    output = dict(
        current_terminal_sha256=terminal, current_runner_sha256=runner,
        recorder_sha256=sha('standalone/record_script_bbs.py'), cases=cases,
        scope='Actual local DOSBox-X script/editor evidence. Synchronet automatic login passes with immediate forwarding. Stock ENiGMA passes with explicit 30ms modem buffering and default network keys; immediate default-key and control-key runs retain editor failures. Owned local accounts, unsaved drafts, CTS held ready. No physical modem, arbitrary-network or full-application completion claim.',
    )
    target = ROOT / 'docs/validation/script-bbs.json'
    target.write_text(json.dumps(output, indent=2) + '\n')
    print('Recorded four script/editor outcomes, including two retained ENiGMA failures')


if __name__ == '__main__':
    main()
