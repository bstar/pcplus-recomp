#!/usr/bin/env python3
"""Audit raw DOS transmit-stall results independently of producer summaries."""
import argparse,hashlib,json,re,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ESC=b'\x1b'
PAYLOAD=b'0123456789ABCDEF'*128
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_run(folder,cts=False):
    r=read(folder/'checks.json');assert r['passed']
    expected_cases=({mode+'-'+flow for mode in ('resume','timeout','cancel') for flow in ('hard','both')} if cts else
        {'default-long','configured-long','maximum-long','short-timeout','cancel-long','cancel-behind-key'})
    assert {c['case'] for c in r['cases']}==expected_cases and len(r['cases'])==6
    for name,digest in r['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    results={}
    for row in r['cases']:
        assert row['passed'] and all(row['checks'].values());name=row['case'];case=folder/name
        for path,digest in row['captures'].items():assert sha(case/path)==digest,path
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256'] and sha(case/'ASPECT.EXE')==r['runner_sha256']
        cancel=name.startswith('cancel');timeout=name.startswith('timeout') or name=='short-timeout'
        success=not cancel and not timeout;status=13 if cancel else 14 if timeout else 0
        soft=not cts or name.endswith('both');queued=cts and cancel or name=='cancel-behind-key'
        seconds=('2' if timeout else '30') if cts else {'default-long':None,'configured-long':'6','maximum-long':'3600','short-timeout':'2','cancel-long':'30','cancel-behind-key':'30'}[name]
        cfg=(case/'dosbox.conf').read_text();assert 'cputype=8086' in cfg
        assert re.findall(r'^set PCPLUS_TXWAIT=(.*)$',cfg,re.M)==([] if seconds is None else [seconds])
        assert ('transparent:0' if cts else 'transparent:1') in cfg
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(int(soft),1)
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        assert (case/'PASS.TXT').is_file() and not (case/'FAIL.TXT').exists()
        raw=(case/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw)
        assert head[:4]==(0x524e,1,1,1) and head[6]==status
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        state=struct.unpack('<4H' if cts else '<3H',raw[-8:] if cts else raw[-6:]);assert state[1]>18
        if cts:assert state[0]==state[2]==0 and state[3]>(60 if success else 8)
        else:assert state[0]>(60 if success else 8)
        marker=case/('CTS.OK' if cts else 'WAIT.OK')
        assert marker.is_file()==success
        if success:assert marker.read_bytes()==b'RESUMED'
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        low_kind='cts-low-go' if cts else 'xoff-go';high_kind='cts-high' if cts else 'xon'
        low=[e for e in events if e['kind']==low_kind];high=[e for e in events if e['kind']==high_kind]
        assert len(low)==len(high)==1 and 4<=high[0]['time']-low[0]['time']<5
        assert bytes.fromhex(low[0]['hex'])==(b'\xff\x02GO' if cts else b'\x13GO')
        assert bytes.fromhex(high[0]['hex'])==(b'\xff\x03' if cts else b'\x11')
        during=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and low[0]['time']<e['time']<high[0]['time'])
        assert not bytes(c for c in during if c not in (17,19))
        wire=(case/'serial.bin').read_bytes()
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        status_frames=[]
        if cts:
            decoded=bytearray();escape=False
            for e in events:
                if e['kind']!='transport-receive':continue
                for byte in bytes.fromhex(e['hex']):
                    if escape:
                        escape=False
                        if byte==255:decoded.append(byte)
                        else:assert byte<=3;status_frames.append(byte)
                    elif byte==255:escape=True
                    else:decoded.append(byte)
            assert not escape and bytes(decoded)==wire and status_frames
            assert status_frames==[int(e['hex'],16) for e in events if e['kind']=='modem-status']
            ready=[e for e in events if e['kind']=='cts-ready'];assert len(ready)==1 and ready[0]['time']<low[0]['time'] and ready[0]['hex']=='ff03'
        control=b'\x13\x11' if soft else b''
        reply=ESC+(b'[1;24R' if success else b'[4;1R' if cancel else b'[5;1R')
        expected=b'ATZ\rATDCaseTest:23\r'+control+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+(PAYLOAD if success else b'')+control+(b'q' if queued else b'')+b'ready'+reply+b'+++ATH\r'
        assert wire==expected
        results[name]=dict(passed=True,child_exit=status,configured_seconds=seconds,wire_bytes=len(wire),wire_sha256=sha(case/'serial.bin'),hold_seconds=high[0]['time']-low[0]['time'],status_frames=len(status_frames),ordinary_q_retained=queued)
    return r,results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('software','CTS','policy','CLI','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();software=a.software.resolve();cts=a.CTS.resolve();cohort=a.cohort.resolve();output=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    s,sr=verify_run(software);c,cr=verify_run(cts,True)
    assert (s['parent_sha256'],s['runner_sha256'])==(c['parent_sha256'],c['runner_sha256'])
    for r,folder in [(s,software),(c,cts)]:
        # Map headers contain build timestamps. Their exact admission bytes
        # were checked above against each frozen input, not a later rebuild.
        for name,digest in r['inputs'].items():
            if not name.startswith('build/'):assert sha(ROOT/name)==digest,name
    assert sha(ROOT/'build/terminal/TERMINAL.EXE')==s['parent_sha256']
    assert sha(ROOT/'build/aspect-runner/ASPECT.EXE')==s['runner_sha256']
    policy=read(a.policy);cli=read(a.CLI)
    assert policy['passed'] and cli['passed'] and len(cli['cases'])==23
    assert policy['runner_sha256']==cli['runner_sha256']==s['runner_sha256']
    assert [r['inputs'] for r in policy['cases']]==[3619,18,8704,9] and all(r['passed'] for r in policy['cases'])
    assert sha(ROOT/'standalone/check_serial_wait_policy.py')==policy['test_sha256']
    assert '23 cases 138 checks 0 failures' in cli['DOS_summary']
    for name,digest in cli['captures'].items():assert sha(a.CLI.parent/name)==digest,name
    cohort.mkdir()
    for item in (software,cts,a.policy.parent.resolve(),a.CLI.parent.resolve(),Path(__file__)):
        target=cohort/item.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if item.is_dir():shutil.copytree(item,target)
        else:shutil.copy2(item,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    report=dict(passed=True,transmit_stall_component_accepted=True,physical_hardware_accepted=False,full_application_accepted=False,
        parent_sha256=s['parent_sha256'],runner_sha256=s['runner_sha256'],software=sr,CTS=cr,linked_policy_cases=[r['inputs'] for r in policy['cases']],CLI_cases=23,
        cohort=str(cohort.relative_to(ROOT)),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope='Twelve actual8086 DOS cases: four-second XOFF and CTS stalls, 2048-byte resume, short expiry and Escape cancellation with ordinary-key retention. Independent raw wire, DOS return, owner/hardware and transport-framing verification. Linked parser/ring/clock checks remain modeled at BIOS/UART boundaries; CLI uses real DOS inheritance. Maximum3600 is not an hour-long wall-time claim. Separate BBS/audio/process receipts and full F01-F16/hardware acceptance remain required.')
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,software=len(sr),CTS=len(cr))))


if __name__=='__main__':main()
