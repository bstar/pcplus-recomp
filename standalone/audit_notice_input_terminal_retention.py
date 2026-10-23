#!/usr/bin/env python3
"""Independently decode the four complete-terminal retention DOS captures."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cohort',required=True);p.add_argument('--output',required=True)
    p.add_argument('--run',action='append',required=True)
    a=p.parse_args();assert len(a.run)==4
    cohort=ROOT/a.cohort;cohort.mkdir(parents=True,exist_ok=False)
    custody={};cases=[];coverage=set()
    for name in a.run:
        run=ROOT/name;d=json.loads((run/'result.json').read_text());repair=d['repair_on_child_exit'];port=d['port']
        assert d['passed'] and all(d['checks'].values())
        assert (repair,port) not in coverage;coverage.add((repair,port))
        folder=run/'unrepaired';raw=(folder/'RENDER.BIN').read_bytes()
        # Fixed capture layouts are decoded here independently of the test's
        # exported dictionaries/booleans (19 child words,12 retention words).
        r=struct.unpack_from('<12H',raw,len(raw)-24)
        c=struct.unpack_from('<19H',raw,len(raw)-24-38)
        assert 'admit_words: times 67 dw 0' in (run/'observer.asm').read_text()
        assert 'admit_snapshots: times 3538 db 0' in (run/'observer.asm').read_text()
        # Header, JFTs, file owners, mode/debug/admission and history captures.
        mouse_offset=14+40+832+20+8+2+67*2+3538+256+8*64+3*72
        mouse=raw[mouse_offset:mouse_offset+4150]
        mouse_words=struct.unpack_from('<27H',mouse)
        driver_bytes=mouse_words[22]
        assert 0<driver_bytes<=2048
        assert mouse[54:54+driver_bytes]==mouse[54+2048:54+2048+driver_bytes]
        head=struct.unpack_from('<7H',raw)
        assert head[:4]==(0x524e,1,1,1) and head[6]==10
        assert c[0]==c[11]==1 and c[4:6]==(8,4) and c[7]==0
        assert c[12:16]==(10,11,0,2)
        assert r[2]==1 and r[3]==0x310a and r[5]==c[3]
        assert r[8:]==(5,778,1,int(repair))
        assert r[7]==int(not repair)
        if repair:
            assert r[4]==0x4c00
            assert c[16:]==(11,c[1],c[2])
        else:
            assert r[4]==0x310e and r[6]==head[5]
            assert c[16:]==(0,0,0)
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        screen=(folder/'SCREEN.BIN').read_bytes()[::2];wire=(folder/'serial.bin').read_bytes()
        assert b'ASPECT memory retained.' in screen
        assert (b'Mouse restore failed' in screen)==(not repair)
        assert b'BAD-CONTINUED' not in wire and (b'ready' in wire)==repair
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
        assert d['parent_sha256']==sha(folder/'TERMINAL.EXE')
        assert d['child_sha256']==sha(folder/'ASPECT.EXE')
        assert d['observer_sha256']==sha(folder/'RENDER.COM')
        for n,h in d['sources'].items():
            assert sha(ROOT/n)==h and sha(run/'sources'/n)==h,n
        for path in sorted(run.rglob('*')):
            if not path.is_file():continue
            target=cohort/'accepted'/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
            assert sha(target)==sha(path)
            custody[str(target.relative_to(ROOT))]=sha(target)
        cases.append(dict(run=name,port=port,repaired_vector=repair,child_exit=r[3],parent_exit=r[4],raw_child_status=r[9],parent_sha256=d['parent_sha256'],child_sha256=d['child_sha256']))
    assert coverage=={(False,1),(False,2),(True,1),(True,2)}
    checker=cohort/'accepted'/Path(__file__).relative_to(ROOT)
    checker.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(__file__,checker)
    custody[str(checker.relative_to(ROOT))]=sha(checker)
    result=dict(passed=True,selected_complete_terminal_retention_accepted=True,
        retained_child_reuse_or_unload_accepted=False,full_application_accepted=False,
        cases=cases,custody_sha256=custody,
        excluded_early_fixtures='unrepaired-01/03 could not collect reports; unrepaired-02/04 assembly errors. Final collector is resident and entered with an8086-compatible tiny COM. No application binary changed.',
        scope='Four DOSBox-X8086 sessions with ordinary terminal and ASPECT on COM1/2. Owned observer replaces INT33 after callback/PSP admission. Unrepaired: child DOS310A and terminal DOS310E retain their PSP blocks, foreign vector preserved. Repaired at child final DOS31 boundary: child stays retained, parent resumes serial input and exits DOS4C normally. Known snapshot/vector cleanup after terminal return matches exact42-byte hardware snapshot and driver snapshot. No general retained-child repair/retry/unload, real DOS kernel, physical hardware or full application acceptance.')
    dest=ROOT/a.output;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(cases),'sessions;',len(custody),'preserved files')
    return 0
if __name__=='__main__':raise SystemExit(main())
