#!/usr/bin/env python3
"""Independent old/new audit of manual hangup under XOFF and clean redial."""
import argparse,json,re,shutil,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read,ESC
from directory_test_support import accounting_check


def verify(folder,gap):
    r=read(folder/'checks.json');assert r['passed'] and r['gap_reproduced']==gap and r['compatibility_accepted']!=gap
    assert len(r['cases'])==2 and {c['case'] for c in r['cases']}=={'soft','both'}
    for name,digest in r['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    rows={}
    for row in r['cases']:
        assert row['passed'] and all(row['checks'].values());case=folder/row['case']
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256']
        prm=(case/'TEST.PRM').read_bytes();assert struct.unpack_from('<H',prm,10)[0]==2
        assert struct.unpack_from('<2H',prm,0x198)==(1,int(row['case']=='both'))
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists()
        delta=1 if gap else 2;assert accounting_check((case/'DIAL.IN').read_bytes(),(case/'TEST.DIR').read_bytes(),1,delta)
        dial=(case/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode();assert dial.startswith('127.0.0.1:')
        log=(case/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
        assert commands==['ATZ','ATD'+dial]*delta
        assert re.findall(r'Modem response: (.*)',log)==['OK','CONNECT 57600','NO CARRIER']*delta
        wire=(case/'serial.bin').read_bytes();prefix=ESC+b'[1;16R'+ESC+b'[?62;2c'
        assert wire==prefix+b'arm'+(b'' if gap else prefix+b'ready'+ESC+b'[1;16R')
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        assert [e['session'] for e in events if e['kind']=='connected']==list(range(1,delta+1))
        paused=[e for e in events if e['kind']=='xoff'];closed=[e for e in events if e['kind']=='first-DTR-close']
        assert len(paused)==len(closed)==1 and paused[0]['hex']=='13' and 1.5<closed[0]['time']-paused[0]['time']<4
        assert not any(e['kind']=='first-hangup' for e in events)
        sent=[bytes.fromhex(e['hex']) for e in events if e['kind']=='send']
        assert all(b'\x11' not in b for b in sent)
        assert sum(e['kind']=='completed-hangup' for e in events)==int(not gap)
        if not gap:
            second=next(e['time'] for e in events if e['kind']=='connected' and e['session']==2)
            assert second>closed[0]['time']
            query=next(e['time'] for e in events if e['kind']=='send' and e['hex']==(ESC+b'[6n').hex())
            response=b'';delay=None
            for e in events:
                if e['kind']=='receive' and e['session']==2 and e['time']>=query:
                    response+=bytes.fromhex(e['hex'])
                    if ESC+b'[1;16R' in response:delay=e['time']-query;break
            assert delay is not None and 0<=delay<1
        else:delay=None
        cfg=(case/'dosbox.conf').read_text();assert 'cputype=8086' in cfg and 'p2400 a r m p600 a-h p4300 a-d p4500 r e a d y p700 a-x' in cfg
        rows[row['case']]=dict(passed=True,connections=delta,accounting_delta=delta,modem_commands=2*delta,wire_sha256=sha(case/'serial.bin'),DTR_close_after_XOFF_seconds=closed[0]['time']-paused[0]['time'],manual_query_seconds=delay)
    return r,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','model','source-proof','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();old,old_rows=verify(a.baseline.resolve(),True);new,new_rows=verify(a.fixed.resolve(),False)
    assert old['parent_sha256']!=new['parent_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
    for name,digest in new['inputs'].items():assert sha(ROOT/name)==digest,name
    model=read(a.model);assert model['passed'] and not model['gap_reproduced'] and model['compatibility_accepted'] and len(model['cases'])==4
    assert model['parent_sha256']==new['parent_sha256'] and all(c['passed'] and c['retry_state']==5 and bytes.fromhex(c['retry_wire_hex'])==b'ATZ\rATDLocal.Example:2323\r' for c in model['cases'])
    source=read(a.source_proof);assert source['passed'] and source['original_inputs']==[] and len(source['products'])==26
    assert all(v['expected']==v['actual'] for v in source['products'].values()) and source['products']['terminal/TERMINAL.EXE']['actual']==new['parent_sha256']
    for name,digest in source['sources'].items():assert sha(ROOT/name)==digest,name
    text=(ROOT/'src/terminal/connection.asm').read_text();assert '.finished:\n call connection_uart_clear_service\n' in text
    assert re.search(r'pushf\s+cli\s+call connection_flow_retire\s+popf\s+mov word \[connection_state\],0',text)
    cohort=a.cohort.resolve();output=a.output.resolve();assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists();cohort.mkdir()
    for item in (a.baseline.resolve(),a.fixed.resolve(),a.model.resolve().parent,a.source_proof.resolve().parent,Path(__file__)):
        target=cohort/item.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if item.is_dir():shutil.copytree(item,target)
        else:shutil.copy2(item,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()};(cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,manual_hangup_reconnect_component_accepted=True,physical_hardware_accepted=False,full_application_accepted=False,baseline_parent_sha256=old['parent_sha256'],parent_sha256=new['parent_sha256'],baseline=old_rows,fixed=new_rows,linked_hangup_cancel_cases=4,source_products=26,cohort=str(cohort.relative_to(ROOT)),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope='Two old/new actual8086 SOFT/BOTH Alt-H under XOFF cases. Configured sender timeout then DTR drop closes first BBS socket; no peer XON or first-session close. Old parent cannot start second init, corrected parent opens second socket with exact init/dial/manual/query/accounting and full hardware cleanup. Four linked cases also cover canceled initialization before DCD high; that cancellation path is hardware-modeled, not actual DOS. Existing APIs and DIRECT lifetime remain separate regressions. No physical or full F01-F16 acceptance.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,fixed_cases=len(new_rows),linked_cases=4)))


if __name__=='__main__':main()
