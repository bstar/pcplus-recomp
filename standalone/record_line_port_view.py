#!/usr/bin/env python3
"""Check native session/save observations and exact bounded popup rendering."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/line-port-view'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--escape',type=Path,required=True)
    parser.add_argument('--save',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((OUT/'manifest.json').read_text())
    dos=json.loads((OUT/'dos-results.json').read_text())
    assert dos['passed'] and dos['frames']==3
    assert dos['binary_sha256']==manifest['binary_sha256']==sha(OUT/'VIEW.EXE')
    for source,digest in manifest['sources'].items():assert sha(ROOT/source)==digest,source
    proof=json.loads((OUT/'source-proof/result.json').read_text())
    assert proof['passed'] and proof['dos_result']['passed']
    for source,digest in proof['sources'].items():assert sha(ROOT/source)==digest,source
    for name,digest in proof['exact_outputs'].items():assert sha(OUT/name)==digest,name
    cells=[r*80+c for r in range(2,20)for c in range(18,77)]+list(range(24*80,25*80))
    sessions=[]
    for saved,path in ((False,args.escape),(True,args.save)):
        path=path.resolve();assert path.is_relative_to(ROOT/'build')
        result=json.loads((path/'result.json').read_text())
        assert result['producer_sha256']==sha(ROOT/'standalone/test_line_port_original_dos.py')
        assert result['watcher_sha256']==sha(ROOT/'standalone/viewer_original_watch.asm')
        assert result['done'] and result['original_unchanged'] and result['length_unchanged']
        assert result['save']==saved and result['before_words']==[0,5,0,1,8]
        assert result['after_words']==([0,4,2,1,8]if saved else [0,5,0,1,8])
        assert result['changed_offsets']==([2,4]if saved else [])
        compared=[]
        for frame_index,source_index in ((1,0),(2,1),(3,2),(5,2)):
            original=(path/f'frame-{frame_index}.bin').read_bytes()
            source=(OUT/f'dos/VIEW{source_index}.BIN').read_bytes()
            assert sha(path/f'frame-{frame_index}.bin')==result['frames'][frame_index]['sha256']
            assert result['frames'][frame_index]['cursor']==[18,67]
            diffs=[at for at in cells if original[at*2:at*2+2]!=source[at*2:at*2+2]]
            assert not diffs,(saved,frame_index,diffs[:10])
            compared.append(dict(original_frame=frame_index,source_frame=source_index,
                cells=len(cells),differences=0,original_sha256=hashlib.sha256(original).hexdigest(),
                source_sha256=hashlib.sha256(source).hexdigest()))
        baseline=(path/'frame-0.bin').read_bytes()
        restored=(path/'frame-4.bin').read_bytes()
        assert baseline[:3840]==restored[:3840], 'native popup must restore live view'
        sessions.append(dict(save=saved,receipt=str((path/'result.json').relative_to(ROOT)),
            receipt_sha256=sha(path/'result.json'),compared=compared,
            restored_live_cells=1920,changed_prm_offsets=result['changed_offsets']))
    names=list(manifest['sources'])+['standalone/test_line_port_view_dos.py',
        'standalone/test_line_port_original_dos.py','standalone/viewer_original_watch.asm',
        'standalone/record_line_port_view.py','standalone/prove_line_port_view_source.py']
    receipt=dict(component_verified=True,application_integrated=False,physical_runtime_verified=False,
        manifest_sha256=sha(OUT/'manifest.json'),dos_result_sha256=sha(OUT/'dos-results.json'),
        public_source_proof_sha256=sha(OUT/'source-proof/result.json'),public_source_files=len(proof['sources']),
        sources={n:sha(ROOT/n)for n in names},sessions=sessions,
        matching_popup_cells=sum(c['cells']for s in sessions for c in s['compared']),
        limitations=['Native and maintained components execute in DOSBox-X8086; native uses dummy COM1.',
          'Comparison covers default-color 80x25 popup/footer for three line states, including reopen.',
          'Source renderer has no UART, apply/save owner, cursor service or live terminal integration.',
          'Configured colors, other row counts and physical hardware remain unverified.'])
    (ROOT/'docs/validation/line-port-view.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Native Escape/Alt-S and source popup: 9136 character/attribute cells match; live restoration checked')


if __name__=='__main__':main()
