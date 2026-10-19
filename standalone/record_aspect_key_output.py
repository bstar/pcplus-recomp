#!/usr/bin/env python3
"""Bind the shared keyboard checkpoint without closing whole-application gates."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    terminal = sha('build/terminal/TERMINAL.EXE')
    runner = sha('build/aspect-runner/ASPECT.EXE')
    compiler = sha('build/aspect-compiler-dos/ASPCOMP.EXE')
    specifications = [
        ('build/terminal-key-output/checks.json', 'standalone/check_terminal_key_output.py', 'binary_sha256', terminal),
        ('build/terminal-key-output/edit-checks.json', 'standalone/check_terminal_key_edit.py', 'binary_sha256', terminal),
        ('build/terminal-key-output/native-echo.json', 'standalone/check_keyboard_echo_native.py', None, None),
        ('build/aspect-keyboard/key-client-checks.json', 'standalone/check_aspect_key_client.py', 'runner_sha256', runner),
        ('build/aspect-keys-dos/half-edit-01/checks.json', 'standalone/test_aspect_keys_dos.py', 'runner_sha256', runner),
        ('build/aspect-keyboard/checks.json', 'standalone/check_aspect_keyboard.py', 'runner_sha256', runner),
        ('build/aspect-source-compile/checks.json', 'standalone/check_aspect_source_compile.py', 'runner_sha256', runner),
        ('build/aspect-source-serial-dos/checks.json', 'standalone/check_aspect_source_serial_dos.py', 'runner_sha256', runner),
    ]
    reports = []
    for path, checker, binary_field, digest in specifications:
        data = json.loads((ROOT / path).read_text())
        assert data['passed'] and data['checker_sha256'] == sha(checker), path
        if binary_field:
            assert data[binary_field] == digest, path
        if 'terminal_sha256' in data:
            assert data['terminal_sha256'] == terminal
        if 'compiler_sha256' in data:
            assert data['compiler_sha256'] == compiler
        if isinstance(data.get('cases'), list):
            assert all(c.get('passed', True) and all(c.get('checks', {}).values()) for c in data['cases'])
        reports.append(dict(path=path, sha256=sha(path), checker_sha256=sha(checker),
            cases=len(data['cases']) if isinstance(data.get('cases'), list) else data.get('cases'),
            scope=data['scope']))
    proof_path = 'docs/validation/application-components-source-build.json'
    proof = json.loads((ROOT / proof_path).read_text())
    assert proof['passed'] and proof['output_count'] >= 153
    assert all(p['matches_workspace'] for p in proof['outputs'].values())
    for path, digest in [('terminal/TERMINAL.EXE', terminal), ('aspect-runner/ASPECT.EXE', runner),
                         ('aspect-compiler-dos/ASPCOMP.EXE', compiler)]:
        assert proof['outputs'][path]['sha256'] == digest
    package = json.loads((ROOT / 'build/dos-package/manifest.json').read_text())
    assert package['files']['TERMINAL.EXE'] == terminal
    assert package['files']['ASPECT.EXE'] == runner
    assert package['files']['ASPCOMP.EXE'] == compiler
    regressions = []
    for path, checker in [('build/terminal/character-edit-live-checks.json', 'standalone/check_character_edit_live.py'),
                          ('build/terminal-keys/result.json', 'standalone/test_terminal_keys.py')]:
        data = json.loads((ROOT / path).read_text())
        assert data['passed'] and data['binary_sha256'] == terminal
        assert all(c['passed'] for c in data['cases'])
        regressions.append(dict(path=path, sha256=sha(path), checker_sha256=sha(checker),
                                cases=len(data['cases']), scope=data['scope']))
    bbs = []
    sync_path = 'build/bbs-lab/script-login/half-edit-sync-01/checks.json'
    sync = json.loads((ROOT / sync_path).read_text())
    assert sync['passed'] and all(sync['checks'].values())
    assert sync['terminal_sha256'] == terminal and sync['runner_sha256'] == runner
    bbs.append(dict(server='stock Synchronet', path=sync_path, sha256=sha(sync_path), checks=sync['checks']))
    enigma_path = 'build/bbs-lab/results/enigma/half-edit-enigma-transfer-01-wrapper/experiment.json'
    enigma = json.loads((ROOT / enigma_path).read_text())
    assert enigma['passed'] and enigma['inputs_unchanged']
    assert enigma['input_hashes']['build/terminal/TERMINAL.EXE'] == terminal
    assert enigma['message_count_before'] == enigma['message_count_after']
    transfer_path = 'build/bbs-lab/results/enigma/half-edit-enigma-transfer-01/result.json'
    transfer = json.loads((ROOT / transfer_path).read_text())
    assert transfer['passed'] and all(transfer['checks'].values())
    assert transfer['binary_sha256'] == terminal
    bbs.append(dict(server='isolated patched ENiGMA', path=enigma_path, sha256=sha(enigma_path),
        checks=transfer['checks'], transfer_sha256=sha(transfer_path),
        scope='Immediate modeled modem, unsaved editor then exact ZMODEM transfer and file-list return. This is not the live LAN board or physical modem.'))
    result = dict(passed=True, renderer_capability=6, recorder_sha256=sha(Path(__file__).relative_to(ROOT)),
        terminal_sha256=terminal, runner_sha256=runner, compiler_sha256=compiler,
        reports=reports, regressions=regressions, BBS=bbs, reproduced_outputs=proof['output_count'], source_proof_sha256=sha(proof_path),
        original_inputs=[], whole_application_gates_closed=[],
        retained_fixture_failures=[dict(label='shared-keys-02', reason='Cursor prediction omitted three displayed END characters.'),
                                  dict(label='shared-keys-04', reason='Enhanced Home was incorrectly expected to perform legacy Home echo; corrected fixture explicitly selects STANDARD BIOS.'),
                                  dict(label='half-edit-source-proof', reason='New55-case checker passed but could not write its report in a fresh checkout; corrected independent output-directory creation.')],
        limitations=['Local menus/macros/HOOK/PROGRAM and abort confirmation remain unfinished during scripts.',
                     'Half-duplex reverse-Tab still returns unsupported before output; Insert/Delete reject unsupported geometry/repair before output.',
                     'Original blocking pacing and complete status/selection post-actions remain unfinished.',
                     'Native echo services in the CPU oracle are explicit recording boundaries; real rendering is exercised separately in DOS.',
                     'Physical BIOS, UART and Wi-Fi modem remain unverified; no complete application or universal BBS compatibility claim.'])
    (ROOT / 'docs/validation/aspect-key-output.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f"Bound shared key output and {proof['output_count']} source-only products; no whole-application gates closed")


if __name__ == '__main__':
    main()
