#!/usr/bin/env python3
"""Audit the banked process observer across all56 DOS UART/flow scenarios."""
import argparse,hashlib,itertools,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-root','source-proof','cohort','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();source=a.source_root.resolve();proof_path=a.source_proof.resolve()
    cohort=a.cohort.resolve();output=a.output.resolve()
    assert all(p.is_relative_to(ROOT/'build') for p in (source,proof_path,cohort))
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists() and not cohort.exists()
    product=ROOT/'build/aspect-process/ASPECT.EXE';identity=sha(product)
    manifest=read(product.parent/'manifest.json');assert manifest['diagnostic_build'] and manifest['binary_sha256']==identity
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    sys.path.insert(0,str(ROOT/'src/aspect'))
    from compiler import compile_source
    paths=[Path(__file__),product.parent/'manifest.json',product,product.parent/'ASPECT.map']
    paths += [ROOT/n for n in manifest['sources']]
    results=[];seen=set()
    labels=['banked-observer-01','banked-com1-other-flows-01','banked-com2-all-flows-01']
    for label in labels:
        folder=source/'build/aspect-process/runs'/label;run=read(folder/'result.json')
        assert run['passed'] and run['binary_sha256']==identity
        paths.append(folder)
        frozen=read(folder/'manifest.json')
        for name,digest in frozen['sources'].items():assert sha(folder/'sources'/name)==digest,name
        for case in run['cases']:
            assert case['passed'] and all(case['checks'].values())
            port,flow,kind=case['port'],case['flow'],case['kind'];key=(port,flow,kind)
            assert key not in seen;seen.add(key)
            target=folder/('com%d-%s-%s'%key)
            for name,digest in case['artifacts'].items():assert sha(target/name)==digest,name
            assert sha(target/'ASPECT.EXE')==identity
            assert (target/'RESULT.TXT').read_text().strip()=='PASS'
            text=(target/'CHECKS.TXT').read_text()
            matched=re.search(r'ASPECT PROCESS COM(\d) ([NSHB]) result(\d+) raw(\d+) calls(\d+) private(\d+) compiler(\d+) checks(\d+) failures(\d+)',text)
            assert matched and 'FAIL' not in text
            expected_status={'abort':11,'budget':6}.get(kind,0)
            assert (int(matched[1]),matched[2],int(matched[3]),int(matched[6]),int(matched[7]),int(matched[9]))==(port,flow,expected_status,7,int(kind=='full'),0)
            assert 'control98 JFT-preserved' in text
            assert all((target/('SLOT%d.BIN'%n)).read_bytes()==('SEED%d'%n).encode() for n in range(5))
            assert (target/'SLOT5.BIN').read_bytes()==b'pending5'
            brackets=11 if kind=='full' else 2 if kind in ('abort','budget') else 1
            expected=b'\x11D'+b'\x13\x11'*brackets+b'RF\x13' if flow in 'SB' else b'DRF'
            assert (target/'wire.bin').read_bytes()==expected
            if kind=='full':
                assert (target/'NEXT.ASX').read_bytes()==compile_source((target/'NEXT.ASP').read_text())
                assert (target/'SHELL.OUT').read_bytes()==b'SHELLREAL' and (target/'EXE.OUT').read_bytes()==b'REAL EXE'
                assert (target/'BATCH.OUT').read_text().strip()=='BATCHPASS'
            if kind in ('abort','budget'):assert 'recovery1 control98' in text
            if kind=='large':
                match=re.search(r'ARENA borrowed(\d+) live-frame(\d+)',text)
                assert match and int(match[1])>int(match[2])>0
            results.append(dict(port=port,flow=flow,scenario=kind,passed=True,assertions=int(matched[8]),wire_sha256=sha(target/'wire.bin')))
    assert seen==set(itertools.product((1,2),'NSHB',('full','fallback','large','memory','divide','abort','budget')))
    listing=(product.parent/'ASPECT.map').read_text();segments={}
    for name in ('_TEXT','PROCESSDIAG','PROGRAMCODE'):
        match=re.search(r'^'+name+r'\s+CODE\s+\S+\s+\S+\s+([0-9a-f]+)',listing,re.M|re.I)
        assert match;segments[name]=int(match[1],16);assert 0<segments[name]<=65536
    assert segments['_TEXT']==65520
    for path in [proof_path,source/'build/aspect-process/source-proofs/banked-observer-source-01/result.json']:
        proof=read(path);assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==23
        assert proof['products']['aspect-process/ASPECT.EXE']['actual']==identity
        assert all(row['actual']==row['expected'] for row in proof['products'].values())
        paths.append(path.parent)
    # Freeze raw observations, both source closures and the failed near build.
    paths += [ROOT/'build/abort-confirm-diagnostic-overflow-01',ROOT/'build/abort-confirm-raw-external-test-01.stderr']
    cohort.mkdir()
    for path in paths:
        target=cohort/path.relative_to(ROOT)
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if path.is_dir():shutil.copytree(path,target)
        else:shutil.copy2(path,target)
    files={str(p.relative_to(cohort)):sha(p) for p in cohort.rglob('*') if p.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,diagnostic_sha256=identity,actual_DOS_cases=56,results=results,segments_bytes=segments,
                remaining_near_code_bytes=65536-segments['_TEXT'],source_only_products=23,
                source_proof_sha256=sha(proof_path),auditor_sha256=sha(Path(__file__)),cohort=str(cohort.relative_to(ROOT)),
                frozen_files=len(files),files_manifest_sha256=sha(cohort/'files.json'),
                retained_failure='Unbanked instrumented build exceeded near TEXT by368 bytes. PROCESSDIAG relocates observation/check/environment helpers behind explicit far CRT adapters; no checks or scenarios are removed.',
                scope='Same diagnostic executable tested in an isolated source tree on COM1/COM2 with NONE/SOFT/HARD/BOTH settings and seven scenarios. Exact wires, source compilation, private streams, inheritance, allocation failure, divide/recovery and VM budget checks. Final canonical executable is byte-identical and rebuilds23 products without originals. Emulated UART settings do not prove physical flow-control timing. Production105-slot and experimental108-slot application identities remain separate; all full application gates stay open.')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,DOS_cases=len(results),original_free_products=23,remaining_near_code_bytes=16)))


if __name__=='__main__':main()
