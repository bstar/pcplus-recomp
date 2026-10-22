#!/usr/bin/env python3
"""Seal native window/video algorithms, guarded DOS ownership and group regression."""
import argparse,hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['dos','source-proof','group-control','cohort','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();dos=a.dos.resolve();fresh=a.source_proof.resolve();control=a.group_control.resolve();cohort=a.cohort.resolve();output=a.output.resolve()
    assert all(path.is_relative_to(ROOT/'build') for path in [dos,fresh,control,cohort]) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    base=ROOT/'build/notice-window';m=read(base/'manifest.json');model=read(base/'checks.json');original=read(base/'original-checks.json');d=read(dos/'result.json');f=read(fresh/'result.json');c=read(control/'result.json')
    assert all(r['passed'] for r in [model,original,d,f,c]) and m['original_inputs']==[] and m['owner_normal_compiled']
    assert len(model['cases'])==len(original['cases'])==original['original_comparisons']==98 and model['cases']==original['cases']
    good=[r for r in model['cases'] if not r.get('allocation_failure')];bad=[r for r in model['cases'] if r.get('allocation_failure')]
    assert len(good)==96 and len(bad)==2 and len({r['closed_sha256'] for r in good})==1
    baseline=good[0]['closed_sha256']
    for r in good:assert r['calls'].count('allocate')==r['calls'].count('free')==1 and '0x488f' not in r['calls'] and r['opened_sha256']!=baseline
    for r in bad:assert r['calls'].count('0x488f')==2 and 'free' not in r['calls'] and r['opened_sha256']==r['closed_sha256']!=baseline
    assert all(d['checks'].values()) and d['assertions']==771 and re.fullmatch(r'WINDOW PASS 771 checks 114 allocations 114 frees\s*',(dos/'OUTPUT.TXT').read_text())
    assert d['inputs']['build/notice-window/manifest.json']==f['manifest_sha256']==sha(base/'manifest.json')
    assert f['products']==m['products'] and f['inputs']==m['sources'] and len(m['sources'])==f['source_files']==40
    assert f['checker_sha256']==sha(ROOT/'standalone/prove_notice_window_source.py') and c['checker_sha256']==sha(ROOT/'standalone/check_window_group_control.py')
    for r in [model,original,d,f,c]:
        for name,digest in r['inputs'].items():assert sha(ROOT/name)==digest,name
    for folder,r in [(dos,d),(control,c)]:
        for name,digest in r['captures_sha256'].items():assert sha(folder/name)==digest,name
    assert sha(dos/'WINDOW.EXE')==m['products']['WINDOW.EXE']==c['good_binary_sha256']
    assert c['rejected'] and c['raw_native_products_unchanged']==30 and c['bad_binary_sha256']!=c['good_binary_sha256']
    rejected=read(control/'rejected-DOS/result.json');assert not rejected['passed'] and not rejected['checks']['DOS_exit']
    variant=read(control/'build/notice-window/manifest.json');binding='src/ui/notice_window_native.asm'
    assert 'GROUP DGROUP _DATA\n' not in (control/binding).read_text() and (ROOT/binding).read_text().count('GROUP DGROUP _DATA\n')==1
    assert sha(control/binding)==c['variant_binding_sha256']==variant['sources'][binding]!=m['sources'][binding]
    for name,digest in m['sources'].items():
        if name!=binding:assert variant['sources'][name]==digest
    for name,digest in m['products'].items():assert sha(base/name)==digest
    assert all(variant['products'][name]==digest for name,digest in m['products'].items() if name.endswith('.bin'))
    selected={Path(__file__),base/'manifest.json',base/'checks.json',base/'original-checks.json'}|{ROOT/name for name in m['sources']}
    selected.update(ROOT/name for name in d['inputs']);selected.update([ROOT/'standalone/check_notice_window.py',ROOT/'standalone/prove_notice_window_source.py',ROOT/'standalone/check_window_group_control.py'])
    for folder in [dos,fresh,control]:selected.update(path for path in folder.rglob('*') if path.is_file())
    for label in ['dos-01','dos-02']:
        folder=base/label
        if folder.exists():
            assert not read(folder/'result.json')['passed'];selected.update(path for path in folder.rglob('*') if path.is_file())
    cohort.mkdir();kept={}
    for path in sorted(selected):
        target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);assert sha(target)==sha(path);kept[str(target.relative_to(ROOT))]=sha(target)
    result=dict(passed=True,native_window_component_accepted=True,guarded_window_owner_accepted=True,PROGRAM_binding_accepted=False,full_F02_accepted=False,full_F13_accepted=False,recovered_bytes=1940,reused_bytes=353,CPU_cases=98,original_comparisons=98,native_allocation_failure_counterexamples=2,DOS_assertions=771,DOS_allocations=114,DOS_frees=114,source_files=40,products=m['products'],normal_owner_compiled=True,group_control=dict(rejected=True,raw_native_products_unchanged=30,bad_binary_sha256=c['bad_binary_sha256']),inputs=m['sources'],toolchain_inputs={name:sha(ROOT/name) for name in ['nix/flake.nix','nix/flake.lock','tools/dev']},custody_sha256=kept,auditor_sha256=sha(Path(__file__)),scope='Native full-screen snapshot/frame/shadow/expansion/collapse/cell-copy/cursor algorithms with guarded source-owned reservation/cleanup. Actual 8086 DOSBox-X mode3/page0/80x25 verifies admission, memory denial before mutation, guard and geometry retention/repair and100 repeat lifetimes using real far heap/video. Sound is disabled and reached sound dependencies fail explicitly. CPU heap/BIOS/sound/CRTC timing are modeled; native NULL allocation remains destructive as a counterexample. Actual PROGRAM/notice scheduling, other live video modes, shared parent/window leases, physical timing and all full application gates remain open.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,CPU_cases=98,DOS_assertions=771,source_files=40,custody_files=len(kept))))
if __name__=='__main__':main()
