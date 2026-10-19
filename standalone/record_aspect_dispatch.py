#!/usr/bin/env python3
"""Freeze sanitized dispatcher/oracle evidence; do not publish private artifacts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(rel):
    return json.loads((ROOT / rel).read_text())

def main():
    paths = ['build/aspect-dispatch/manifest.json', 'build/aspect-dispatch/checks.json',
             'build/aspect-dispatch/checks-native.json', 'analysis/aspect-vm/inventory-02.json',
             'analysis/aspect-vm-runtime/flow-01/result.json',
             'analysis/aspect-vm-runtime/false-01/result.json',
             'analysis/aspect-vm-runtime/header-02/report.json',
             'analysis/aspect-vm-runtime/header-03/report.json',
             'analysis/aspect-vm-runtime/keywords-02/inventory.json',
             'analysis/aspect-vm/rea-loader-dispatch-01.json']
    manifest, checks, native, inventory, flow, false, h2, h3, keywords, _ = [read(p) for p in paths]
    assert checks['passed'] and native['passed'] and inventory['passed']
    assert checks['original_inputs'] == [] and manifest['original_inputs'] == []
    assert checks['binary_sha256'] == manifest['binary_sha256'] == native['binary_sha256']
    assert checks['flat_sha256'] == native['flat_sha256'] == manifest['flat_sha256']
    assert checks['cpu_cases'] == native['optional_original']['paired_cpu_cases'] == 590
    assert native['optional_original']['exact_bytes'] == 224
    sources = {**manifest['sources'], 'standalone/check_aspect_dispatch.py': checks['check_sha256'],
               'standalone/inventory_aspect_vm.py': inventory['inventory_source_sha256'],
               'standalone/inventory_aspect_keywords.py': keywords['harness_sha256'],
               'standalone/aspect_vm_probe.py': flow['harness_sha256'],
               'standalone/aspect_header_probe.py': h3['harness_sha256']}
    for rel, digest in sources.items():
        assert sha(ROOT / rel) == digest, rel
    sources['standalone/record_aspect_dispatch.py'] = sha(Path(__file__).resolve())
    runtime = []
    for result in (flow, false):
        assert result['passed'] and all(result['checks'].values())
        assert result['harness_sha256'] == flow['harness_sha256']
        runtime.append({k: result[k] for k in ('case', 'checks', 'original_application_sha256',
                        'original_compiler_sha256', 'harness_sha256', 'source_sha256', 'asx_sha256',
                        'serial_sha256', 'returncode', 'timed_out', 'scope')})
    assert len(h2['cases']) == 114 and len(h3['cases']) == 6
    declarations = []
    for report in (h2, h3):
        declarations.append(dict(cases=len(report['cases']), accepted=sum(c['success'] for c in report['cases']),
            compiler_sha256=report['compiler_sha256'], historical_harness_sha256=report['harness_sha256'],
            scope=report['scope']))
    result = dict(passed=True, sources=sources, local_evidence={p: sha(ROOT/p) for p in paths},
        diagnostic=manifest, source_only_checks=checks, optional_native_comparison=native['optional_original'],
        dispatch_inventory={k: inventory[k] for k in ('original_sha256', 'dispatch_table', 'resident_handlers',
                           'overlay_handlers', 'overlay_handler_counts', 'scope')},
        original_runtime=runtime, original_compiler_declarations=declarations,
        compiler_keyword_inventory=dict(table_count=len(keywords['groups']), record_count=keywords['record_count'],
            command_records=keywords['command_summary']['records'],
            unique_command_tokens=keywords['command_summary']['unique_nonmarker_tokens'],
            limits=keywords['limits'], retained_rea_evidence=keywords['retained_rea_evidence']),
        limits=['Only the dispatch loop is reconstructed here; the diagnostic substitutes every backend callback.',
                'Original compiler/application runtime probes are baseline evidence, not maintained VM functionality.',
                'Compiler-only declaration probes do not establish runtime allocation or malformed-input safety.',
                'No full compiler, loader, VM, recorder, floating runtime or application script integration yet.'])
    out = ROOT/'docs/validation/aspect-dispatch.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(f'Recorded dispatcher and sanitized original-oracle evidence: {out.relative_to(ROOT)}')

if __name__ == '__main__':
    main()
