#!/usr/bin/env python3
"""Verify the complete shared Meta connection-test package and source export."""
import json
from package_connection_test import ROOT, sha


def main():
    receipts, sources = {}, {}

    def read(name):
        path = ROOT / name
        result = json.loads(path.read_text())
        assert result['passed'], name
        receipts[name] = sha(path)
        for source, expected in result.get('sources', {}).items():
            assert sha(ROOT / source) == expected, source
            assert source not in sources or sources[source] == expected
            sources[source] = expected
        return result

    base = 'build/meta-shared-connection-candidate-20261107'
    result = read(base + '/result.json')
    recipe_path = ROOT / 'standalone/meta_shared_connection_candidate_recipe.json'
    recipe = json.loads(recipe_path.read_text())
    assert result['recipe_sha256'] == sha(recipe_path)
    manifest = json.loads((ROOT / base / 'package/manifest.json').read_text())
    assert manifest['files'] == result['files'] == recipe['expected_files'] and len(manifest['files']) == 15
    assert manifest['experimental_meta_shared_runtime'] and manifest['experimental_meta_editor_module']
    assert manifest['experimental_line_port_overlay'] and manifest['parent_render_capability'] == 20
    assert manifest['original_inputs'] == [] and not manifest['card_written']
    for name, expected in manifest['files'].items():
        path = ROOT / base / 'package/PCPLUS' / name
        assert sha(path) == expected, name
        receipts[str(path.relative_to(ROOT))] = expected
    archive = read(base + '/archive/result.json')
    assert archive['archive_sha256'] == result['archive_sha256'] == recipe['expected_archive_sha256']
    assert sha(ROOT / base / 'archive/PCPLUSSE.ZIP') == archive['archive_sha256']
    contracts = {}
    for module, count in (('meta', 17), ('line', 14)):
        path = f'build/meta-shared-package-{module}-contract-final-20261107/result.json'
        contract = read(path)
        assert contract['module'] == module and len(contract['cases']) == count
        if module == 'meta':
            assert contract['package_manifest_sha256'] == sha(ROOT / base / 'package/manifest.json')
            assert contract['terminal_sha256'] == manifest['files']['TERMINAL.EXE']
            assert contract['overlay_sha256'] == manifest['files']['PCMETA.OVL']
        contracts[module] = count
    modes = {}
    for mode in ('precompile', 'setup', 'splash', 'chat-help', 'line-port', 'meta-editor'):
        folder = ROOT / f'build/meta-shared-package-{mode}-final-20261107'
        case = read(str((folder / 'result.json').relative_to(ROOT)))
        assert case['package_files'] == manifest['files']
        assert case['package_manifest_sha256'] == sha(ROOT / base / 'package/manifest.json')
        assert case['cpu'] == '8086' and case['port'] == 3 and case['irq'] == 5
        assert len(case['private_fixture_sha256']) == 6
        if mode == 'meta-editor':assert case['meta_editor']
        if mode == 'line-port':assert case['native_line_port']
        if mode == 'chat-help':assert case['chat_help']
        if mode == 'precompile':
            assert case['bios_port_omitted'] and case['packaged_ASPECT_EMULATE_exercised'] and case['packaged_ASPECT_clock_alarm_exercised']
        for name, expected in case['artifacts'].items():
            assert sha(folder / name) == expected, name
        modes[mode] = case['checks']
    cold = read('build/meta-shared-connection-public-source-20261107/result.json')
    assert cold['files'] == manifest['files'] and cold['archive_sha256'] == result['archive_sha256']
    assert cold['ancestor_git_unavailable'] and cold['original_inputs'] == []
    control = read('build/meta-shared-line-control-candidate-20261107/result.json')
    old = json.loads((ROOT / 'standalone/line_port_connection_candidate_recipe.json').read_text())
    assert control['files'] == old['expected_files'] and len(control['files']) == 14
    assert control['archive_sha256'] == old['expected_archive_sha256']
    historical = {}
    for name in ('runtime', 'faults', 'transfers', 'carrier', 'enigma-transfers'):
        path = ROOT / f'docs/validation/meta-shared-{name}.json'
        checkpoint = json.loads(path.read_text())
        assert checkpoint['checkpoint_verified'] and not checkpoint['physical_verified']
        parent = checkpoint.get('parent_sha256', checkpoint.get('products', {}).get('TERMINAL.EXE'))
        assert parent == manifest['files']['TERMINAL.EXE']
        for leaf, expected in checkpoint.get('products', checkpoint.get('product_hashes', {})).items():
            assert manifest['files'][leaf] == expected, leaf
        historical[str(path.relative_to(ROOT))] = sha(path)
    for name in ('standalone/record_meta_shared_connection_candidate.py', 'docs/META_SHARED_CONNECTION_CANDIDATE.md'):
        sources[name] = sha(ROOT / name)
    report = dict(passed=True, software_package_verified=True, physical_runtime_verified=False,
                  files=manifest['files'], archive_sha256=result['archive_sha256'],
                  source_base_commit=result['source_base_commit'], source_export_commit=cold['source_commit'],
                  public_source_files=cold['source_count'], contracts=contracts, DOS_modes=modes,
                  previous_14_file_archive_reproduced=True, sources=sources, receipts=receipts,
                  identical_product_historical_checkpoints=historical, original_inputs=[],
                  limitations=[
                      'Public source export reproduces all15files and deterministic ZIP without originals/private files/prior objects/ancestor Git.',
                      'Six actualDOS8086 package workflows use dummy UARTs and six synthetic configuration/history sentinels.',
                      'Earlier core/BBS receipts apply to identical product hashes; their source snapshots remain historical.',
                      'This software receipt does not establish deployment or physical modem/CTS/SIP/audio acceptance or full original parity.'])
    output = ROOT / 'docs/validation/meta-shared-connection-candidate.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified shared Meta package:15files,31contract cases,6DOS modes,', cold['source_count'], 'public source files')


if __name__ == '__main__':
    main()
