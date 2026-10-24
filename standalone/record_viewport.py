#!/usr/bin/env python3
"""Verify native pane recovery, DS repair, cursor composition and DOS/source evidence."""
import argparse,hashlib,json,struct
from pathlib import Path
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dos',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();dos=args.dos.resolve();base=ROOT/'build/viewport';joined=ROOT/'build/terminal-reset-viewport'
    manifest=read(base/'manifest.json');normal=read(base/'checks.json');paired=read(base/'paired-checks.json')
    integration=read(joined/'viewport-checks.json');d=read(dos/'result.json');sources={}
    for report in [manifest,normal,paired,integration,d]:
        for name,digest in report['sources'].items():assert sha(ROOT/name)==digest;sources[name]=digest
    assert normal['passed']and paired['passed']and not normal['paired_original']and paired['paired_original']
    assert len(normal['cases'])==len(paired['cases'])==160
    assert all(case['passed']and case['maintained_foreign_calls']==0 for case in paired['cases'])
    assert any(case['native_foreign_calls']for case in paired['cases'])
    assert normal['products']==paired['products']==manifest['products']
    assert integration['passed']and len(integration['cases'])==10 and all(c['passed']for c in integration['cases'])
    assert integration['wide_allocation_boundary']==0x860f
    assert sha(joined/'RESET.EXE')==integration['binary_sha256']
    assert d['passed']and d['cpu']=='8086'and d['original_inputs']==[]and len(d['products'])==3
    assert sha(dos/'source-build.log')==d['source_build_log_sha256']
    for name,digest in d['products'].items():assert sha(ROOT/name)==sha(dos/'source'/name)==digest
    assert(dos/'PASS.TXT').is_file()and not(dos/'FAIL.TXT').exists()
    for name,digest in read(base/'manifest.json')['sources'].items():assert sha(dos/'source'/name)==digest
    control=ROOT/'build/reset-before-viewport-control';c=read(control/'result.json')
    assert c['passed']and c['baseline_byte_identical']
    assert c['binary_sha256']==sha(ROOT/'build/terminal-reset/RESET.EXE')==sha(control/'source/build/terminal-reset/RESET.EXE')
    assert c['build_log_sha256']==sha(control/'build.log')
    regression=read(ROOT/'build/terminal-reset/checks-original.json')
    assert regression['passed']and regression['binary_sha256']==c['binary_sha256']and regression['genuine_original_comparisons']==47
    failed=ROOT/'build/viewport-dos-01'
    assert(failed/'FAIL.TXT').is_file()and not(failed/'PASS.TXT').exists()
    prior_host=(failed/'source/standalone/viewport_host.asm').read_text()
    assert 'mov ss,ax'not in prior_host and 'mov ss,ax'in(ROOT/'standalone/viewport_host.asm').read_text()
    old=DosImage(failed/'source/build/viewport/VIEWPORT.EXE',failed/'source/build/viewport/VIEWPORT.map')
    assert old.base_segment+struct.unpack_from('<H',old.image,14)[0]!=old.ds
    decoy=ROOT/'build/viewport-before-decoy-fix';assert not read(decoy/'failure.json')['passed']
    artifacts={}
    for folder in [base,joined,dos,control,failed,decoy]:
        for path in folder.rglob('*'):
            if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    evidence=[]
    for name in ['viewport-wrapper-0','viewport-wrapper-1','viewport-0x14816','viewport-0x1483b','viewport-0x1644c','viewport-0x177be','viewport-0x177ae']:
        path=ROOT/'analysis'/(name+'-20261024.rea.json');e=read(path)
        assert e['authority']=='shipped-artifact'
        evidence.append(dict(evidence_id=e['evidence_id'],inline_evidence_sha256=sha(path)))
    for name in ['Makefile','nix/flake.nix','nix/flake.lock','standalone/record_viewport.py']:
        sources[name]=sha(ROOT/name)
    result=dict(passed=True,application_integrated=False,recovered_bytes=183,products=d['products'],
                source_files=d['source_files'],sources=sources,artifacts=artifacts,evidence=evidence,
                source_only_cases=160,paired_original_cases=160,cursor_reset_cases=10,dos_copy_calls=2,
                standard_reset_byte_identical=True,standard_reset_original_comparisons=47,
                native_fault='CGA end callback runs through foreign shadow/video DS',
                repair='Restore caller DS before the real unblank helper; flat native control unchanged',
                retained_failures=[dict(label=decoy.name,accepted=False,reason='Initial decoy ignored relocated CGA field'),
                                   dict(label=failed.name,accepted=False,reason='DOS fixture had not established DS=SS')],
                wide_allocation_boundary=0x860f,
                scope='Guarded pane copies/switches, native foreign-DS counterexample and repair, real native cursor/hidden-status/reset composition, DOS8086 and three-product source proof. Full allocation/unwind, live width/renderer/UI and physical CGA remain open. No package/card change.')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS viewport evidence: native/control/repair, composition, DOS and source proof')


if __name__=='__main__':main()
