#!/usr/bin/env python3
"""Independent modem-command and child-observed offline PROGRAM audit."""
import argparse,json,re,shutil,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read,ESC


def verify(folder,gap):
    r=read(folder/'checks.json')
    assert r['passed'] and r['gap_reproduced']==gap and r['compatibility_accepted']!=gap
    assert {c['case'] for c in r['cases']}=={'soft','both'} and len(r['cases'])==2
    for name,digest in r['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    rows={}
    for row in r['cases']:
        assert row['passed'] and all(row['checks'].values());case=folder/row['case']
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256']
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case']=='both'))
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists()
        assert struct.unpack('<4H',(case/'OFFLINE.BIN').read_bytes())==(0,6,1,int(gap))
        handoff=(case/'HANDOFF.BIN').read_bytes();assert len(handoff)==10 and handoff[5]==0 and handoff[6]&3==1
        assert (case/'HANDARG.BIN').read_bytes()==b'\x07 /OWNED\r'
        log=(case/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
        dial=(case/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
        assert dial.startswith('127.0.0.1:')
        assert commands==['ATZ','ATD'+dial,('\x13' if gap else '')+'ATZ','ATD'+dial]
        replies=re.findall(r'Modem response: (.*)',log)
        assert replies==['OK','CONNECT 57600','NO CARRIER','ERROR' if gap else 'OK','CONNECT 57600','NO CARRIER']
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        assert [e['session'] for e in events if e['kind']=='connected']==[1,2]
        first=next(e['time'] for e in events if e['kind']=='first-hangup')
        second=next(e['time'] for e in events if e['kind']=='connected' and e['session']==2)
        assert first<second and sum(e['kind']=='completed-hangup' for e in events)==1
        prefix=ESC+b'[1;16R'+ESC+b'[?62;2c'
        wire=(case/'serial.bin').read_bytes();assert wire==prefix+prefix+b'ready'+ESC+b'[1;16R'
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        assert b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and e['session']==1)==prefix
        rows[row['case']]=dict(passed=True,child_parent_state=0,child_parent_status=6,child_parent_carrier_seen=1,child_parent_xoff=int(gap),modem_ERROR_count=int(gap),connections=2,wire_sha256=sha(case/'serial.bin'))
    return r,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','model','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();old,old_rows=verify(a.baseline.resolve(),True);current,rows=verify(a.fixed.resolve(),False)
    assert old['parent_sha256']!=current['parent_sha256']
    model=read(a.model);assert model['passed'] and not model['gap_reproduced'] and model['compatibility_accepted']
    assert len(model['cases'])==4 and all(c['passed'] for c in model['cases']) and model['parent_sha256']==current['parent_sha256']
    assert sha(ROOT/'build/terminal/TERMINAL.EXE')==current['parent_sha256']
    for name,digest in current['inputs'].items():assert sha(ROOT/name)==digest,name
    cohort=a.cohort.resolve();output=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    cohort.mkdir()
    for item in (a.baseline.resolve(),a.fixed.resolve(),a.model.resolve().parent,Path(__file__)):
        target=cohort/item.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if item.is_dir():shutil.copytree(item,target)
        else:shutil.copy2(item,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,offline_PROGRAM_component_accepted=True,physical_hardware_accepted=False,full_application_accepted=False,
        baseline_parent_sha256=old['parent_sha256'],parent_sha256=current['parent_sha256'],baseline=old_rows,fixed=rows,linked_cases=4,
        cohort=str(cohort.relative_to(ROOT)),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope=__doc__+' Actual8086 DOS SOFT/BOTH old/new comparison. Real socket disconnect precedes helper; child observes offline parent and released UART, parent restores and redials. Corrected command stream removes isolated XOFF from second ATZ and ERROR becomes OK while both BBS byte streams stay exact. General helper/Script, sustained pressure, other DCD transitions and physical acceptance remain separate.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
