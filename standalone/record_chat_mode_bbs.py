#!/usr/bin/env python3
"""Bind current Chat-mode payload to stock BBS transfers and exact modal screens."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipts = {}

    def read(name):
        path = ROOT / name
        result = json.loads(path.read_text())
        assert result['passed'], name
        receipts[name] = sha(path)
        for field in ('sources', 'captures', 'product_inputs', 'products', 'server_inputs'):
            for source, digest in result.get(field, {}).items():
                # Bare products are payload leaves, checked below; other
                # report bindings use paths relative to the workspace.
                if '/' in source:
                    assert sha(ROOT / source) == digest, source
        return result

    payload_dir = ROOT / 'build/chat-send-mode-bbs-payload-20261108'
    payload = read('build/chat-send-mode-bbs-payload-20261108/package.json')
    products = payload['products']
    assert len(products) == 9 and all(sha(payload_dir / name) == digest for name, digest in products.items())
    parent, module = products['TERMINAL.EXE'], products['PCCHAT.OVL']
    prior_path = ROOT / 'docs/validation/chat-send-mode-live.json'
    prior = json.loads(prior_path.read_text())
    assert prior['checkpoint_verified'] and prior['parent_sha256'] == parent and prior['module_sha256'] == module
    receipts[str(prior_path.relative_to(ROOT))] = sha(prior_path)
    proof = read('build/chat-mode-bbs-source-export-20261108/result.json')
    assert len(proof['sources']) == 1053 and proof['DOS_cases'] == 2
    assert proof['lab_payload']['products'] == products
    contract = read('build/chat-mode-bbs-contract-20261108/result.json')
    assert contract['products'] == products and all(contract['checks'].values())
    transfers = []
    for server, mode, label, size in [
        ('enigma', 'download', 'chat-mode-enigma-download-v2-20261108', 11521),
        ('enigma', 'upload', 'chat-mode-enigma-upload-20261108', 65539),
        ('synchronet', 'download', 'chat-mode-sync-download-20261108', 11521),
        ('synchronet', 'upload', 'chat-mode-sync-upload-20261108', 65539),
    ]:
        result = read('build/bbs-lab/' + label + '-transfer/result.json')
        native = read('build/bbs-lab/results/' + server + '/' + label + '/result.json')
        assert result['terminal_sha256'] == native['binary_sha256'] == parent
        assert native['cpu'] == '8086' and result['mode'] == mode and result['fixture']['bytes'] == size
        assert all(result['checks'].values()) and all(result['protocol_checks'].values()) and not result['protocol_errors']
        assert ('mount c "' + str(payload_dir) + '"') in (ROOT / 'build/bbs-lab/results' / server / label / 'dosbox.conf').read_text()
        for name, digest in result['proxy']['installed_sources'].items():
            assert sha(ROOT / 'build/compiler-bridge-current-proxy-20261108' / name) == digest
        transfers.append(dict(server=server, mode=mode, fixture=result['fixture'], checks=result['checks'],
                              protocol_checks=result['protocol_checks'], scope=native['scope']))
    screens = []
    for server, label, controls in [
        ('enigma', 'chat-mode-loc-main-20261108', 'chat-mode-loc-screen-controls-20261108'),
        ('enigma', 'chat-mode-enigma-chat-help-v2-20261108', 'chat-mode-enigma-screen-controls-20261108'),
        ('synchronet', 'chat-mode-sync-editor-20261108', 'chat-mode-sync-screen-controls-20261108'),
    ]:
        folder = 'build/bbs-lab/results/' + server + '/' + label
        result = read(folder + '/proxy-integration.json')
        cells = read(folder + '/screen-reference-audit.json')
        assert result['binary_sha256'] == cells['binary_sha256'] == parent
        assert all(result['checks'].values()) and all(cells['checks'].values())
        assert cells['matched_cells'] == 1920 and cells['different_cells'] == 0
        modal = None
        if 'loc-main' in label:
            modal = read(folder + '/loc-main-audit.json')
            modal_checks = dict(source_art=modal['matched_source_art_cells']==1906,
                                focused_field=modal['field_cells']==14 and modal['field_text']=='LOCSNAP',
                                native_reference=modal['native_reference_observed'],
                                native_labels=modal['all_39_native_labels'],
                                message_menu_return=modal['message_menu_return'])
        elif server == 'enigma':
            modal = read(folder + '/chat-help-audit.json')
            modal_checks = modal['checks']
            assert result['chat_help']['passed']
            semantic = read(folder + '/semantic-audit.json')
            assert all(semantic['checks'].values())
        else:
            modal = read(folder + '/keymap-audit.json')
            modal_checks = modal['checks']
            assert modal['help_roundtrip'] and modal['profiles']==7
            assert result['keymap']['passed']
            assert result['interpreter_sha256'] == products['ASPECT.EXE']
            assert (ROOT / folder / 'SCRIPT.OK').read_bytes() == b'PASS'
        assert all(modal_checks.values())
        negative = read('build/' + controls + '/result.json')
        assert len(negative['cases']) == 9 and all(row['passed'] and row['rejected'] == (row['case'] != 'unchanged') for row in negative['cases'])
        screens.append(dict(server=server, label=label, matched_cells=1920, different_cells=0,
                            CPR=cells['actual_CPR'], checks=result['checks'], modal_checks=modal_checks,
                            rejected_screen_controls=8, scope=modal['scope']))
    chat = []
    for label in ('chat-mode-text-regression-20261108', 'chat-mode-echo-regression-20261108'):
        result = read('build/' + label + '/result.json')
        assert result['binary_sha256'] == parent and result['module_sha256'] == module
        assert all(result['checks'].values())
        wire = (ROOT / result['capture'] / 'serial.bin').read_bytes()
        assert (ROOT / result['capture'] / 'TEST.PRM').read_bytes()[0x1f2] != 0
        if 'expected_TEXT_hex' in result:
            assert bytes.fromhex(result['expected_TEXT_hex']) in wire
        chat.append(dict(label=label, checks=result['checks'], scope=result['scope']))
    bundle = read('build/chat-mode-help-bundle-controls-20261108/result.json')
    assert len(bundle['cases']) == 6 and bundle['original_unchanged']
    assert all(row['passed'] and row['rejected'] == (row['case'] != 'unchanged') for row in bundle['cases'])
    source_names = ['standalone/record_chat_mode_bbs.py', 'standalone/test_chat_live_keys_dos.py',
                    'lab/bbs/chat_help_bbs_support.py', 'lab/bbs/check_chat_help_bundle_controls.py']
    result = dict(checkpoint_verified=True, tool_source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), products=products,
        transfers=transfers, screens=screens, native_Chat=chat, help_bundle_controls=bundle['cases'],
        source_export_files=1053, source_replayed_DOS_cases=2, receipts=receipts,
        sources={name: sha(ROOT / name) for name in source_names}, installed_changed=False,
        selector_changed=False, physical_verified=False, release_eligible=False,
        scope='Current opt-in Chat parent/API0107 module, matched9-file lab payload. Actual DOS8086 serial-side stock BBS transfers; selected25-row screens/modal return. Actual SynthModem Telnet proxy, synthetic Hayes, no SIP/DSP/audio or physical CTS. Separate copied LoC menu fixture; live board unchanged. No full archive or original feature parity claim.',
        excluded=['Initial Enigma download requested upload-only post-menu-reset and was rejected before connection.',
                  'Initial Chat/Help BBS fixture expected legacy mapped_contexts metadata absent from the complete9-file bundle; rejected before connection. Updated hashed-manifest/actual-context guard and5 negative controls precede accepted v2.'])
    (ROOT / 'docs/validation/chat-mode-bbs.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Verified4 stock transfers,3 exact1920-cell screens/24 rejections,Chat TEXT/echo and9-file source proof')


if __name__ == '__main__':
    main()
