#!/usr/bin/env python3
"""Audit accepted baseline bytes, lifetime transitions and source-only products."""
import argparse,hashlib,json,re,shutil,struct
from pathlib import Path
from terminal_memory import inspect_terminal_memory
from omf_imports import records,externals
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def sealed(raw,generation,kind):
    h=0xb41d^generation^kind
    for value in struct.unpack('<632H',raw):h=((h<<1)|(h>>15))&65535;h^=value
    return struct.pack('<4H',0xb451,generation,kind,h)+raw
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cohort',type=Path,required=True);a=ap.parse_args()
    out=a.cohort.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound'
    probe=ROOT/(str(base.relative_to(ROOT))+'-probe');m=read(base/'manifest.json');pm=read(probe/'manifest.json')
    assert m['experimental_session_baseline'] and not m['session_projection_probe'] and pm['session_projection_probe']
    for folder,r in [(base,m),(probe,pm)]:assert sha(folder/'TERMINAL.EXE')==r['binary_sha256']
    assert b'AWAY.PRM' not in (base/'TERMINAL.EXE').read_bytes()
    layout=inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map');assert layout==m['memory_layout']
    assert layout['near_bytes']==65520 and layout['resident_code_spare_bytes']==702
    assert next(c for c in layout['code_segments'] if c['name']=='HOOK_CODE')['bytes']==3647
    listing=(base/'terminal.map').read_text()
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    seg,off=symbols['terminal_baseline_storage'];eseg,end=symbols['terminal_baseline_storage_end']
    assert seg==eseg and end-off==1272
    exe=(base/'TERMINAL.EXE').read_bytes();header=struct.unpack_from('<14H',exe)
    assert exe[header[4]*16+seg*16+off:header[4]*16+seg*16+end]==bytes(1272)
    imports={}
    for name in ['terminal_preferences','live_setup_owner','session_projection']:
        imports[name]=[n.decode() for k,p,_ in records((base/(name+'.obj')).read_bytes()) if k==0x8c for n,_ in externals(p)]
    assert {'_hook_baseline_invalidate','_hook_baseline_publish'}<=set(imports['terminal_preferences'])
    assert '_hook_baseline_publish' in imports['live_setup_owner'] and '_hook_baseline_invalidate' not in imports['live_setup_owner']
    assert '_hook_baseline_copy' in imports['session_projection']
    linked_path=ROOT/'build/session-baseline/linked-02/result.json';linked=read(linked_path)
    assert linked['passed'] and linked['inputs']==1330 and linked['binary_sha256']==m['binary_sha256']
    dos=ROOT/'build/session-baseline/DOS-01';d=read(dos/'result.json')
    assert d['passed'] and d['retained_baseline'] and len(d['cases'])==5 and d['binary_sha256']==pm['binary_sha256']
    for r in d['cases']:
        assert r['passed'] and all(r['checks'].values());folder=dos/r['case']
        raw=(folder/'AWAY.PRM').read_bytes();assert len(raw)==1264 and raw==(folder/'PBASE.BIN').read_bytes()
        assert not (folder/'TEST.PRM').exists() and (folder/'BSTATE.BIN').read_bytes()==sealed(raw,1,1)
        expected=bytearray(raw);serial=r['case'] in ('serial','serial-inactive')
        struct.pack_into('<H',expected,2,5 if serial else 6)
        struct.pack_into('<H',expected,0x194,6 if r['case'].startswith('directory-') else 4)
        if serial:struct.pack_into('<H',expected,0x1a4,350)
        assert (folder/'POUT.BIN').read_bytes()==expected and (folder/'PSTAT.BIN').read_bytes()==b'\0\0'
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and len((folder/'BEFORE.BIN').read_bytes())==42
    live=ROOT/'build/session-baseline/live-DOS-01';l=read(live/'result.json')
    assert l['passed'] and len(l['cases'])==2 and l['binary_sha256']==m['binary_sha256']
    for r in l['cases']:
        assert r['passed'] and all(r['checks'].values()) and r['child_reproduces'];folder=live/r['case']
        raw=(folder/'STATE1.BIN').read_bytes()[8:];assert len(raw)==1264 and (folder/'STATE1.BIN').read_bytes()==sealed(raw,1,1)
        accepted=r['case']=='accepted';changed=bytearray(raw);struct.pack_into('<H',changed,0x1ae if accepted else 0x194,30 if accepted else 7)
        assert (folder/'TEST.PRM').read_bytes()==changed
        assert (folder/'STATE2.BIN').read_bytes()==(sealed(bytes(changed),2,2) if accepted else sealed(raw,1,1))
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and len((folder/'BEFORE.BIN').read_bytes())==42
        assert b'ready' in (folder/'serial.bin').read_bytes()
        cells=(folder/'SCREEN.BIN').read_bytes();assert cells[22:32:2]==b' LIVE' and cells[23:33:2]==bytes([30 if accepted else 7])*5
        assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
    proof_path=ROOT/'build/session-baseline/source-01/result.json';proof=read(proof_path)
    assert proof['passed'] and proof['original_inputs']==[] and proof['source_files']==683 and len(proof['products'])==6
    for n,h in proof['products'].items():assert sha(ROOT/n)==h,n
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py')
    sources={}
    for r in [m,pm,linked,d,l,proof]:
        for n,h in r['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    files=[ROOT/n for n in sources]+[linked_path,proof_path,proof_path.parent/'build.log']
    for folder in [base,probe]:files.extend(folder/n for n in ['manifest.json','TERMINAL.EXE','terminal.map'])
    files.extend(base/(n+'.obj') for n in imports)
    for folder in [dos,live]:files.extend(p for p in folder.rglob('*') if p.is_file() and 'source' not in p.relative_to(folder).parts)
    files.extend([Path(__file__).resolve(),ROOT/'standalone/omf_imports.py',ROOT/'standalone/terminal_memory.py',ROOT/'Makefile',ROOT/'tools/dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock'])
    out.mkdir(parents=True);custody={}
    for p in sorted(set(files)):
        target=out/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        assert sha(p)==sha(target);custody[str(target.relative_to(ROOT))]=sha(target)
    report=dict(passed=True,linked_cases=1330,startup_DOS_cases=d['cases'],live_DOS_cases=l['cases'],source_files=683,
        products=proof['products'],memory_layout=layout,store_bytes=1272,imports=imports,custody_sha256=custody,
        terminal_HOOK_accepted=False,full_native_PRM_accepted=False,full_application_accepted=False,
        scope='Retained accepted startup image and successful setup acknowledgement; failed startup invalidation and failed live retention. Linked store/seal/bound projection, five8086 renamed-file startup runs, two8086 live sessions/four controlled children, six empty-tree products. No native register handback, full PRM projection, terminal HOOK/returned commit, BBS or hardware acceptance.')
    (ROOT/'docs/validation/session-baseline.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS1330 linked,five startup/two live DOS sessions,683 sources/six products')
if __name__=='__main__':main()
