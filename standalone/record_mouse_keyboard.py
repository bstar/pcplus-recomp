#!/usr/bin/env python3
"""Record bounded mouse/keyboard composition and preserved application identity."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
from build_mouse_keyboard import ROOT, OUT, sha


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
    parser.add_argument('--dos-label', required=True)
    parser.add_argument('--source-label', required=True)
    parser.add_argument('--application-source-label', required=True)
    args = parser.parse_args()
    for label in (args.dos_label, args.source_label, args.application_source_label):
        assert re.fullmatch(r'[A-Za-z0-9_-]+', label)
    manifest = read(OUT / 'manifest.json')
    assert manifest['original_inputs'] == []
    current(manifest['sources'])
    binary = sha(OUT / 'MOUSEKEY.EXE')
    assert manifest['binary_sha256'] == binary
    model = read(OUT / 'checks.json')
    assert model['passed'] and len(model['cases']) == 76 and all(c['passed'] for c in model['cases'])
    assert model['binary_sha256'] == binary and model['checker_sha256'] == sha(ROOT / 'standalone/check_mouse_keyboard.py')
    folder = OUT / 'runs' / args.dos_label
    run = read(folder / 'result.json')
    assert run['passed'] and all(run['checks'].values()) and run['binary_sha256'] == binary
    assert run['checker_sha256'] == sha(ROOT / 'standalone/test_mouse_keyboard_dos.py')
    assert run['actual_DOS_assertions'] == 42 and run['actual_driver_state_bytes'] == 576
    for name, digest in run['artifacts'].items():
        assert sha(folder / name) == digest
    assert read(folder / 'manifest.json') == manifest
    source = OUT / 'source-proofs' / args.source_label
    proof = read(source / 'result.json')
    assert proof['passed'] and proof['exit_code'] == 0 and proof['original_inputs'] == []
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/check_mouse_keyboard_source.py')
    assert proof['log_sha256'] == sha(source / 'build.log')
    current(proof['sources'], source / 'source')
    assert len(proof['products']) == 3
    for name, pair in proof['products'].items():
        assert pair['expected'] == pair['actual'] == sha(OUT / name) == sha(source / 'source/build/mouse-keyboard' / name)
    app_source = ROOT / 'build/aspect-unwind/source-proofs' / args.application_source_label
    application = read(app_source / 'result.json')
    previous_path = ROOT / 'docs/validation/aspect-unwind.json'
    previous = read(previous_path)
    assert application['passed'] and len(application['products']) == 27 and application['original_inputs'] == []
    assert application['checker_sha256'] == sha(ROOT / 'standalone/check_aspect_unwind_source.py')
    assert application['log_sha256'] == sha(app_source / 'build.log')
    current(application['sources'], app_source / 'source')
    for name, pair in application['products'].items():
        assert pair['expected'] == pair['actual'] == previous['products'][name]['actual']
        assert pair['actual'] == sha(ROOT / 'build' / name) == sha(app_source / 'source/build' / name)
    assert sha(ROOT / 'build/keyboard/KEYBOARD.EXE') == '929aad6a4e5b3ac921cb5d73974b9381c24889c4dcb51b8f898d60b993d40976'
    primitive_path = ROOT / 'docs/validation/native-mouse.json'
    primitive = read(primitive_path)
    assert primitive['binary_sha256'] == sha(ROOT / 'build/native-mouse/MOUSE.EXE')
    defaults_path = ROOT / 'reconstruction/program_mouse/defaults.json'
    defaults = read(defaults_path)
    assert defaults['bytes'] == 30 and defaults['sha256'] == sha(OUT / 'defaults.bin')
    spec = importlib.util.spec_from_file_location('mouse_prm_codec', ROOT / 'src/config/prm.py')
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves its defining module during construction.
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.WORD_FIELDS['mouse_scale_x'] == 0x4e4 and module.WORD_FIELDS['mouse_scale_y'] == 0x4e6
    original = bytes([0xa5] * 0x4f0)
    edited = module.LegacyPrm201(original).with_word('mouse_scale_x', 8).with_word('mouse_scale_y', 4).to_bytes()
    assert edited[:0x4e4] == original[:0x4e4] and edited[0x4e8:] == original[0x4e8:]
    assert edited[0x4e4:0x4e8] == b'\x08\x00\x04\x00'
    evidence = [OUT / 'manifest.json', OUT / 'checks.json', folder / 'result.json',
                source / 'result.json', source / 'build.log', app_source / 'result.json',
                app_source / 'build.log', previous_path, primitive_path, defaults_path]
    result = dict(passed=True, component_only=True, normal_mouse_enabled=False,
        whole_application_gates_closed=[], build_original_inputs=[],
        native_existing_code_and_guard_bytes=599, native_default_table_bytes=30,
        default_table=defaults, linked_policy_cases=76, actual_DOS_cases=1,
        actual_DOS_assertions=42, actual_driver_state_bytes=576, native_state_bytes=28,
        actual_child_executions=2, fresh_source_products=3, products=proof['products'],
        preserved_application_products=27, preserved_application_source_proof=application,
        prior_161_DOS_receipt_carried_by_binary_identity=True,
        preceding_primitives_and_keyboard_preserved=True, source_hashes=manifest['sources'],
        host_codec_sha256=sha(ROOT / 'src/config/prm.py'),
        nix_inputs={name: sha(ROOT / name) for name in ('nix/flake.nix', 'nix/flake.lock')},
        config_evidence=dict(PRM_scale_offsets=[0x4e4, 0x4e6], admitted_bounds=[1, 999],
            editor_evidence='ev_1eee73036fc8047b24c407d354f7d218a7438e67ddf4cd7a6916b4a913d5c229',
            editor_analysis_artifact_sha256='22070e35ee8d32be4403109f445ad4239d4694fa7d052e7cc4af1bc83ebdcdaf',
            parent16_range_evidence='ev_fbf418713ae6763bce21af6f6cf20e4cbf91980c8e20205f6bf4182581f335b1',
            parent16_analysis_artifact_sha256='7fda4f6320fd3d5b5e1916b85835618cbe73eff81a07336c33b858e94a0cc783'),
        recorder_sha256=sha(Path(__file__)),
        evidence={str(path.relative_to(ROOT)): sha(path) for path in evidence},
        limitations=['Separate composed diagnostic. Startup/live setup, real PROGRAM/ASPECT/fault ownership and actual menu/terminal dispatch remain open.',
            'The two actual DOS children use CRT spawnl. This is not production integration of the recovered PROGRAM controller.',
            'The assembly-started terminal needs a parent-compatible allocator and banked-code ABI; the diagnostic currently uses CRT far-heap initialization.',
            'Mouse events are direct source-owned native callbacks; physical mouse/modem and real DOS kernels remain unvalidated.',
            'Opaque driver contract is assumed after identity/size/guard checks. Quarantine retains storage; repair and close are required before its allocation can terminate.',
            'Prior161 DOS cases were not rerun for comment changes; all27 tested products are exactly reproduced and preserved.',
            'Original macro/window/error UI, application segmentation, full language/BBS/hardware acceptance and every whole-feature gate remain open.'])
    (ROOT / 'docs/validation/mouse-keyboard.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded76 linked cases,42 DOS assertions,3 fresh products and27 preserved application products')


if __name__ == '__main__':
    main()
