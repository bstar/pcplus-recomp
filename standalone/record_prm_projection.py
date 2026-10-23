#!/usr/bin/env python3
"""Bind the accepted supported-fields projector to source, DOS bytes and OMF imports."""
import argparse,hashlib,json,shutil
from pathlib import Path
from omf_imports import records,externals
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cohort',type=Path,required=True);a=ap.parse_args()
    out=a.cohort.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/prm-projection/DOS-03';r=json.loads((base/'result.json').read_text())
    assert r['passed'] and all(r['checks'].values()) and r['self_checks']==2660 and r['original_inputs']==[]
    assert (base/'OUTPUT.TXT').read_bytes()==b'PRMPROJECT checks=2660 failures=0\r\n'
    assert (base/'PASS.TXT').read_bytes().strip()==b'PASS' and not (base/'FAIL.TXT').exists()
    assert sha(base/'PRMPROJ.EXE')==r['binary_sha256']==sha(base/'rebuild/PRMPROJ.EXE')
    assert sha(base/'ACTIVE.BIN')==r['projected_sha256']
    for n,h in r['sources'].items():assert sha(ROOT/n)==h==sha(base/'source'/n),n
    imported=[name.decode() for kind,payload,_ in records((base/'prm_projection.obj').read_bytes()) if kind==0x8c for name,_ in externals(payload)]
    assert set(imported)=={'memcpy_','memcmp_','strcmp_','_transfer_import_path','_terminal_import_decode','_modem_import_decode','_transfer_import_decode','_small_code_'}
    before=(base/'BASE.BIN').read_bytes();after=(base/'ACTIVE.BIN').read_bytes()
    assert len(before)==len(after)==1264
    allowed=set()
    for lo,hi in [(0,0x174),(0x176,0x178),(0x186,0x188),(0x194,0x196),(0x198,0x1a0),
                  (0x1a4,0x1a6),(0x1ae,0x1b8),(0x1e0,0x1e3),(0x1e4,0x1e6),(0x4ea,0x4ec)]:allowed.update(range(lo,hi))
    assert all(i in allowed or x==after[i] for i,x in enumerate(before))
    assert after[0x42c:0x42e]==before[0x42c:0x42e]==bytes.fromhex('efbe')
    for lo,hi in [(0x18,0x47),(0x47,0x60),(0x60,0x79),(0x79,0x92),(0x92,0xab),(0xab,0xc4),*[(0xc4+i*16,0xd4+i*16) for i in range(11)]]:
        end=after.index(0,lo,hi)+1;assert before[end:hi]==after[end:hi]
    files=[p for p in base.rglob('*') if p.is_file()]
    for run in ['DOS-01','DOS-02']:
        old=ROOT/'build/prm-projection'/run
        files.extend(old/n for n in ['result.json','OUTPUT.TXT','dosbox.log','source/standalone/prm_projection_diagnostic.c'])
    files.extend(ROOT/n for n in r['sources'])
    files.extend([Path(__file__).resolve(),ROOT/'standalone/omf_imports.py',ROOT/'Makefile',ROOT/'tools/dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock'])
    out.mkdir(parents=True);custody={}
    for p in sorted(set(files)):
        target=out/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        assert sha(target)==sha(p);custody[str(target.relative_to(ROOT))]=sha(target)
    receipt=dict(passed=True,DOS_checks=2660,binary_sha256=r['binary_sha256'],projection_sha256=r['projected_sha256'],
        imports=imported,sources=r['sources'],custody_sha256=custody,terminal_capture_accepted=False,
        complete_native_PRM_accepted=False,terminal_HOOK_accepted=False,scope=r['scope'],
        early_attempts='DOS-01/02:23 invalid-output fixture comparisons used the original sentinel after successful calls; exact complete-image oracle passed. DOS-03 snapshots output before rejected calls.')
    (ROOT/'docs/validation/prm-projection.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS source/bytes/import audit,2660 DOS checks')
if __name__=='__main__':main()
