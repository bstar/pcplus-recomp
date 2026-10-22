#!/usr/bin/env python3
"""Independently audit DOS software-flow stall, resume and parent handback."""
import argparse,json,shutil,struct
from pathlib import Path
from audit_aspect_abort_carrier import ROOT,sha,read
ESC=b'\x1b';DATA=b'0123456789ABCDEF'*128


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run=a.run.resolve();cohort=a.cohort.resolve();output=a.output.resolve()
    assert run.is_relative_to(ROOT/'build') and cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    report=read(run/'checks.json');assert report['passed'] and {r['case'] for r in report['cases']}=={'soft','both'}
    for name,digest in report['inputs'].items():assert sha(ROOT/name)==sha(run/'inputs'/name)==digest,name
    results={}
    for row in report['cases']:
        assert row['passed'] and all(row['checks'].values());case=run/row['case']
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==report['parent_sha256'] and sha(case/'ASPECT.EXE')==report['runner_sha256']
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        raw=(case/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw)
        assert head[:4]==(0x524e,1,1,1) and head[6]==0
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        paused,returned,stuck=struct.unpack('<3H',raw[-6:]);assert paused>12 and returned>18 and stuck==0
        assert (case/'FLOW.OK').read_bytes()==b'RESUMED'
        wire=(case/'serial.bin').read_bytes()
        expected=b'ATZ\rATDCaseTest:23\r\x13\x11'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+DATA+b'\x13\x11ready'+ESC+b'[1;24R+++ATH\r'
        assert wire==expected
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        assert b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')==wire
        blocked=[e for e in events if e['kind']=='xoff-go'];resumed=[e for e in events if e['kind']=='xon'];queries=[e for e in events if e['kind']=='parent-query']
        assert len(blocked)==len(resumed)==len(queries)==1
        off,on=blocked[0]['time'],resumed[0]['time'];assert 1.2<=on-off<1.8 and queries[0]['time']>on
        assert bytes.fromhex(blocked[0]['hex'])==b'\x13GO' and bytes.fromhex(resumed[0]['hex'])==b'\x11'
        # KEYREADY is received in the event immediately preceding XOFF. Every
        # later receive before XON must contain only flow-control bytes.
        for event in events:
            if event['kind']=='receive' and off<=event['time']<on:assert set(bytes.fromhex(event['hex']))<={17,19}
        settings=(case/'TEST.PRM').read_bytes();assert struct.unpack_from('<2H',settings,0x198)==(1,int(row['case']=='both'))
        assert (case/'PASS.TXT').is_file() and not (case/'FAIL.TXT').exists()
        results[row['case']]=dict(passed=True,child_paused_ticks=paused,parent_return_ticks=returned,
                                  pause_seconds=on-off,payload_bytes=len(DATA),wire_bytes=len(wire),wire_sha256=sha(case/'serial.bin'))
    cohort.mkdir()
    for source in (run,ROOT/'build/aspect-flow-return-dos/flow-01',ROOT/'build/aspect-flow-return-dos/flow-02',Path(__file__)):
        target=cohort/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_dir():shutil.copytree(source,target)
        else:shutil.copy2(source,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,parent_sha256=report['parent_sha256'],runner_sha256=report['runner_sha256'],cases=results,
                cohort=str(cohort.relative_to(ROOT)),frozen_files=len(files),files_manifest_sha256=sha(cohort/'files.json'),
                full_application_accepted=False,scope='Two actual8086 DOS runs: SOFT and BOTH,1.2-second remote XOFF pause,2048 exact resumed script bytes, live manual parent typing/query and original hardware/JFT/file-owner restoration. Entire wire including all four flow-control bytes is exact. Peer and passive timer independently constrain the pause. CTS remains asserted in DOSBox-X nullmodem.',
                remaining=['CTS/RTS stalls, sustained RX high water, cancellation/timeout handback, carrier reconnect, software audio and physical modem flow timing remain open.'])
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=results)))


if __name__=='__main__':main()
