#!/usr/bin/env python3
"""Reject copied compiler-bridge Help bundle corruption before a DOS run."""
import argparse
import json
from pathlib import Path
import shutil
from chat_help_bbs_support import inputs
from product_inputs import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    payload, out = args.payload.resolve(), args.output.resolve()
    assert payload.is_relative_to(ROOT / 'build') and out.is_relative_to(ROOT / 'build') and not out.exists()
    original = {str(p.relative_to(payload)): sha(p) for p in payload.rglob('*') if p.is_file()}
    out.mkdir()
    cases = []
    for kind in ('unchanged', 'parent-binding', 'missing-resource-manifest', 'helper-manifest', 'topic-count', 'context-three'):
        folder = out / kind
        shutil.copytree(payload, folder)
        package = json.loads((folder / 'package.json').read_text())
        if kind == 'parent-binding':
            package['parent_manifest_sha256'] = '0' * 64
        elif kind == 'missing-resource-manifest':
            (folder / 'PCPLUS.json').unlink()
        elif kind == 'helper-manifest':
            path = folder / 'help-build/manifest.json'
            path.write_bytes(path.read_bytes() + b' ')
        elif kind in ('topic-count', 'context-three'):
            resource_path = folder / 'PCPLUS.json'
            resource = json.loads(resource_path.read_text())
            if kind == 'topic-count':
                resource['topics'] = 46
            else:
                path = folder / 'PCPLUS.HLP'
                data = bytearray(path.read_bytes())
                assert data[3+3*38:3+3*38+9] == b'Chat Mode'
                data[3+3*38] = ord('X')
                path.write_bytes(data)
                resource['sha256'] = package['products']['PCPLUS.HLP'] = sha(path)
            resource_path.write_text(json.dumps(resource, indent=2) + '\n')
            package['resource_manifest_sha256'] = sha(resource_path)
        (folder / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
        error = None
        try:
            inputs(folder / 'TERMINAL.EXE')
        except (AssertionError, KeyError, OSError) as exception:
            error = type(exception).__name__
        rejected = error is not None
        assert rejected == (kind != 'unchanged'), kind
        cases.append(dict(case=kind, passed=True, rejected=rejected, error=error))
    assert original == {str(p.relative_to(payload)): sha(p) for p in payload.rglob('*') if p.is_file()}
    result = dict(passed=True, cases=cases, original_unchanged=True,
        original_package_sha256=sha(payload / 'package.json'),
        sources={name: sha(ROOT / name) for name in ('lab/bbs/check_chat_help_bundle_controls.py', 'lab/bbs/chat_help_bbs_support.py')},
        scope=__doc__ + ' Declared metadata mutations affect only owned copies. Context/topic cases update related copied hashes to test semantic guards. No DOS, network or physical acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS original and5 rejected Help bundle controls')


if __name__ == '__main__':
    main()
