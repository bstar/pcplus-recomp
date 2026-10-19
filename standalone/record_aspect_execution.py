#!/usr/bin/env python3
"""Freeze stack/nonlocal-unwind evidence with current source/hash reconciliation."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    components={};local={};sources={}
    for name in ('stack','unwind'):
        paths=[f'build/aspect-{name}/{p}.json' for p in ('manifest','checks','checks-native')]
        manifest,checks,native=[json.loads((ROOT/p).read_text()) for p in paths]
        assert checks['passed'] and native['passed']
        assert checks['original_inputs']==manifest['original_inputs']==[]
        assert checks['binary_sha256']==native['binary_sha256']==manifest['binary_sha256']
        assert native['optional_original']['original_sha256']==ORIGINAL_SHA
        if name=='stack':
            assert checks['cpu_cases']==native['optional_original']['paired_cpu_cases']==786
            assert native['optional_original']['exact_stack_bytes']==197
            assert native['optional_original']['exact_copy_bytes']==72
            assert checks['flat_sha256']==native['flat_sha256']==manifest['flat_sha256']
            assert checks['copy_sha256']==native['copy_sha256']==manifest['copy_sha256']
        else:
            assert checks['DOS_cases']==native['DOS_cases']==72
            assert checks['manifest_sha256']==native['manifest_sha256']==sha(ROOT/paths[0])
            assert native['optional_original']['exact_bytes']==618
        current={**manifest['sources'],f'standalone/check_aspect_{name}.py':checks['check_sha256']}
        assert checks['check_sha256']==native['check_sha256']
        for path,digest in current.items():
            assert sha(ROOT/path)==digest,path
            assert path not in sources or sources[path]==digest
            sources[path]=digest
        local.update({p:sha(ROOT/p) for p in paths})
        components[name]=dict(manifest=manifest,source_only_checks=checks,
                              optional_original=native['optional_original'])
    evidence=[]
    carrier_manifest_path='analysis/pcplus-overlay-entry-images/manifest.json'
    carrier_manifest=json.loads((ROOT/carrier_manifest_path).read_text())
    assert carrier_manifest['original_sha256']==ORIGINAL_SHA
    carrier=next(i for i in carrier_manifest['images'] if i['overlay']==16)
    carrier_path=ROOT/'analysis/pcplus-overlay-entry-images'/carrier['file']
    assert sha(carrier_path)==carrier['sha256']
    native_range=next(r for r in carrier['source_ranges'] if r['role']=='overlay-16')
    assert native_range['relative_address']==0xd0d0 and native_range['source_file_offset']==109184
    assert native_range['bytes']>=197
    local[carrier_manifest_path]=sha(ROOT/carrier_manifest_path)
    entries=[('pcplus-main','0x14ebc')]+[('pcplus-overlay-anchored-16',f'0x1{p}') for p in ('d0d0','d0f2','d110','d134','d157','d17a','d186')]
    for directory,procedure in entries:
        rel=f'analysis/{directory}/functions/{procedure}-asm.json'
        tool_result=json.loads((ROOT/rel).read_text())
        record=json.loads(next(c['text'] for c in tool_result['content'] if c['type']=='text'))
        subject_sha=record['subject']['digest']['sha256']
        assert subject_sha==(ORIGINAL_SHA if directory=='pcplus-main' else carrier['sha256'])
        local[rel]=sha(ROOT/rel)
        evidence.append(dict(evidence_id=record['evidence_id'],operation=record['operation'],subject_sha256=subject_sha,
                             parameters=record['parameters'],scope='Retained static assembly, not observed execution'))
    sources['standalone/record_aspect_execution.py']=sha(Path(__file__).resolve())
    result=dict(passed=True,sources=sources,local_evidence=local,components=components,retained_rea=evidence,
        static_carrier=dict(sha256=carrier['sha256'],original_sha256=ORIGINAL_SHA,stack_source_range=native_range,
                            scope='Synthetic static-analysis carrier only; never executed. Original bytes independently compared by optional native checks.'),
        limitations=['Stack component preserves unchecked arithmetic/pop semantics; not a safe production stack.',
          'Unwind composition executes real native abort/setjmp/longjmp; file/UI/opcode callbacks remain diagnostic models.',
          'Error105 adapter calls real native abort, while complete error UI/resource ownership remains unimplemented.',
          'No whole compiler/VM, file-backed scripts, live terminal script integration or physical hardware validation.'])
    out=ROOT/'docs/validation/aspect-execution.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(f'Recorded {out.relative_to(ROOT)}')

if __name__=='__main__':main()
