#!/usr/bin/env python3
"""Reject a Chat-mode parent/settings pairing before staging any payload."""
import argparse
import copy
import json
from pathlib import Path
from package_connection_test import ROOT, sha, validate_chat_setup_pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent', 'setup', 'legacy-parent', 'legacy-setup', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    manifests = []
    receipts = {}
    for binary in (args.parent, args.setup, args.legacy_parent, args.legacy_setup):
        binary = binary.resolve()
        assert binary.is_relative_to(ROOT / 'build')
        path = binary.with_name('manifest.json')
        manifest = json.loads(path.read_text())
        assert sha(binary) == manifest['binary_sha256']
        receipts[str(path.relative_to(ROOT))] = sha(path)
        manifests.append(manifest)
    parent, setup, legacy_parent, legacy_setup = manifests
    cases = []
    variants = [('matched-current', parent, setup, True), ('matched-legacy', legacy_parent, legacy_setup, True),
                ('new-parent-old-editor', parent, legacy_setup, False), ('old-parent-new-editor', legacy_parent, setup, False)]
    changed = copy.deepcopy(parent)
    changed['chat_loader']['module']['api_version'] = 0x106
    variants.append(('old-module-API', changed, setup, False))
    changed = copy.deepcopy(parent)
    changed['experimental_chat_send_mode'] = False
    variants.append(('undeclared-API0107', changed, legacy_setup, False))
    changed = copy.deepcopy(setup)
    changed['field_count'] -= 1
    variants.append(('missing-editor-field', parent, changed, False))
    for name, left, right, accepted in variants:
        actual = True
        try:
            validate_chat_setup_pair(left, right)
        except AssertionError:
            actual = False
        assert actual == accepted, name
        cases.append(dict(case=name, passed=True, accepted=actual))
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir()
    result = dict(passed=True, cases=cases, receipts=receipts,
        sources={name: sha(ROOT / name) for name in ('standalone/check_chat_setup_pair.py', 'standalone/package_connection_test.py')},
        scope=__doc__ + ' Source-built products checked against their manifests; altered in-memory declarations only. No files staged, DOS execution or physical acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS2 matched pairs and5 rejected Chat settings pairings')


if __name__ == '__main__':
    main()
