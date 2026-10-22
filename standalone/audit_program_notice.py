#!/usr/bin/env python3
"""Bind native notice recovery, paired CPU cases, actual DOS and source-only proof."""
import argparse,hashlib,itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dos',type=Path,required=True);p.add_argument('--source-proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.dos=a.dos.resolve();a.source_proof=a.source_proof.resolve()
    assert a.dos.is_relative_to(ROOT/'build') and a.source_proof.is_relative_to(ROOT/'build')
    out=a.output.resolve();assert out.is_relative_to(ROOT/'docs/validation') and not out.exists()
    base=ROOT/'build/program-notice';m=read(base/'manifest.json');model=read(base/'checks.json');original=read(base/'original-checks.json');dos=read(a.dos/'result.json');fresh=read(a.source_proof/'result.json');proof=read(ROOT/'reconstruction/program_notice/provenance.json')
    assert all(r['passed'] for r in (model,original,dos,fresh))
    assert model['cases']==original['cases'] and original['original_comparisons']==len(model['cases'])==495
    keys={(r['entry'],r['length'],r['kind'],r['policy']) for r in model['cases']}
    assert keys==set(itertools.product(['0x427f','0x4288','0x429a'],[0,1,2,31,73,74,75,80,81,160,511],[0,1,256],['immediate','transient','timeout','backwards','stopped-clock']))
    assert sum(not r['returned'] for r in model['cases'])==99
    assert dos['cases']==6 and all(dos['checks'].values()) and dos['manifest_sha256']==sha(base/'manifest.json')==fresh['manifest_sha256']
    assert sha(a.dos/'NOTICE.EXE')==m['products']['NOTICE.EXE']
    for name,digest in dos['captures_sha256'].items():assert sha(a.dos/name)==digest
    for r in (model,original,dos,fresh):
        for name,digest in r['inputs'].items():assert sha(ROOT/name)==digest
    assert fresh['checker_sha256']==sha(ROOT/'standalone/prove_program_notice_source.py')
    assert fresh['products']==m['products'] and fresh['inputs']==m['sources'] and m['original_inputs']==[]
    for name,digest in m['products'].items():assert sha(base/name)==digest
    assert proof['bytes']==190 and proof['sha256']==m['products']['core.bin'] and proof['read_evidence'] and proof['mapping_evidence'] and proof['function_evidence']
    paths=[base/'manifest.json',base/'checks.json',base/'original-checks.json',a.dos/'result.json',a.source_proof/'result.json',ROOT/'reconstruction/program_notice/provenance.json']
    result=dict(passed=True,native_notice_component_accepted=True,application_binding_accepted=False,full_PROGRAM_accepted=False,full_F13_accepted=False,recovered_bytes=190,reused_clock_string_bytes=71,CPU_cases=495,original_comparisons=495,stopped_clock_counterexamples=99,DOS_cases=6,source_files=fresh['source_files'],products=m['products'],provenance=proof,reports={str(path.relative_to(ROOT)):sha(path) for path in paths},inputs={**m['sources'],**dos['inputs'],'standalone/check_program_notice.py':sha(ROOT/'standalone/check_program_notice.py'),'standalone/prove_program_notice_source.py':sha(ROOT/'standalone/prove_program_notice_source.py')},toolchain_inputs={name:sha(ROOT/name) for name in ['nix/flake.nix','nix/flake.lock','tools/dev']},auditor_sha256=sha(Path(__file__)),scope='Exact native notice wrappers/controller with real recovered strlen and DOS-time extraction. CPU time samples, keys, sound and screen services are declared models. Six actual DOSBox-X8086 cases use real DOS seconds/BIOS keys and a maintained screen-copy test platform; speaker is a no-op test boundary. Original macro keyboard, window heap/drawing, foreground UART, PROGRAM integration, other geometry and physical hardware remain unverified.')
    with out.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,CPU_cases=495,DOS_cases=6,application_binding_accepted=False)))
if __name__=='__main__':main()
