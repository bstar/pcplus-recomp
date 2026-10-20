"""Publish scoped network-fragmentation, live editor and transfer evidence."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('network-label', 'editor-label', 'transfer-label', 'candidate-editor-label'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for label in (args.network_label, args.editor_label, args.transfer_label, args.candidate_editor_label):
        assert re.fullmatch(r'[A-Za-z0-9_-]+', label)
    base = ROOT / 'build/bbs-lab/results'
    paths = [base / 'enigma' / args.network_label / 'search-checks.json',
             base / 'enigma-owned' / args.editor_label / 'owned-server-checks.json',
             base / 'enigma' / (args.transfer_label + '-wrapper') / 'characterization.json']
    network, editor, transfer = [json.loads(p.read_text()) for p in paths]
    paths += [base / 'enigma' / (args.candidate_editor_label + '-wrapper') / 'experiment.json',
              base / 'enigma' / args.candidate_editor_label / 'semantic-audit.json']
    framed, framed_audit = [json.loads(p.read_text()) for p in paths[3:]]
    assert framed['passed'] and framed['mode'] == 'editor'
    assert framed['inputs_unchanged'] and framed['editor_audit_exit'] == 0
    assert framed['message_count_before'] == framed['message_count_after']
    assert framed_audit['passed'] and all(framed_audit['checks'].values())
    assert network['passed'] and all(network['checks'].values())
    assert network['network_experiment']['requested_byte_delay_ms'] == 20
    assert network['network_experiment']['byte_conservation']
    assert not network['network_experiment']['errors']
    inputs = network['input_hashes']
    assert inputs['runner'] == sha(ROOT / 'lab/bbs/enigma_search_dos.py')
    assert inputs['fragment_relay'] == sha(ROOT / 'lab/bbs/fragment_relay.py')
    for prefix, folder in [('candidate/', args.candidate), ('source_board/', args.server_root)]:
        for path, digest in inputs.items():
            if path.startswith(prefix):
                assert sha(folder / path[len(prefix):]) == digest, path
    assert editor['mode'] == 'editor'
    assert editor['passed'] == all(editor['checks'].values())
    assert all(sha(Path(p)) == h for p, h in editor['input_hashes'].items())
    for check in ('DOS_harness', 'authenticated_probe', 'main_menu',
                  'inputs_unchanged', 'no_post_saved', 'staged_products_unchanged',
                  'DOS_source_compiled', 'editor_entered'):
        assert editor['checks'][check], check
    assert transfer['passed'] and transfer['inputs_unchanged'] and transfer['no_post_saved']
    assert transfer['protocol_checks'] and all(transfer['protocol_checks'].values())
    terminal = sha(ROOT / 'build/terminal/TERMINAL.EXE')
    assert network['terminal_sha256'] == editor['binary_sha256'] == transfer['terminal_sha256'] == terminal
    assert framed_audit['binary_sha256'] == framed['input_hashes']['build/terminal/TERMINAL.EXE'] == terminal
    assert framed['input_hashes'][str(args.candidate.resolve().relative_to(ROOT) / 'core/client.js')] == inputs['candidate/core/client.js']
    report = dict(date=date.today().isoformat(), compatibility_complete=False,
                  live_server_modified=False, physical_modem_validated=False,
                  terminal_sha256=terminal,
                  isolated_navigation=dict(passed=network['passed'], checks=network['checks'],
                      network_experiment=network['network_experiment'], pages=network['pages'],
                      selected=network['selected'], route=network['route']),
                  live_editor=dict(passed=editor['passed'], checks=editor['checks']),
                  isolated_editor=dict(passed=framed_audit['passed'], checks=framed_audit['checks']),
                  isolated_download=dict(passed=transfer['passed'], checks=transfer['protocol_checks'],
                      archive_sha256=transfer['archive']['sha256'],
                      archive_bytes=transfer['archive']['bytes']),
                  source_hashes={**network['source_inputs'],
                      'core/client.js':inputs['source_board/core/client.js']},
                  candidate_decoder_hashes={p:inputs['candidate/' + p] for p in
                      ('core/client.js', 'core/key_stream.js')},
                  evidence=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in paths],
                  recorder_sha256=sha(Path(__file__)),
                  limitations=['Paced writes do not guarantee TCP receive-event boundaries.',
                               'The decoder candidate remains separate from the live board.',
                               'Downloads use a synthetic archive on the isolated board.',
                               'Physical modem, complete live editor/transfer/door acceptance remain open.'])
    with args.output.open('x') as output:
        output.write(json.dumps(report, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
