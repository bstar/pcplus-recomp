#!/usr/bin/env python3
"""Bind a stock Enigma navigation capture and controls to the packaged candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('capture', 'semantic-controls', 'screen-controls', 'legacy-controls', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    receipts = {}

    def read(path):
        path = path.resolve()
        assert path.is_relative_to(ROOT / 'build')
        result = json.loads(path.read_text())
        assert result['passed'], path
        receipts[str(path.relative_to(ROOT))] = sha(path)
        for key in ('sources', 'product_inputs', 'captures', 'original_captures'):
            for name, digest in result.get(key, {}).items():
                assert sha(ROOT / name) == digest, name
        return result

    producer = read(args.capture / 'proxy-integration.json')
    semantic = read(args.capture / 'semantic-audit.json')
    screen = read(args.capture / 'screen-reference-audit.json')
    for result in (producer, semantic, screen):
        assert all(result['checks'].values())
    detail = semantic['authority']['multiline']
    assert detail['mode'] == 'navigation'
    assert detail['actual_body'] == detail['expected_body']
    navigation = detail['navigation']
    assert navigation['actual_cursor_history'] == navigation['expected_cursor_history']
    assert screen['different_cells'] == 0 and screen['matched_cells'] == 1920
    assert semantic['authority']['stock_server'] and semantic['checks']['no_post_saved']
    package_path = ROOT / 'docs/validation/aspect-compiler-package.json'
    package = json.loads(package_path.read_text())
    assert package['checkpoint_verified']
    assert producer['binary_sha256'] == semantic['binary_sha256'] == screen['binary_sha256'] == package['files']['TERMINAL.EXE']
    receipts[str(package_path.relative_to(ROOT))] = sha(package_path)
    controls = []
    for folder, count in ((args.semantic_controls, 12), (args.screen_controls, 9), (args.legacy_controls, 6)):
        result = read(folder / 'result.json')
        assert len(result['cases']) == count
        assert all(row['passed'] and row['rejected'] == (row['case'] != 'unchanged') for row in result['cases'])
        controls.append(dict(path=str(folder.relative_to(ROOT) if folder.is_absolute() else folder), cases=result['cases']))
    sources = ['standalone/record_editor_navigation.py', 'lab/bbs/check_enigma_multiline_controls.py',
               'lab/bbs/enigma_multiline.py', 'lab/bbs/check_editor_dos.py',
               'lab/bbs/test_synthmodem_proxy_dos.py', 'lab/bbs/audit_screen_reference.py',
               'lab/bbs/check_screen_reference_controls.py', 'nix/flake.nix', 'nix/flake.lock']
    result = dict(checkpoint_verified=True, tool_source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        application_bytes_changed=False, installed_changed=False, selector_changed=False,
        physical_verified=False, package_files=package['files'],
        semantic_checks=semantic['checks'], navigation=navigation,
        final_body=detail['actual_body'], screen_checks=screen['checks'],
        matched_cells=1920, different_cells=0, CPR=screen['actual_CPR'],
        delivered_bytes=screen['delivered_bytes'], controls=controls, receipts=receipts,
        sources={name: sha(ROOT / name) for name in sources},
        scope='Actual DOS BIOS keys through SynthModem Telnet proxy into stock loopback Enigma unsaved editor. Default25-row/status-visible profile. No SIP/audio, physical CTS, every-profile or published-post acceptance.')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Verified navigation semantics,1920 cells,11 semantic/8 screen rejections and legacy controls')


if __name__ == '__main__':
    main()
