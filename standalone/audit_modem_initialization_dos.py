#!/usr/bin/env python3
"""Independently bind initialization/error/readiness evidence from actual DOS."""
import argparse,json,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    folder=a.cohort.resolve();r=read(folder/'checks.json');assert r['passed'] and r['initialization_policy_gap_reproduced'] and not r['initialization_policy_accepted']
    assert len(r['cases'])==4 and {v['policy'] for v in r['cases']}=={'OK','quiet','error','delayed'}
    assert r['parent_sha256']==sha(folder/'admitted.EXE')==sha(ROOT/'build/terminal/TERMINAL.EXE')
    for name,digest in r['inputs'].items():assert sha(ROOT/name)==sha(folder/'inputs'/name)==digest
    rows=[]
    for row in r['cases']:
        case=folder/row['policy'];assert row['passed'] and all(row['checks'].values())
        for name,digest in row['captures'].items():assert sha(case/name)==digest
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256']
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        wire=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive');assert wire==(case/'serial.bin').read_bytes()
        assert wire==b'ATZ\rATDCaseTest:23\r'+(b'\x1b[1;16R\x1b[?1;2c+++ATH\r' if row['policy'] in ('OK','quiet') else b'\x1b')
        cursor=0;dial_start=None
        for event in events:
            if event['kind']!='receive':continue
            length=len(bytes.fromhex(event['hex']))
            if cursor<=4<cursor+length:dial_start=event['time']
            cursor+=length
        assert dial_start is not None
        replies=[e for e in events if e['kind']=='response'];early=[e for e in events if e['kind']=='dial-before-ready']
        if row['policy']=='error':
            error=next(e for e in replies if bytes.fromhex(e['hex'])==b'\r\nERROR\r\n');assert error['time']<dial_start and len(early)==1
            assert [bytes.fromhex(e['hex']) for e in replies]==[b'\r\nERROR\r\n',b'\r\nNO CARRIER\r\n']
        elif row['policy']=='delayed':
            pending=next(e for e in events if e['kind']=='initialization-pending');ready=next(e for e in events if e['kind']=='initialization-ready')
            assert pending['time']<dial_start<ready['time'] and ready['time']-pending['time']>=.75 and len(early)==1
            assert [bytes.fromhex(e['hex']) for e in replies]==[b'\r\nOK\r\n',b'\r\nNO CARRIER\r\n']
        else:
            assert not early
            prior=[bytes.fromhex(e['hex']) for e in replies if e['time']<dial_start]
            assert prior==([b'\r\nOK\r\n'] if row['policy']=='OK' else [])
            assert any(bytes.fromhex(e['hex']).startswith(b'CONNECT\r\n') for e in replies)
        prm=(case/'TEST.PRM').read_bytes();assert struct.unpack_from('<H',prm,0x14)[0]==1 and prm[0x18:0x47].split(b'\0',1)[0]==b'ATZ^M'
        assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes() and (case/'BEFORE.BIN').stat().st_size==42
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists() and 'cputype=8086' in (case/'dosbox.conf').read_text()
        rows.append(dict(policy=row['policy'],gap_reproduced=row['gap_reproduced'],wire_hex=wire.hex(),dial_start=dial_start,reply_events=replies,captures=row['captures']))
    result=dict(passed=True,initialization_policy_gap_reproduced=True,initialization_policy_accepted=False,quiet_profile_control_accepted=True,parent_sha256=r['parent_sha256'],cases=rows,source_inputs=r['inputs'],producer_report_sha256=sha(folder/'checks.json'),auditor_sha256=sha(Path(__file__)),
        scope='Four independently audited actual8086 DOS serial-peer cases. The current controller sends ATD after explicit init ERROR and starts ATD before a declared750ms readiness response; those peers reject the dial. Immediate OK and intentional no-reply quiet-ready controls connect and answer actual ANSI queries. Readiness timing is the owned peer policy, not a Boca measurement. No initialization correction, SIP/audio, physical modem or full F03 acceptance.')
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,DOS_cases=4,gaps=2,controls=2,initialization_policy_accepted=False)))


if __name__=='__main__':main()
