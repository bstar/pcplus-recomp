#!/usr/bin/env python3
"""Bind the batch-code migration to compiled input, DOS and fresh-build evidence."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = '245e681ae1cd142362d19cffd87f8538668f3d8e'
BASELINE_SHA = '4557259887c7d0f0a4a535b90e53a459077b414caf17e570edfd8e0ac77b942c'


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def verify_sources(report):
    for name, digest in report.get('sources', {}).items():
        assert sha(name) == digest, name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, help='Fresh independent DOS YMODEM run')
    args = parser.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    runtime = sha('build/terminal/TERMINAL.EXE')
    manifest = read('build/terminal/manifest.json')
    assert manifest['binary_sha256'] == runtime
    verify_sources(manifest)
    baseline_path = Path('build/checkpoints/4557')
    baseline = read(baseline_path / 'manifest.json')
    assert baseline['binary_sha256'] == sha(baseline_path / 'TERMINAL.EXE') == BASELINE_SHA
    published = json.loads(subprocess.check_output(
        ['git', 'show', BASELINE_COMMIT + ':docs/validation/terminal-source-build.json'], cwd=ROOT))
    assert published['manifest'] == baseline, 'Baseline manifest differs from the published checkpoint'
    for name, digest in baseline['sources'].items():
        original = subprocess.check_output(['git', 'show', BASELINE_COMMIT + ':' + name], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == digest, name
    # Placement and source-owned adapters change; the protocol and codec do not.
    for name in ['src/transfer/ymodem.c', 'src/transfer/batch_header.c']:
        assert manifest['sources'][name] == baseline['sources'][name]
    layout = manifest['memory_layout']
    old = baseline['memory_layout']
    assert layout['near_bytes'] == old['near_bytes'] == 64480
    assert layout['resident_code_bytes'] == 61970
    assert old['resident_code_bytes'] - layout['resident_code_bytes'] == 3328
    assert layout['resident_code_spare_bytes'] == 3566
    assert (layout['retained_parent_paragraphs'] - old['retained_parent_paragraphs']) * 16 == 464
    assert layout['ymodem_far_code_verified'] and layout['configuration_bridge_pairs_verified'] == 60
    assert layout['far_code_bridge_pairs_verified'] == 109
    artifacts = [Path('build/terminal/manifest.json'), baseline_path / 'manifest.json']
    checks = {}
    for name, path in [
        ('migration', 'build/terminal/ymodem-far-checks.json'),
        ('linked_engine', 'build/terminal/terminal-ymodem-live-checks.json'),
        ('frames', 'build/terminal/config-far-checks.json'),
        ('actual_DOS', f'build/terminal-ymodem-dos/{args.label}/checks.json'),
        ('DOS_retention', 'build/far-storage-dos/checks.json'),
        ('isolated_linked', 'build/application-source-proof/ymodem-far-linked-checks.json'),
    ]:
        checks[name] = read(path)
        assert checks[name]['passed'] and checks[name]['binary_sha256'] == runtime, name
        verify_sources(checks[name])
        artifacts.append(Path(path))
    assert checks['migration']['inputs'] == checks['isolated_linked']['inputs'] == 413
    assert checks['linked_engine']['inputs'] == 23
    assert len(checks['frames']['rejected_mutations']) == 269
    assert all(checks['DOS_retention']['checks'].values())
    dos = checks['actual_DOS']
    assert len(dos['cases']) == 30 and all(c['passed'] and all(c['checks'].values()) for c in dos['cases'])
    for folder in sorted((ROOT / 'build/terminal-ymodem-dos' / args.label).iterdir()):
        if folder.is_dir():
            artifacts.extend(p.relative_to(ROOT) for p in sorted(folder.rglob('*')) if p.is_file())
    imports = read('build/terminal/compiler-helper-adapters.json')
    assert imports['binary_sha256'] == runtime and imports['import_counts'] == {'__U4D': 2, '__U4M': 1}
    assert sha('build/terminal/batch-header-compiler.obj') == imports['compiler_object_sha256'] == checks['migration']['compiler_object_sha256']
    assert sha('build/terminal/batch_header.obj') == imports['normalized_object_sha256'] == checks['migration']['normalized_object_sha256']
    artifacts.extend(map(Path, ['build/terminal/compiler-helper-adapters.json', 'build/terminal/batch-header-compiler.obj',
                               'build/terminal/batch_header.obj', 'build/ymodem-far/compiler.asm', 'build/ymodem-far/normalized.asm']))
    regression = read('build/terminal/setup-profile-regression.json')
    commands = subprocess.check_output(['make', '-n', 'test-terminal'], cwd=ROOT, text=True).splitlines()
    assert len(commands) == 77 and regression['complete'] and regression['passed'] and regression['binary_sha256'] == runtime
    assert commands == [c['command'] for c in regression['commands']] and all(c['exit_code'] == 0 for c in regression['commands'])
    artifacts.append(Path('build/terminal/setup-profile-regression.json'))
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 64
    assert proof['outputs']['terminal/TERMINAL.EXE']['sha256'] == runtime and all(o['matches_workspace'] for o in proof['outputs'].values())
    sources = ['standalone/record_ymodem_far.py', 'standalone/check_ymodem_far_live.py', 'standalone/omf_imports.py',
               'standalone/build_terminal.py', 'standalone/terminal_memory.py', 'standalone/check_config_far_live.py',
               'standalone/test_terminal_ymodem_dos.py', 'standalone/test_far_storage_dos.py', 'src/terminal/config_abi.inc',
               'src/terminal/config_bridge.asm', 'src/terminal/config_far.asm']
    result = dict(passed=True, binary_sha256=runtime, memory_layout=layout,
                  baseline=dict(commit=BASELINE_COMMIT, binary_sha256=BASELINE_SHA, compiled_inputs_verified=len(baseline['sources']), memory_layout=old),
                  resident_code_bytes_freed=3328, retained_parent_bytes_added=464,
                  compiler_import_adapters=imports, checks=checks, terminal_regression=regression,
                  runtime_sources=manifest['sources'], sources={p: sha(p) for p in sources},
                  retained_artifacts={str(p): sha(p) for p in artifacts},
                  source_rebuild=dict(report='docs/validation/application-components-source-build.json', output_count=64,
                                      source_snapshot_sha256=proof['source_snapshot_sha256'], isolated_linked_inputs=413),
                  scope='Unchanged maintained YMODEM/metadata C in CONFIG_CODE with explicit four near entry pairs and eighteen resident callbacks. Compiler helper binding changes only freshly compiled global OMF import names and their record lengths/checksums, preserving code/data/fixups and external indices. Independent decimal/CRC peers, register/FLAGS/stack observations, malformed-image rejection, thirty actual DOS sessions and original-free isolated rebuilding are separate evidence. This frees resident code address space while increasing total retained parent memory by464 bytes; no protocol additions, complete application, other emulations or physical RS232/Wi-Fi compatibility claim.')
    (ROOT / 'docs/validation/ymodem-far-code.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded YMODEM far-code migration', runtime)


if __name__ == '__main__':
    main()
