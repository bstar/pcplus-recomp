#!/usr/bin/env python3
"""Seal original editor launch observations and the opt-in source parent tests."""
import argparse
import hashlib
import json
from pathlib import Path
from build_path_session import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    binary = ROOT / 'build/editor-parent-v2-20261106/TERMINAL.EXE'
    manifest = json.loads(binary.with_name('manifest.json').read_text())
    digest = sha(binary)
    assert manifest['experimental_external_editor']
    assert digest == manifest['binary_sha256']
    original_digest = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    disabled_digest = '2d626fb001bed53d3fb3c3a49ea1859f17e69b6ade07792c3a160043ff0a6c02'

    def bind(path):
        return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))

    def read(path, maintained=True):
        report = json.loads(path.read_text())
        for name, want in report.get('sources', {}).items():
            assert sha(ROOT / name) == want, name
        if maintained:
            assert report['passed'] and report['binary_sha256'] == digest, path
        return report

    for name, want in manifest['sources'].items():
        assert sha(ROOT / name) == want, name
    native = []
    for case in ['relative', 'absolute', 'options', 'spaces', 'empty', 'cancel', 'long', 'disabled']:
        folder = ROOT / f'build/editor-original-{case}-20261106'
        report = read(folder / 'result.json', False)
        assert report['tool'] == 'editor' and report['PRM_offset'] == 0x39e
        assert report['original_sha256'] == original_digest
        assert report['process_exit'] == 0 and report['DOS_done'] and report['generated_unchanged']
        expected = {'relative': ' PAGE.DAT', 'absolute': ' D:\\PAGE.DAT',
                    'options': ' /Q /X PAGE.DAT', 'spaces': ' D:\\A B.DAT',
                    'empty': '', 'long': ' ' + 'A' * 48}.get(case)
        assert report['child_tail_text'] == expected
        if expected is None:
            assert not report['child_report_bytes']
        else:
            assert report['child_report_bytes'] == 202
            assert report['child_drive'] == 2 and report['child_cwd'] == ''
            assert sha(folder / 'd/VCHILD.BIN') == report['child_report_sha256']
        assert sha(folder / 'c/PCPLUS.EXE') == original_digest
        native.append(dict(case=case, report=bind(folder / 'result.json')))

    rows, comparisons = [], []
    for tool, cases in [('editor', ['relative', 'absolute', 'options', 'spaces', 'empty',
                                   'cancel', 'long', 'maximum', 'reference', 'browser',
                                   'malformed', 'disabled']),
                        ('viewer', ['relative', 'options', 'cancel', 'reference', 'browser', 'maximum'])]:
        for case in cases:
            name = (f'editor-parent-v2-relative-20261106' if tool == 'editor' and case == 'relative'
                    else f'editor-v2-{tool}-{case}-20261106')
            path = ROOT / 'build' / name / 'result.json'
            report = read(path)
            assert report['tool'] == tool and len(report['cases']) == 1
            item = report['cases'][0]
            assert item['case'] == case and item['passed'] and all(item['checks'].values())
            frame = ROOT / item['drive'] / 'VIEWUI.BIN'
            assert sha(frame) == item['frame_sha256']
            rows.append(dict(tool=tool, case=case, report=bind(path)))
            if tool == 'editor' and case in ['relative', 'absolute', 'options', 'spaces', 'empty', 'cancel', 'long']:
                original = ROOT / f'build/editor-original-{case}-20261106/c/EDITVIEW.BIN'
                old = original.read_bytes()[4014:8014]
                new = frame.read_bytes()[4018:8018]
                def box(data):
                    return b''.join(data[(row * 80 + 5) * 2:(row * 80 + 76) * 2]
                                    for row in range(10, 15))
                assert len(box(old)) == 710 and box(old) == box(new), case
                comparisons.append(dict(case=case, identical_bytes=710,
                                        sha256=hashlib.sha256(box(new)).hexdigest(),
                                        original=bind(original), maintained=bind(frame)))

    layout_path = ROOT / 'build/editor-parent-v2-layout-20261106/result.json'
    layout = read(layout_path)
    assert layout['state_bytes'] == 130 and layout['external_editor']
    assert len(layout['negative_controls']) == 5 and all(c['rejected'] for c in layout['negative_controls'])
    proof_path = ROOT / 'build/editor-public-source-proof-20261106/result.json'
    proof = read(proof_path)
    assert proof['disabled_sha256'] == disabled_digest and not proof['original_inputs']
    assert proof['ancestor_git_unavailable']
    assert sha(ROOT / 'build/editor-disabled-v6-20261106/TERMINAL.EXE') == disabled_digest
    static_path = ROOT / 'analysis/pcedit-launch-static-20261106.json'
    static = json.loads(static_path.read_text())
    evidence_ids = [r['evidence_id'] for r in static['records']]
    assert len(evidence_ids) == 2
    result = dict(passed=True, binary_sha256=digest, disabled_sha256=disabled_digest,
                  original_sha256=original_digest, original_runtime=native, maintained_runtime=rows,
                  native_prompt_comparisons=comparisons, layout=bind(layout_path),
                  source_build=bind(proof_path), source_commit=proof['source_commit'],
                  source_file_count=proof['source_count'], static_evidence=bind(static_path),
                  static_evidence_ids=evidence_ids, near_bytes=layout['near_bytes'],
                  resident_code_bytes=layout['resident_code_bytes'], deployment_changed=False,
                  sources={'standalone/record_external_editor.py': sha(Path(__file__))},
                  limits=['External launcher only; no recreated or bundled PCEDIT application.',
                          'Empty-setting error presentation intentionally differs from original.',
                          'Physical modem and editor-specific BBS/transfer/carrier-loss composition remain open.',
                          'Reviewed connection package and bridge service unchanged.'])
    output.mkdir()
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS 8 original workflows,12 editor and6 viewer DOS cases,7 native boxes,5 linked controls,public rebuild')


if __name__ == '__main__':
    main()
