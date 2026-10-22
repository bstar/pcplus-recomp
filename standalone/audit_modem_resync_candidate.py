#!/usr/bin/env python3
"""Independently compare retained-parser failure with isolated retry-separator captures."""
import argparse, difflib, json, runpy, struct
from pathlib import Path
import audit_manual_cancel_retained as baseline_audit
from audit_aspect_transmit_wait import ROOT, sha, read, ESC
from directory_test_support import accounting_check


def verify(folder,policy,backend):
    report=read(folder/'checks.json');assert report['passed'] and not report['gap_reproduced']
    assert report['emulator']==backend and sha(folder/'admitted.EXE')==report['parent_sha256']
    for name,digest in report['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    assert len(report['cases'])==2 and {r['case'] for r in report['cases']}=={'soft','both'}
    rows=[]
    for row in report['cases']:
        case=folder/row['case'];assert row['passed'] and all(row['checks'].values())
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==report['parent_sha256']
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case']=='both'))
        sample=struct.unpack('<12H',(case/'CANCEL.BIN').read_bytes())
        assert sample[0]==0x434d and sample[1] and sample[2]>18 and sample[3]>8
        assert sample[4:6]==(0,0) and sample[6]>8 and sample[7:10]==(1,0,0) and sample[10]>18 and sample[11]==1
        for before,after,length in [('BEFORE.BIN','AFTER.BIN',42),('VECOLD.BIN','VECNEW.BIN',8)]:
            data=(case/before).read_bytes();assert len(data)==length and data==(case/after).read_bytes()
        fixture=runpy.run_path(str(folder/'inputs/standalone/directory_fixtures.py'))['directory'](profile=4)
        assert accounting_check(fixture,(case/'TEST.DIR').read_bytes(),1,1)
        wire=(case/'serial.bin').read_bytes()
        assert wire==b'A\rATZ\rATDCaseTest:23\r'+ESC+b'[1;16R'+ESC+b'[?62;2cready'+ESC+b'[1;16R+++ATH\r'
        events=read(case/'peer-events.json');assert all(a['time']<=b['time'] for a,b in zip(events,events[1:]))
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        decoded=bytearray();status=[];escaped=False
        for event in events:
            if event['kind']!='transport-receive':continue
            for byte in bytes.fromhex(event['hex']):
                if escaped:
                    escaped=False
                    if byte==255:decoded.append(byte)
                    else:assert byte<=7;status.append(byte)
                elif byte==255:escaped=True
                else:decoded.append(byte)
        assert not escaped and bytes(decoded)==wire and status==[int(e['hex'],16) for e in events if e['kind']=='modem-status']
        ordered=[]
        separator_kind='stale-command-terminated' if policy=='retained' else 'empty-command-terminated'
        for kind,value in [('DCD-low','ff81'),('XOFF-first-init','13'),('cancel-DTR-low',''),('cancel-DTR-restored',''),(separator_kind,'41' if policy=='retained' else ''),('DCD-high-CONNECT','ff8b'),('DCD-low-hangup','ff81')]:
            found=[e for e in events if e['kind']==kind];assert len(found)==1 and found[0]['hex']==value
            ordered.append(found[0]['time'])
        assert ordered==sorted(ordered) and .8<ordered[3]-ordered[2]<1.3
        assert not any(e['kind']=='receive' and ordered[1]<e['time']<ordered[3] for e in events)
        assert not any(e['kind']=='initialization-ERROR' for e in events)
        raw=read(case/'result.json');assert raw['commands']==['ATZ','ATDCaseTest:23']
        rows.append(dict(case=row['case'],parser_policy=policy,passed=True,first_DCD_high_samples=sample[4],idle_pause=sample[8],online_ticks=sample[10],wire_sha256=sha(case/'serial.bin')))
    return report,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    old=baseline_audit.verify(a.baseline.resolve());old_report=read(a.baseline/'checks.json');candidate=a.candidate.resolve()
    rows=[]
    for label,policy in [('retained-fixed-01','retained'),('cleared-fixed-01','cleared')]:
        r,found=verify(candidate/'build/manual-cancel-dos'/label,policy,old_report['emulator']);rows+=found
    manifest=read(candidate/'build/terminal/manifest.json');assert manifest['binary_sha256']==r['parent_sha256']!=old['parent_sha256']
    for name,digest in manifest['sources'].items():assert sha(candidate/name)==digest
    changed=[name for name,digest in manifest['sources'].items() if old_report['inputs'].get(name)!=digest]
    assert set(changed)=={'src/terminal/connection.asm','src/terminal/modem_sender.asm'}
    patch=''
    for name in sorted(changed):
        patch+=''.join(difflib.unified_diff((a.baseline/'inputs'/name).read_text().splitlines(True),(candidate/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    assert patch==(ROOT/'patches/modem-retry-resync.patch').read_text()
    result=dict(passed=True,candidate_only=True,canonical_accepted=False,physical_hardware_accepted=False,stock_backend_accepted=False,baseline_parent_sha256=old['parent_sha256'],parent_sha256=r['parent_sha256'],cases=rows,changed_product_sources=changed,patch_sha256=sha(ROOT/'patches/modem-retry-resync.patch'),auditor_sha256=sha(Path(__file__)),scope=__doc__+' Four actual DOS patched-DCD-lab SOFT/BOTH cases; source-bound unchanged configured initialization, exact UART stream, separate stale/empty command termination, no corrupted ATZ, hardware/vectors/accounting restored. Broader admission and physical validation remain open.')
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),candidate_only=True)))


if __name__=='__main__':main()
