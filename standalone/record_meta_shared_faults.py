#!/usr/bin/env python3
"""Verify the shared-runtime fault checkpoint without granting release acceptance."""
import json
from pathlib import Path
from build_context_help import ROOT, sha


def main():
    receipts, sources = {}, {}
    parent = ROOT / 'build/meta-shared-help-seventh-20261107'
    digest = sha(parent / 'TERMINAL.EXE')

    def read(name):
        path = ROOT / name
        data = json.loads(path.read_text())
        assert data['passed'], name
        assert all(data.get('checks', {}).values()), name
        assert data.get('binary_sha256', data.get('parent_sha256')) == digest, name
        receipts[name] = sha(path)
        for source, expected in data.get('sources', {}).items():
            assert sha(ROOT / source) == expected, source
            assert source not in sources or sources[source] == expected
            sources[source] = expected
        for capture, expected in data.get('captures', {}).items():
            assert sha(ROOT / capture) == expected, capture
            receipts[capture] = expected
        return data

    arena = [read(f'build/meta-arena-{case}-final-20261107/result.json')
             for case in ('arena-cookie', 'history-return')]
    faults = ('fixup-outside', 'fixup-duplicate', 'fixup-overlap', 'fixup-order',
              'fixup-segment', 'header-magic', 'header-version', 'header-small',
              'header-large', 'header-count', 'header-data', 'header-arena')
    metadata = []
    for fault in faults:
        result = read(f'build/meta-metadata-{fault}-20261107/result.json')
        assert result['metadata_diagnostic'] and result['tested_parent_sha256'] != digest
        metadata.append(result)
    closes = []
    for module in ('line', 'meta'):
        for when in ('before', 'after'):
            result = read(f'build/meta-close-{module}-{when}-accepted-20261107/result.json')
            assert result['loader_state'][0] == 3 and result['loader_state'][6] == 1
            assert result['loader_state'][4] == 0
            assert result['fault_words'][2] == result['fault_words'][7] == 1
            closes.append(result)
    cold = read('build/meta-arena-source-current-20261107/result.json')
    assert cold['ancestor_git_unavailable'] and len(cold['runs']) == 4 and len(cold['meta_runs']) == 3
    products = {name: sha(parent / name) for name in ('TERMINAL.EXE', 'PCMETA.OVL', 'PCLINE.OVL')}
    assert cold['meta_overlay_sha256'] == products['PCMETA.OVL']
    assert cold['overlay_sha256'] == products['PCLINE.OVL']
    for name in ('standalone/record_meta_shared_faults.py', 'docs/META_SHARED_FAULTS.md'):
        sources[name] = sha(ROOT / name)
    report = dict(checkpoint_verified=True, release_eligible=False, installed_changed=False,
                  physical_verified=False, products=products, source_export_files=cold['source_count'],
                  arena_cases=arena, metadata_cases=metadata, close_cases=closes,
                  sources=sources, receipts=receipts, original_inputs=[],
                  limitations=[
                      'Emulated DOS8086 and synthetic UART peer; no physical acceptance.',
                      'Prior cookie observed before module loading; no stale-cookie application bug reproduced.',
                      'Metadata cases execute diagnostic copies with changed expected headers/CRC, not the unchanged release parent.',
                      'Close injection leaves fatal ownership until DOS exit14; later shutdown closes outside loader CS are recorded separately.',
                      'Exact-product reconnect, transfers, cancellation and carrier-loss acceptance remain open.'])
    output = ROOT / 'docs/validation/meta-shared-faults.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Verified: {len(arena)} arena/history, {len(metadata)} metadata/fixup, {len(closes)} close cases; {cold["source_count"]} source files; no deployment')


if __name__ == '__main__':
    main()
