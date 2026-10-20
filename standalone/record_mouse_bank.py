#!/usr/bin/env python3
"""Bind CRT-free bank/allocator evidence and preserved application identities."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
from build_native_mouse import ROOT, sha


def read(path):
    return json.loads(path.read_text())


def current(sources, frozen=None):
    for name, digest in sources.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(ROOT / name) == digest, name
        if frozen:
            assert sha(frozen / name) == digest, name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for variant in ('crt', 'dos', 'bank'):
        parser.add_argument('--' + variant + '-run', required=True)
        parser.add_argument('--' + variant + '-source', required=True)
    parser.add_argument('--application-source', required=True)
    parser.add_argument('--application-mouse-source', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for value in vars(args).values():
        if isinstance(value, str):
            assert re.fullmatch(r'[A-Za-z0-9_-]+', value)
    variants, evidence = {}, []
    for name, subdir, executable, cases, assertions in (
            ('crt', 'mouse-keyboard', 'MOUSEKEY.EXE', 76, 42),
            ('dos', 'mouse-keyboard-dos', 'MOUSEKEY.EXE', 84, 42),
            ('bank', 'mouse-bank', 'MOUSEBNK.EXE', 84, 46)):
        folder = ROOT / 'build' / subdir
        manifest = read(folder / 'manifest.json')
        current(manifest['sources'])
        binary = sha(folder / executable)
        assert manifest['binary_sha256'] == binary and manifest['original_inputs'] == []
        model = read(folder / 'checks.json')
        assert model['passed'] and len(model['cases']) == cases and all(c['passed'] for c in model['cases'])
        assert model['binary_sha256'] == binary
        assert model['checker_sha256'] == sha(ROOT / 'standalone/check_mouse_keyboard.py')
        run_dir = folder / 'runs' / getattr(args, name + '_run')
        run = read(run_dir / 'result.json')
        assert run['passed'] and all(run['checks'].values()) and run['binary_sha256'] == binary
        assert run['actual_DOS_assertions'] == assertions and run['actual_driver_state_bytes'] == 576
        assert run['checker_sha256'] == sha(ROOT / 'standalone/test_mouse_keyboard_dos.py')
        assert read(run_dir / 'manifest.json') == manifest
        assert all(sha(run_dir / p) == digest for p, digest in run['artifacts'].items())
        proof_dir = folder / 'source-proofs' / getattr(args, name + '_source')
        proof = read(proof_dir / 'result.json')
        assert proof['passed'] and proof['exit_code'] == 0 and proof['original_inputs'] == []
        assert proof['checker_sha256'] == sha(ROOT / 'standalone/check_mouse_keyboard_source.py')
        assert proof['log_sha256'] == sha(proof_dir / 'build.log')
        current(proof['sources'], proof_dir / 'source')
        assert len(proof['products']) == 3
        for product, pair in proof['products'].items():
            assert pair['expected'] == pair['actual'] == sha(folder / product)
            assert pair['actual'] == sha(proof_dir / 'source/build' / subdir / product)
        variants[name] = dict(binary_sha256=binary, linked_cases=cases,
            actual_DOS_assertions=assertions, actual_driver_state_bytes=576,
            products=proof['products'], source_hashes=manifest['sources'])
        evidence += [folder / 'manifest.json', folder / 'checks.json', run_dir / 'result.json',
                     proof_dir / 'result.json', proof_dir / 'build.log']
        if name == 'bank':
            assert manifest['bank'] and manifest['CRT_libraries'] == []
            assert all(n.startswith('_mouse_') or n == '_small_code_' for n in manifest['owner_imports'])
            assert 'library ' not in (folder / 'link.lnk').read_text()
            assert 'option nodefaultlibs' in (folder / 'link.lnk').read_text()
            assert len(model['bank_execution_entries']) == 11
            variants[name].update(segments=manifest['segments'],
                retained_paragraphs=manifest['retained_paragraphs'],
                bank_execution_entries=model['bank_execution_entries'],
                owner_imports=manifest['owner_imports'], CRT_libraries=[])
            evidence += [folder / 'MOUSEBNK.map', folder / 'link.lnk']
    app_dir = ROOT / ('build/aspect-unwind-mouse/source-proofs' if args.application_mouse_source else 'build/aspect-unwind/source-proofs') / args.application_source
    application = read(app_dir / 'result.json')
    preceding = read(ROOT / 'docs/validation/aspect-unwind.json')
    assert application['passed'] and application['original_inputs'] == [] and len(application['products']) == (29 if args.application_mouse_source else 27)
    assert application['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_unwind_source.py')
    assert application['log_sha256'] == sha(app_dir / 'build.log')
    current(application['sources'], app_dir / 'source')
    normal_products={p:v for p,v in application['products'].items() if not p.startswith(('terminal-mouse/', 'terminal-mouse-process/'))}
    assert len(normal_products)==27
    for name, pair in normal_products.items():
        assert pair['actual'] == pair['expected'] == preceding['products'][name]['actual']
        assert pair['actual'] == sha(ROOT / 'build' / name) == sha(app_dir / 'source/build' / name)
    evidence += [app_dir / 'result.json', app_dir / 'build.log', ROOT / 'docs/validation/aspect-unwind.json']
    report = dict(date=date.today().isoformat(), passed=True, component_only=True,
        normal_mouse_enabled=False, whole_application_gates_closed=[], original_build_inputs=[],
        variants=variants, linked_policy_cases=244, actual_DOS_assertions=130,
        native_code_and_guard_bytes=599, original_default_table_bytes=30,
        preserved_application_products={p:v['actual'] for p,v in normal_products.items()},
        prior_161_DOS_cases_carried_by_unchanged_binary_identity=True,
        evidence=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p)) for p in evidence],
        nix_inputs={p:sha(ROOT / p) for p in ('nix/flake.nix', 'nix/flake.lock')},
        recorder_sha256=sha(Path(__file__)),
        limitations=['Normal builds keep mouse disabled; selectable terminal integration has separate acceptance.',
                     'Changed INT33 quarantine is repaired explicitly by the diagnostic before termination.',
                     'Events are injected through the native foreign-DS/SS callback; physical input and other DOS kernels remain untested.',
                     'The CRT-free host deliberately contains 60000 bytes of near-code padding to force a different mouse-bank CS.',
                     'The live ENiGMA decoder remains unchanged; no whole-application gate closes.'])
    with args.output.open('x') as output:
        output.write(json.dumps(report, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
