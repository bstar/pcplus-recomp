#!/usr/bin/env python3
"""Record explicit keymap comparison separately from default compatibility."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enigma', required=True)
    parser.add_argument('--network', required=True)
    args = parser.parse_args()
    runs = {}
    for profile, label in [('enigma-editor', args.enigma), ('network', args.network)]:
        assert label and all(c.isalnum() or c in '-_' for c in label)
        folder = ROOT/'build/bbs-lab/results/enigma'/label
        experiment = read(folder/'keymap-experiment.json')
        result = read(folder/'result.json')
        audit = read(folder/'semantic-audit.json')
        modem = read(folder/'modem.json')
        assert experiment['profile'] == audit['keyboard_profile'] == profile
        assert experiment['source_sha256'] == {p: sha(ROOT/p) for p in experiment['source_sha256']}
        assert experiment['binary_sha256'] == result['binary_sha256'] == audit['binary_sha256']
        assert experiment['kbd_sha256'] == result['keyboard_profile']['sha256'] == sha(folder/'BOARD.KBD')
        assert result['passed'] and audit['checks']['stock_editor_entered'] and audit['checks']['no_post_saved']
        assert modem['packet_delay_ms'] == result['modem_packet_delay_ms'] == audit['modem_packet_delay_ms'] == 0
        assert all(audit['observed_key_wire'].values())
        runs[profile] = dict(label=label, experiment=experiment, configuration=result['configuration'],
                             keyboard=result['keyboard'], serial=result['serial'], semantic_evidence=audit,
                             retained_artifacts={str(p.relative_to(ROOT)): sha(p) for p in sorted(folder.iterdir()) if p.is_file()})
    enigma, network = runs['enigma-editor'], runs['network']
    for key in ['configuration', 'keyboard', 'serial']:
        assert enigma[key] == network[key], key
    for key in ['binary_sha256', 'server_commit', 'server_source_sha256']:
        assert enigma['experiment'][key] == network['experiment'][key], key
    common = []
    for run in [enigma, network]:
        common.append({p: h for p, h in run['experiment']['source_sha256'].items()
                       if not p.startswith('build/keyboard-profiles/')})
    assert common[0] == common[1]
    # Bind the paired experiment to exactly six whole-slot overrides per block,
    # with every other native field/padding byte identical.
    base = (ROOT/'build/bbs-lab/results/enigma'/args.network/'BOARD.KBD').read_bytes()
    changed = bytearray(base)
    for profile in range(7):
        for slot, value in [(8,22), (54,22), (56,1), (76,1), (57,5), (77,5)]:
            at = profile*948+slot*12
            changed[at:at+12] = bytes([value])+bytes(11)
    assert bytes(changed) == (ROOT/'build/bbs-lab/results/enigma'/args.enigma/'BOARD.KBD').read_bytes()
    source = ROOT/'build/bbs-lab/enigma/source'
    conflict_sources = {}
    for name in ['core/fse.js', 'core/view_controller.js',
                 'misc/menu_templates/message_base.in.hjson']:
        data = (source/name).read_bytes()
        assert data == subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=source)
        conflict_sources[name] = sha(source/name)
    assert (source/'config/menus/loc-message_base.hjson').read_bytes() == (source/'misc/menu_templates/message_base.in.hjson').read_bytes()
    result = dict(recorded=True, binary_sha256=enigma['experiment']['binary_sha256'],
                  opt_in_editor_passed=enigma['experiment']['editor_passed'],
                  network_editor_passed=network['experiment']['editor_passed'], runs=runs,
                  static_conflict_evidence=dict(sources=conflict_sources,
                    installed_menu_matches_stock_template=True,
                    observation='Multi-line view offers Ctrl-A for Home, but stock compose form maps Ctrl-A to editModeChangeSubject. That action focuses the subject field before the body view handles the key. Candidate wire sends 01; its captured body cursor updates stop after ABCDE. This supports the focus-conflict explanation; no runtime server breakpoint or trace of view dispatch was used.'),
                  scope='Paired actual DOS/stock loopback ENiGMA unsaved-editor comparison. Same physical keys, binary, source, PRM, serial settings and immediate byte-transparent modem; only explicit KBD bytes differ. Home/End/Insert use stock editor control aliases in the opt-in map. Server/user state was not reset. Default-key compatibility aggregate remains separate and unchanged; no universal BBS, multiline, other-menu or physical modem claim.')
    target = ROOT/'docs/validation/bbs-enigma-keymap.json'
    if target.exists():
        old = read(target)
        history = old.pop('prior_experiments', [])
        if {p: r['label'] for p, r in old['runs'].items()} != {p: r['label'] for p, r in runs.items()}:
            history.append(old)
        if history:
            result['prior_experiments'] = history
    target.write_text(json.dumps(result, indent=2)+'\n')
    print('Recorded opt-in editor:', result['opt_in_editor_passed'],
          'network:', result['network_editor_passed'])


if __name__ == '__main__':
    main()
