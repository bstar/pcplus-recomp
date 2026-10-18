#!/usr/bin/env python3
"""Explicit opt-in KBD experiment against the owned stock unsaved editor."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['network', 'enigma-editor'], required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    out = ROOT/'build/bbs-lab/results/enigma'/args.label
    assert not out.exists(), 'Preserve earlier runs; choose a new label'
    recipe_path = ROOT/'lab/bbs/editor-recipes.json'
    recipe = json.loads(recipe_path.read_text())['enigma_unsaved']['keyboard_input']
    assert recipe.endswith('U N S A V E D p3000 a-x')
    assert 'enter' not in recipe[recipe.index('A B C D E'):].split()
    binary = ROOT/'build/terminal/TERMINAL.EXE'
    kbd = ROOT/'build/keyboard-profiles'/('ENIGMA.KBD' if args.profile=='enigma-editor' else 'NETWORK.KBD')
    assert kbd.is_file(), 'Build keyboard-profiles first'
    source = ROOT/'build/bbs-lab/enigma/source'
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    assert commit == '6c25317168b762f7d9088a54d3f8295438827a0e'
    server_sources = {}
    for name in ['core/client.js', 'core/multi_line_edit_text_view.js']:
        original = subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=source)
        assert (source/name).read_bytes() == original, 'Stock server input/editor required'
        server_sources[name] = sha(source/name)
    inputs = [binary, kbd, recipe_path, Path(__file__).resolve()]
    inputs += [ROOT/p for p in ['lab/bbs/test_dos.py', 'lab/bbs/check_editor_dos.py',
                               'lab/bbs/editor_dos_probe.py', 'lab/bbs/modem.py',
                               'standalone/build_keyboard_profiles.py',
                               'src/terminal/key_configuration.asm']]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    command = [sys.executable, str(ROOT/'lab/bbs/editor_dos_probe.py'), str(binary),
               'enigma', '--port', '23233', '--label', args.label, '--com', '2',
               '--baud', '19200', '--flow', 'HARD', '--dial-fixture',
               '--packet-delay-ms', '0', '--timeout', '160', '--wait', '2',
               '--keymap-fixture', str(kbd), '--keys', recipe]
    out.mkdir(parents=True)
    with (out/'harness.log').open('w') as log:
        subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    audit_command = [sys.executable, str(ROOT/'lab/bbs/check_editor_dos.py'), 'enigma',
                     '--label', args.label, '--disconnect-unsaved',
                     '--keyboard-profile', args.profile]
    with (out/'audit.log').open('w') as log:
        code = subprocess.call(audit_command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    assert hashes == {str(p.relative_to(ROOT)): sha(p) for p in inputs}, 'Inputs changed during run'
    run = json.loads((out/'result.json').read_text())
    audit = json.loads((out/'semantic-audit.json').read_text())
    assert run['passed'] and audit['checks']['stock_editor_entered']
    assert audit['checks']['no_post_saved'], 'Unexpected saved message'
    result = dict(profile=args.profile, binary_sha256=sha(binary), source_sha256=hashes,
                  server_commit=commit, server_source_sha256=server_sources,
                  kbd_sha256=sha(kbd), modem_packet_delay_ms=0,
                  DOS_harness_passed=run['passed'], editor_passed=audit['passed'],
                  audit_exit_code=code, checks=audit['checks'], observed_key_wire=audit['observed_key_wire'],
                  scope='Actual source-built DOS terminal, explicit source-owned KBD and immediate byte-transparent modeled modem against stock loopback ENiGMA. Home/End/Insert use editor-specific controls only in the opt-in profile. Same physical-key recipe; closes without posting. This is separate from default-key/buffering aggregates and does not prove other menus, boards or physical modem behavior.')
    (out/'keymap-experiment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
