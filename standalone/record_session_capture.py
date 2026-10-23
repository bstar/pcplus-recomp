#!/usr/bin/env python3
"""Audit shared capture against raw DOS artifacts and empty-tree source proof."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cohort',type=Path,required=True);a=ap.parse_args()
    out=a.cohort.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture';m=read(base/'manifest.json')
    assert m['experimental_session_capture'] and m['banked_process']
    assert sha(base/'TERMINAL.EXE')==m['binary_sha256']
    layout=inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map');assert layout==m['memory_layout']
    assert layout['near_bytes']==65520 and layout['resident_code_spare_bytes']==744
    bank=next(x for x in layout['code_segments'] if x['name']=='HOOK_CODE');assert bank['bytes']<512
    linked_path=ROOT/'build/session-capture/linked-final-01/result.json';linked=read(linked_path)
    assert linked['passed'] and linked['inputs']==144 and linked['binary_sha256']==m['binary_sha256']
    dos=ROOT/'build/session-capture/DOS-final-01';d=read(dos/'result.json')
    assert d['passed'] and len(d['cases'])==3 and d['binary_sha256']==m['binary_sha256']
    for r in d['cases']:assert r['passed'] and all(r['checks'].values())
    expected=bytearray(struct.pack('<22H',1,19200,0,0,8,1,0,1,4,7,8,9,10,11,1,1,0x3f8,4,126,30,0,13)+bytes(584))
    struct.pack_into('<H',expected,410,350)
    assert (dos/'observe/PLANCAP.BIN').read_bytes()==expected
    for case,color in [('observe',7),('cancel',7),('color',30)]:
        folder=dos/case
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        assert len((folder/'BEFORE.BIN').read_bytes())==42
        assert (folder/'PASS.TXT').read_bytes().strip()==b'PASS' and not (folder/'FAIL.TXT').exists()
        assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
        assert b'ready' in (folder/'serial.bin').read_bytes()
        cells=(folder/'SCREEN.BIN').read_bytes()
        assert cells[22:32:2]==b' LIVE' and cells[23:33:2]==bytes([color])*5
    original=(dos/'observe/TEST.PRM').read_bytes();assert original==(dos/'cancel/TEST.PRM').read_bytes()
    changed=bytearray(original);struct.pack_into('<H',changed,0x1ae,30)
    assert (dos/'color/TEST.PRM').read_bytes()==changed
    proof_path=ROOT/'build/session-capture/source-final-01/result.json';proof=read(proof_path)
    assert proof['passed'] and proof['original_inputs']==[] and proof['source_files']==675 and len(proof['products'])==5
    for n,h in proof['products'].items():assert sha(ROOT/n)==h,n
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py')
    sources={}
    for r in [m,linked,d,proof]:
        for n,h in r['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    files=[ROOT/n for n in sources]+[base/n for n in ['manifest.json','TERMINAL.EXE','terminal.map']]
    files.extend([linked_path,proof_path,proof_path.parent/'build.log'])
    files.extend(p for p in dos.rglob('*') if p.is_file() and 'source' not in p.relative_to(dos).parts)
    for n in ['observer.asm','observe/PLANCAP.BIN','observe/result.json','cancel/result.json','color/result.json']:
        files.append(ROOT/'build/session-capture/DOS-01'/n)
    files.extend([Path(__file__).resolve(),ROOT/'standalone/terminal_memory.py',ROOT/'Makefile',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock',ROOT/'tools/dev'])
    out.mkdir(parents=True);custody={}
    for p in sorted(set(files)):
        target=out/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        assert sha(target)==sha(p);custody[str(target.relative_to(ROOT))]=sha(target)
    report=dict(passed=True,linked_cases=144,DOS_cases=d['cases'],source_files=675,products=proof['products'],
        binary_sha256=m['binary_sha256'],memory_layout=layout,custody_sha256=custody,
        terminal_HOOK_accepted=False,complete_native_PRM_accepted=False,full_application_accepted=False,
        scope='Shared configured/setup policy exercised in three actual8086 DOS sessions; actual-session policy and geometry/context linked checks. Captures raw active/configured groups without semantic validation. Inactive modem and divergent shared fields remain explicit; no HOOK routing, native register lifetime, full PRM projection/returned commit, BBS or hardware acceptance.',
        early_attempt='Initial three DOS cases passed but aggregate provenance failed due to a misspelled dependency filename. Early raw artifacts are historical only; final cohort binds current sources.')
    (ROOT/'docs/validation/session-capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS144 linked cases,three8086 DOS workflows,675 sources/five products')
if __name__=='__main__':main()
