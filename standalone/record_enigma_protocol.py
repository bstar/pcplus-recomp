#!/usr/bin/env python3
"""Bind owned ENiGMA navigation and download evidence to its custom selector."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab/bbs'))
from enigma_key_stream_fixture import owned
from enigma_search_fixture import parse


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--server-root', type=Path, required=True)
    p.add_argument('--search-label', required=True)
    p.add_argument('--transfer-label', required=True)
    a = p.parse_args()
    assert all(re.fullmatch(r'[A-Za-z0-9_-]+', s) for s in (a.search_label, a.transfer_label))
    candidate = owned(a.candidate)
    server = a.server_root.resolve()
    setup = read(candidate / 'search-instance.json')
    prepared = read(candidate.parent / 'report.json')
    assert prepared['passed'] and prepared['stock_client_unchanged']
    assert sha(server / 'core/client.js') == prepared['stock_client_sha256']
    assert prepared['nix_lock_sha256'] == sha(ROOT / 'nix/flake.lock')
    for name, digest in setup['source_inputs'].items():
        assert sha(server / name) == digest, name
    for name, digest in setup['source_modules'].items():
        assert sha(candidate / name) == digest, name
    for name, digest in setup['fixture_inputs'].items():
        assert sha(candidate / name) == digest, name
    assert len(setup['source_modules']) == 6
    menus = read(candidate / 'config/menus/loc-main.hjson')['menus']
    original = parse(candidate, server / 'config/menus/file_base.hjson')['menus']
    for name in setup['selected_menus']:
        assert menus[name] == original[name], name
    assert menus['fileTransferProtocolSelection']['module'] == '@userModule:loc_transfer_protocol_select'
    assert menus['locDownloadReady']['module'] == '@userModule:loc_download_ready'
    source_theme = parse(candidate, server / 'art/themes/black_flag/theme.hjson')
    staged_theme = parse(candidate, candidate / 'art/themes/luciano_blocktronics/theme.hjson')
    for name in setup['selected_theme']:
        assert staged_theme['customization']['menus'][name] == source_theme['customization']['menus'][name]
    selector_art = 'art/themes/black_flag/FPROSEL.ANS'
    assert sha(server / selector_art) == sha(candidate / 'art/themes/luciano_blocktronics/FPROSEL.ANS')

    terminal = sha(ROOT / 'build/terminal/TERMINAL.EXE')
    results = ROOT / 'build/bbs-lab/results/enigma'
    search_path = results / a.search_label / 'search-checks.json'
    transfer_path = results / (a.transfer_label + '-wrapper') / 'characterization.json'
    query_path = candidate.parent / 'search-query-checks.json'
    search, transfer, queries = map(read, (search_path, transfer_path, query_path))
    assert queries['passed'] and queries['checks'] == 11
    assert queries['checker_sha256'] == sha(ROOT / 'lab/bbs/check_enigma_search.js')
    assert queries['search_sha256'] == setup['source_modules']['mods/black_flag_files/search.js']
    assert queries['file_entry_sha256'] == sha(server / 'core/file_entry.js')
    assert search['passed'] and all(search['checks'].values())
    assert search['source_inputs'] == setup['source_inputs']
    assert search['source_modules'] == setup['source_modules']
    assert search['runner_sha256'] == sha(ROOT / 'lab/bbs/enigma_search_dos.py')
    assert search['fixture_sha256'] == sha(ROOT / 'lab/bbs/enigma_search_fixture.py')
    assert transfer['passed'] and transfer['transfer_passed'] and transfer['harness_exit'] == 0
    assert all(transfer['protocol_checks'].values()) and not transfer['protocol_errors']
    assert transfer['inputs_unchanged'] and transfer['no_post_saved']
    assert transfer['runner_sha256'] == sha(ROOT / 'lab/bbs/enigma_game_transfer_dos.py')
    assert search['terminal_sha256'] == transfer['terminal_sha256'] == terminal
    for name, digest in setup['source_modules'].items():
        assert transfer['input_hashes'][name] == digest, name
    archive = setup['archives'][1]
    source = candidate / 'file_base/pcplus_games' / archive['name']
    received = results / a.transfer_label / 'RECV' / transfer['expected_local_name']
    assert sha(source) == sha(received) == archive['sha256']
    assert source.stat().st_size == received.stat().st_size == archive['bytes']
    report = dict(
        passed=True, compatibility_complete=False, live_server_modified=False,
        terminal_sha256=terminal, owned_upstream_revision=prepared['upstream_revision'],
        live_client_sha256=prepared['stock_client_sha256'],
        staged_client_sha256=prepared['candidate_client_sha256'],
        source_modules=setup['source_modules'], selected_menus=setup['selected_menus'],
        selected_theme=setup['selected_theme'], selector_art_sha256=sha(server / selector_art),
        synthetic_archives=len(setup['archives']), query_checks=queries['checks'],
        navigation_checks=search['checks'], transfer_checks=transfer['protocol_checks'],
        archive=dict(wire_name=archive['name'], local_name=received.name,
                     bytes=archive['bytes'], sha256=archive['sha256']),
        evidence={str(path.relative_to(ROOT)): sha(path) for path in
                  (candidate.parent / 'report.json', candidate / 'search-instance.json',
                   search_path, transfer_path, query_path)},
        nix_lock_sha256=sha(ROOT / 'nix/flake.lock'), recorder_sha256=sha(Path(__file__)),
        scope='Actual DOS immediate modem through six exact owned modules and selected menus; generated ZIP/DIZ/NFO data and isolated patched decoder. Custom terminal protocol selector, ZMODEM and return to NFO verified. HTTP/browser branch, live catalog, physical modem and whole-application completion remain unverified.',
        whole_application_gates_closed=[])
    output = ROOT / 'docs/validation/enigma-protocol-selector.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(output)


if __name__ == '__main__':
    main()
