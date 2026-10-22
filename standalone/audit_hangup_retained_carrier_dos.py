#!/usr/bin/env python3
"""Independently audit retained-carrier negative evidence, not compatibility."""
import argparse,json,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha


def audit(folder):
    r=json.loads((folder/'checks.json').read_text())
    assert r['passed'] and r['gap_reproduced'] and r['compatibility_accepted'] is False
    assert len(r['cases'])==4
    for name,digest in r['inputs'].items():assert sha(folder/'inputs'/name)==digest
    assert sha(folder/'admitted.EXE')==r['parent_sha256']
    rows=[]
    for drop in (0,1):
      for hard in (0,1):
        name=f'drop{drop}-'+('both' if hard else 'soft');case=folder/name
        row=next(v for v in r['cases'] if v['case']==name)
        for path,digest in row['captures'].items():assert sha(case/path)==digest
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256']
        events=json.loads((case/'peer-events.json').read_text())
        transport=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='transport-receive')
        decoded=bytearray();controls=[];at=0
        while at<len(transport):
            byte=transport[at];at+=1
            if byte==255:
                assert at<len(transport);byte=transport[at];at+=1
                if byte!=255:controls.append(byte);continue
            decoded.append(byte)
        wire=(case/'serial.bin').read_bytes();assert bytes(decoded)==wire
        prefix=b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?62;2c'
        # Alt-X cancels the unacknowledged second dial with configured ESC.
        assert wire==prefix+b'armATZ\rATDCaseTest:23\r\x1b'
        assert [e['kind'] for e in events if e['kind'].startswith('DCD-')]==['DCD-low']
        assert sum(e['kind']=='online-CONNECT' for e in events)==1
        assert sum(e['kind']=='XOFF-online' for e in events)==1
        connected=next(i for i,e in enumerate(events) if e['kind']=='online-CONNECT')
        online=b''.join(bytes.fromhex(e['hex']) for e in events[connected:] if e['kind']=='online-data')
        assert online==wire[len(b'ATZ\rATDCaseTest:23\r'):]
        sample=struct.unpack('<12H',(case/'RETAIN.BIN').read_bytes())
        assert sample[0]==0x4847 and sample[1] and sample[2]>100 and sample[3]>4 and sample[4]>30
        assert (sample[5]>8 if drop else sample[5]==0)
        assert sample[6]>4 and sample[7]==0 and sample[8]>4 and sample[9]==3 and sample[10]>4 and sample[11]==1
        assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes() and (case/'BEFORE.BIN').stat().st_size==42
        assert (case/'VECOLD.BIN').read_bytes()==(case/'VECNEW.BIN').read_bytes() and (case/'VECOLD.BIN').stat().st_size==8
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists()
        assert row['passed'] and all(row['checks'].values())
        rows.append(dict(case=name,sample=list(sample),wire_hex=wire.hex(),guest_control_values=controls,capture_hashes=row['captures']))
    return dict(passed=True,gap_reproduced=True,compatibility_accepted=False,cohort=str(folder.relative_to(ROOT)),parent_sha256=r['parent_sha256'],cases=rows,producer_sha256=sha(folder/'checks.json'),auditor_sha256=sha(Path(__file__)),inputs=r['inputs'],emulator=r['emulator'],scope=r['scope'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=audit(a.cohort.resolve());a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,gap_reproduced=True,cases=len(r['cases']))))


if __name__=='__main__':main()
