#!/usr/bin/env python3
"""Verify the complete LoC art/focus/modal-return matrix and bound captures."""
import argparse
import json
from pathlib import Path
from product_inputs import ROOT, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run, out = a.run.resolve(), a.output.resolve()
    assert run.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
    report = json.loads((run/'result.json').read_text())
    assert report['passed'] and len(report['cases'])==8
    assert {(r['physical_rows'],r['status_hidden']) for r in report['cases']} == {
        (rows,hidden) for rows in (25,28,43,50) for hidden in (0,1)}
    for name,digest in report['sources'].items():
        assert sha(ROOT/name)==digest,name
    cases = []
    for case in report['cases']:
        capture = ROOT/case['capture']
        assert case['passed'] and sha(ROOT/case['audit_path'])==case['audit_sha256']
        logical = case['physical_rows']-(not case['status_hidden'])
        for filename in ['proxy-integration.json','screen-reference-audit.json','loc-main-audit.json']:
            record = json.loads((capture/filename).read_text())
            assert record['passed'] and record['binary_sha256']==report['terminal_sha256']
            for group in ['sources','product_inputs']:
                for name,digest in record.get(group,{}).items():
                    assert sha(ROOT/name)==digest,name
            for name,digest in record.get('captures',{}).items():
                path = Path(name)
                assert sha(path if path.is_absolute() else ROOT/path)==digest,name
        audit = json.loads((capture/'loc-main-audit.json').read_text())
        assert audit['matched_reference_cells']==logical*80 and audit['matched_source_art_cells']==logical*80-14
        assert audit['field_cells']==14 and audit['field_text']=='LOCSNAP' and audit['field_foreground']==15
        assert audit['NAWS']==[[80,logical]] and audit['native_reference_observed'] and audit['all_39_native_labels']
        assert audit['actual_CPR']==[24 if logical==24 else 25,53] and audit['message_menu_return']
        cell = json.loads((capture/'screen-reference-audit.json').read_text())
        assert cell['different_cells']==0 and cell['matched_cells']==logical*80
        base = json.loads((capture/'result.json').read_text())
        assert base['passed'] and base['cpu']=='8086'
        assert base['serial']['com']==3 and base['serial']['irq']==5
        before = (capture/'BEFORE.BIN').read_bytes()
        assert len(before)==42 and before==(capture/'AFTER.BIN').read_bytes()
        cases.append(dict(physical_rows=case['physical_rows'],status_hidden=case['status_hidden'],
            logical_rows=logical,matched_reference_cells=logical*80,matched_source_model_cells=logical*80-14,
            field_cells=14,actual_CPR=audit['actual_CPR'],passed=True))
    assert sum(r['matched_reference_cells'] for r in cases)==23040
    assert sum(r['matched_source_model_cells'] for r in cases)==22928
    out.mkdir(parents=True,exist_ok=False)
    result = dict(passed=True,DOS_workflows=8,matched_reference_cells=23040,matched_source_model_cells=22928,
        live_field_cells=112,native_39_label_witnesses=8,message_menu_return_workflows=8,
        cases=cases,terminal_sha256=report['terminal_sha256'],report_sha256=sha(run/'result.json'),
        sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},
        scope=__doc__+' Current copied source menu/form/layout on isolated stock core with selected M/F/G actions. Paced synthetic-Hayes route; not whole live board, all intermediate frames, transfers, fonts or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS complete LoC matrix:8 authenticated workflows/23040 cells/8 native-menu witnesses')


if __name__=='__main__':
    main()
