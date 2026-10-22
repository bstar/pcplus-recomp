#!/usr/bin/env python3
"""Audit a retained-parser failure without promoting it to compatibility acceptance."""
import argparse, json, struct, subprocess
from pathlib import Path
from audit_aspect_transmit_wait import ROOT, sha, read, ESC
from directory_test_support import accounting_check
import runpy


def verify(folder):
    report=read(folder/'checks.json'); receipt=read(folder/'retained-checks.json')
    assert not report['passed'] and receipt['gap_reproduced']
    assert receipt['compatibility_accepted'] is False
    assert sha(folder/'checks.json')==receipt['producer_report_sha256']
    assert sha(folder/'admitted.EXE')==report['parent_sha256']==receipt['parent_sha256']
    for name,digest in report['inputs'].items():
        assert sha(folder/'inputs'/name)==digest,name
    for name,key in [('test_manual_cancel_retained_dos.py','checker_sha256'),('test_manual_cancel_dos.py','base_checker_sha256')]:
        assert sha(folder/'retained-inputs/standalone'/name)==receipt[key]
    backend=report['emulator']; wrapper=Path(backend['wrapper'])
    assert backend['test_backend'] and 'pcplus-dcd-lab-' in str(wrapper)
    assert sha(wrapper)==backend['wrapper_sha256']
    assert sha(wrapper.with_name('.dosbox-x-wrapped'))==backend['binary_sha256']
    proof=read(folder/'inputs/build/dosbox-dcd-lab-build.json')[0]
    assert subprocess.check_output(['nix-store','--query','--outputs',proof['drvPath']],text=True).split()==[str(wrapper.parent.parent)]
    patches=subprocess.check_output(['nix-store','--query','--binding','patches',proof['drvPath']],text=True).split()
    assert len(patches)==1 and sha(Path(patches[0]))==backend['patch_sha256']
    assert sha(folder/'inputs/nix/patches/dosbox-dcd-control.patch')==backend['patch_sha256']
    assert len(report['cases'])==2 and {r['case'] for r in report['cases']}=={'soft','both'}
    rows=[]
    for row in report['cases']:
        case=folder/row['case']; assert not row['passed']
        assert {k for k,v in row['checks'].items() if not v}=={'no_unexpected_commands','actual_init_and_dial'}
        for name,digest in row['captures'].items(): assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==report['parent_sha256']
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case']=='both'))
        sample=struct.unpack('<12H',(case/'CANCEL.BIN').read_bytes())
        assert sample[0]==0x434d and sample[1] and sample[2]>18 and sample[3]>8
        assert sample[4:6]==(0,0) and sample[6]>8 and sample[7:10]==(1,0,0)
        assert sample[10]>18 and sample[11]==1
        wire=(case/'serial.bin').read_bytes()
        assert wire==b'AATZ\rATDCaseTest:23\r'+ESC+b'[1;16R'+ESC+b'[?62;2cready'+ESC+b'[1;16R+++ATH\r'
        events=read(case/'peer-events.json')
        assert all(a['time']<=b['time'] for a,b in zip(events,events[1:]))
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        decoded=bytearray(); status=[]; escaped=False
        for event in events:
            if event['kind']!='transport-receive': continue
            for byte in bytes.fromhex(event['hex']):
                if escaped:
                    escaped=False
                    if byte==255: decoded.append(byte)
                    else: assert byte<=7; status.append(byte)
                elif byte==255: escaped=True
                else: decoded.append(byte)
        assert not escaped and bytes(decoded)==wire
        assert status==[int(e['hex'],16) for e in events if e['kind']=='modem-status']
        ordered=[]
        for kind,value in [('DCD-low','ff81'),('XOFF-first-init','13'),('cancel-DTR-low',''),('cancel-DTR-restored',''),('initialization-ERROR','4141545a'),('DCD-high-CONNECT','ff8b'),('DCD-low-hangup','ff81')]:
            found=[e for e in events if e['kind']==kind]; assert len(found)==1 and found[0]['hex']==value
            ordered.append(found[0]['time'])
        assert ordered==sorted(ordered) and .8<ordered[3]-ordered[2]<1.3
        assert not any(e['kind']=='receive' and ordered[1]<e['time']<ordered[3] for e in events)
        raw=read(case/'result.json'); assert raw['commands']==['AATZ','ATDCaseTest:23']
        for before,after,length in [('BEFORE.BIN','AFTER.BIN',42),('VECOLD.BIN','VECNEW.BIN',8)]:
            data=(case/before).read_bytes(); assert len(data)==length and data==(case/after).read_bytes()
        fixture=runpy.run_path(str(folder/'inputs/standalone/directory_fixtures.py'))['directory'](profile=4)
        assert accounting_check(fixture,(case/'TEST.DIR').read_bytes(),1,1)
        rows.append(dict(case=row['case'],initialization_command='AATZ',retry_initialization_failed=True,reconnected=True,first_DCD_high_samples=sample[4],idle_pause=sample[8],online_ticks=sample[10],wire_sha256=sha(case/'serial.bin')))
    return dict(passed=True,gap_reproduced=True,compatibility_accepted=False,physical_hardware_accepted=False,stock_backend_accepted=False,parent_sha256=report['parent_sha256'],cases=rows,producer_receipt_sha256=sha(folder/'retained-checks.json'),auditor_sha256=sha(Path(__file__)),scope='Owned retained-parser peer on explicit patched DCD lab. Cancellation retires flow but fails to terminate partial initialization; later CONNECT does not establish successful initialization. No physical Boca or stock-emulator acceptance.')


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('folder',type=Path); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    assert not a.output.exists()
    result=verify(a.folder.resolve()); a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,gap_reproduced=True,cases=len(result['cases']))))


if __name__=='__main__': main()
