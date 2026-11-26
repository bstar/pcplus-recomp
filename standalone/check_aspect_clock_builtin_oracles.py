#!/usr/bin/env python3
"""Bind frozen clock/procedure-keyword outcomes to actual host and DOS compiler output."""
import argparse, hashlib, json, sys
from pathlib import Path
from build_context_help import ROOT, sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import CompileError, compile_source


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();folder=a.compiler.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    checks=json.loads((folder/'checks.json').read_text())
    manifest=json.loads((folder/'manifest.json').read_text())
    assert checks['passed'] and checks['original_inputs']==manifest['original_inputs']==[]
    assert checks['binary_sha256']==manifest['binary_sha256']==sha(folder/'ASPCOMP.EXE')
    assert checks['manifest_sha256']==sha(folder/'manifest.json')
    assert checks['case_manifest_sha256']==sha(folder/'cases.json')
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    rows=json.loads((folder/'cases.json').read_text())
    indexed={r['source_sha256']:(i,r) for i,r in enumerate(rows)}
    records=[];sources=dict(manifest['sources'])
    for leaf,count,accepted in [('aspect_clock_builtin_compiler_vectors.json',63,27),
                                ('aspect_procedure_keyword_vectors.json',566,8)]:
        path=ROOT/'standalone/fixtures'/leaf;oracle=json.loads(path.read_text())
        assert oracle['compiler_sha256']=='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
        assert len(oracle['cases'])==count and sum(c['success'] for c in oracle['cases'])==accepted
        assert checks['fixture_sources'][str(path.relative_to(ROOT))]==sha(path)
        sources[str(path.relative_to(ROOT))]=sha(path)
        for case in oracle['cases']:
            assert hashlib.sha256(case['source'].encode('cp437')).hexdigest()==case['source_sha256']
            try:data=compile_source(case['source']);success=True
            except CompileError:success=False;data=b''
            assert success==case['success'],case['label']
            i,row=indexed[case['source_sha256']]
            assert row['accepted']==success,case['label']
            if success:
                expected=bytes.fromhex(case['hex'])
                assert data==expected==(folder/'tests'/f'P{i:05}.ASX').read_bytes(),case['label']
                assert hashlib.sha256(expected).hexdigest()==case['asx_sha256']==row['asx_sha256']
        records.append(dict(fixture=leaf,cases=count,accepted=accepted,rejected=count-accepted))
    for path in [Path(__file__),ROOT/'src/aspect/compiler.py',ROOT/'standalone/build_context_help.py']:
        sources[str(path.relative_to(ROOT))]=sha(path)
    result=dict(passed=True,original_inputs=[],oracles=records,binary_sha256=manifest['binary_sha256'],
        sources=sources,receipts={str((folder/n).relative_to(ROOT)):sha(folder/n)
            for n in ('checks.json','manifest.json','cases.json')},
        scope=__doc__+'63 clock expression cases and566 procedure names (558 catalog keywords,8 valid prefix controls). Does not establish all variable-declaration keyword rules or full language parity.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS629 original compiler cases against host and actual DOS bytes')


if __name__=='__main__':main()
