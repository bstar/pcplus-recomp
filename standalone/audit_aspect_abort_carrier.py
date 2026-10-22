#!/usr/bin/env python3
"""Independent raw-capture audit of prompt-time native carrier service."""
import argparse,hashlib,itertools,json,re,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
ESC=b'\x1b';QUERY=ESC+b'[6n'
FIELDS=['carrier_armed_seen','carrier_cleared_seen','carrier_pending_seen','carrier_error_seen',
        'carrier_clear_ticks','carrier_depth_seen','carrier_last_key_seen','carrier_tx_paused_seen']


def verify_modem(folder,baseline=False,parent_status=False):
    receipt=read(folder/'checks.json');assert receipt['passed'] and receipt['gap_reproduced']==baseline
    if parent_status:assert not baseline and not receipt['expected_parent_gap']
    assert receipt['compatibility_accepted']!=baseline and receipt['observer_fields']==FIELDS
    for name,digest in receipt['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    results={}
    assert {r['case'] for r in receipt['cases']}==({'CALL-No'} if baseline else {'TX-No','CALL-No','CALL-Yes','XOFF-error'})
    for row in receipt['cases']:
        name=row['case'];case=folder/name;fault=name=='XOFF-error';yes=name=='CALL-Yes';call=name.startswith('CALL')
        assert row['passed'] and all(row['checks'].values())
        for name_,digest in row['captures'].items():assert sha(case/name_)==digest,name_
        events=read(case/'peer-events.json');assert all(a['time']<=b['time'] for a,b in zip(events,events[1:]))
        assert [e['kind'] for e in events].count('connected')==1
        assert [e['kind'] for e in events].count('script-ready')==1
        assert [e['kind'] for e in events].count('hangup')==1
        sends=[bytes.fromhex(e['hex']) for e in events if e['kind']=='send']
        banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+ESC+b'[0cLOGIN:'
        assert sends==[banner,QUERY]+([b'\x13'] if fault else [])
        prefix=b'\x13\x11' if fault else b''
        expected=prefix+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+ESC+b'[1;22R'
        wire=(case/'serial.bin').read_bytes()
        assert wire==expected==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        query=next(e for e in events if e['kind']=='send' and e['hex']==QUERY.hex())
        tail=b'';completed=None
        for event in events:
            if event['kind']=='receive' and event['time']>=query['time']:
                tail+=bytes.fromhex(event['hex'])
                if ESC+b'[1;22R' in tail:completed=event['time'];break
        hangup=next(e['time'] for e in events if e['kind']=='hangup')
        assert completed is not None and 0<=completed-query['time']<=1 and completed<hangup
        raw=(case/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw)
        assert header[:4]==(0x524e,1,1,1) and header[6]==(14 if fault else 13 if yes else 0)
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        observation=struct.unpack('<17H',raw[-34:]);window=observation[:5];prompt=observation[5:9];carrier=dict(zip(FIELDS,observation[9:]))
        assert window[4]==1 and prompt[1:3]==(1,1) and prompt[3]>18
        assert carrier['carrier_armed_seen']==carrier['carrier_last_key_seen']==1
        assert carrier['carrier_error_seen'] in ((0,14) if fault else (0,))
        assert carrier['carrier_cleared_seen']==int(not baseline and not fault)
        assert carrier['carrier_pending_seen']==int(call and not baseline)
        assert carrier['carrier_depth_seen']==int(call and not baseline)
        assert carrier['carrier_tx_paused_seen']==int(fault)
        if not baseline and not fault:assert carrier['carrier_clear_ticks']>18
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        assert (case/'MAIN.OK').exists()==(not yes and not fault)
        if not yes and not fault:assert (case/'MAIN.OK').read_bytes()==b'DECLINED'
        assert (case/'DCD.OK').exists()==(call and not yes)
        if call and not yes:assert (case/'DCD.OK').read_bytes()==b'FRAME37'
        log=(case/'dosbox.log').read_text()
        assert log.count('Modem response: NO CARRIER')==1 and 'Modem response: ERROR' not in log
        assert ('Command sent to modem: ->AT<-' in log)==(name=='TX-No')
        assert ('Command sent to modem: ->ATH<-' in log)==(not fault and not parent_status)
        # The synthetic fixture changes only its selected phone number before
        # execution; the actual ephemeral dial address must match the modem.
        dial=(case/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
        assert 'Command sent to modem: ->ATD'+dial+'<-' in log
        assert len((case/'SCREEN.BIN').read_bytes())==4000
        if parent_status:assert (case/'SCREEN.BIN').read_bytes()[3840+71*2:3840+79*2:2]==b'OFF-LINE'
        results[name]=dict(passed=True,child_exit=header[6],query_reply_seconds=completed-query['time'],
                          prompt_ticks=prompt[3],carrier=carrier,wire_sha256=sha(case/'serial.bin'),
                          stale_ON_LINE_label=b'ON-LINE' in (case/'SCREEN.BIN').read_bytes()[::2])
    return receipt,results


def verify_process(path,identity):
    report=read(path);assert report['passed'] and len(report['cases'])==56 and report['binary_sha256']==identity
    combinations=set()
    for row in report['cases']:
        assert row['passed'] and all(row['checks'].values())
        port,flow,kind=row['port'],row['flow'],row['kind'];combinations.add((port,flow,kind))
        case=path.parent/('com%d-%s-%s'%(port,flow,kind))
        for name,digest in row['artifacts'].items():assert sha(case/name)==digest,name
        assert sha(case/'ASPECT.EXE')==identity
        n=11 if kind=='full' else 2 if kind in ('abort','budget') else 1
        expected=b'\x11D'+b'\x13\x11'*n+b'RF\x13' if flow in 'SB' else b'DRF'
        assert (case/'wire.bin').read_bytes()==expected
        assert (case/'RESULT.TXT').read_text().strip()=='PASS'
        elapsed=struct.unpack('<4H',(case/'DRAIN.BIN').read_bytes())
        assert elapsed[2]+65536*elapsed[3]>=2
        for slot in range(5):assert (case/('SLOT%d.BIN'%slot)).read_bytes()==('SEED%d'%slot).encode()
        assert (case/'SLOT5.BIN').read_bytes()==b'pending5'
    assert combinations==set(itertools.product((1,2),'NSHB',('full','fallback','large','memory','divide','abort','budget')))
    assert report['owned_sources']['standalone/process_capture_idle.asm']==sha(ROOT/'standalone/process_capture_idle.asm')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('modem','baseline','model','process','source-proof','diagnostic-proof','regression','cohort','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();paths={name:getattr(a,name.replace('-','_')).resolve() for name in
                           ('modem','baseline','model','process','source-proof','diagnostic-proof','regression','cohort','output')}
    assert all(path.is_relative_to(ROOT/'build') for name,path in paths.items() if name not in ('output','regression'))
    assert paths['output'].is_relative_to(ROOT/'docs/validation') and not paths['output'].exists() and not paths['cohort'].exists()
    receipt,results=verify_modem(paths['modem']);prior,baseline=verify_modem(paths['baseline'],True)
    assert receipt['parent_sha256']==prior['parent_sha256'] and receipt['runner_sha256']!=prior['runner_sha256']
    model=read(paths['model']);assert model['passed'] and model['compatibility_accepted'] and not model['gap_reproduced'] and len(model['cases'])==8
    assert model['runner_sha256']==receipt['runner_sha256']
    for name,digest in model['frozen_files'].items():assert sha(paths['model'].parent/name)==digest,name
    proof=read(paths['source-proof']);diagnostic=read(paths['diagnostic-proof'])
    for report,count in [(proof,26),(diagnostic,23)]:
        assert report['passed'] and report['original_inputs']==[] and len(report['products'])==count
        assert all(r['actual']==r['expected'] for r in report['products'].values())
        for name,digest in report['sources'].items():assert sha(ROOT/name)==digest,name
    assert proof['products']['aspect-runner/ASPECT.EXE']['actual']==receipt['runner_sha256']
    assert proof['products']['terminal/TERMINAL.EXE']['actual']==receipt['parent_sha256']
    diagnostic_id=diagnostic['products']['aspect-process/ASPECT.EXE']['actual']
    process=verify_process(paths['process'],diagnostic_id)
    regression=read(paths['regression']);assert regression['passed'] and regression['runner_sha256']==receipt['runner_sha256']
    assert len(regression['results'])==10 and regression['attached_PROGRAM_cases']==13
    listing=(ROOT/'build/aspect-process/ASPECT.map').read_text()
    segment=re.search(r'^_TEXT\s+CODE\s+AUTO\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I)
    assert segment;near_start=int(segment[2],16);near_size=int(segment[3],16);near_end=near_start+near_size
    assert near_end<=65536
    freeze=[paths[name].parent for name in ('model','process','source-proof','diagnostic-proof')]
    freeze += [paths['modem'],paths['baseline'],paths['regression'],Path(__file__),ROOT/'standalone/process_capture_idle.asm',
               ROOT/'standalone/test_aspect_process_dos.py',ROOT/'build/aspect-process/runs/abort-carrier-01',
               ROOT/'build/abort-carrier-tail-control-01',ROOT/'build/abort-carrier-CTS-probe-review.json',
               ROOT/'build/abort-carrier-CTS-probe-02.stdout']
    for label in ('virtual-modem-01','virtual-modem-02','native-gap-01','virtual-XOFF-01','virtual-XOFF-02'):
        freeze.append(ROOT/'build/aspect-abort-carrier-dos'/label)
    cohort=paths['cohort'];cohort.mkdir()
    for source in freeze:
        target=cohort/source.relative_to(ROOT)
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_dir():shutil.copytree(source,target)
        else:shutil.copy2(source,target)
    files={str(path.relative_to(cohort)):sha(path) for path in cohort.rglob('*') if path.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,prompt_carrier_service_accepted=True,full_application_accepted=False,
                parent_sha256=receipt['parent_sha256'],runner_sha256=receipt['runner_sha256'],results=results,
                previous_build_counterexample=baseline,linked_groups=8,actual_DOS_modem_cases=4,
                actual_DOS_confirmation_regressions=10,attached_PROGRAM_cases=13,process_cases=56,
                source_only_products=dict(application=26,diagnostic=23),diagnostic_sha256=diagnostic_id,
                diagnostic_near_code=dict(start=near_start,size=near_size,end=near_end,remaining=65536-near_end),
                cohort=str(cohort.relative_to(ROOT)),frozen_files=len(files),files_manifest_sha256=sha(cohort/'files.json'),
                auditor_sha256=sha(Path(__file__)),regression_receipt_sha256=sha(paths['regression']),
                known_gaps=['The final native status line retains ON-LINE after carrier loss in these captures. Full parent status refresh remains unaccepted.',
                            'Parent carrier-seen bookkeeping may miss a high-to-low transition entirely inside automatic script execution; connection.asm requires prior carrier_seen before acting on low. This is a source inference needing a dedicated parent-state test.',
                            'Hardware CTS stalls, full XOFF/XON handback/reconnect, other commands, physical Boca/SPA2102 and all full F01–F16 gates remain open.'],
                capture_boundary='The first22-case raw run missed its final XOFF in one case and remains unaccepted. Unchanged old/current individual controls subsequently passed. The new56-case run requires a source-owned UART-free two-BIOS-tick dwell after DOS application return, before emulator shutdown; exact expected wires are unchanged. DOSBox upstream nullmodem batches host writes on a separate txdelay event; this supports a shutdown-window explanation, not an exhaustive attribution for the failed run.',
                source_reference='https://github.com/joncampbell123/dosbox-x/blob/master/src/hardware/serialport/nullmodem.cpp',
                scope='Native host/carrier service executes on the ordinary modal VM stack; confirmation owns local keys, normal WHEN TX and framed CALL scheduling persist, Yes cancels pending CALL, and XOFF-blocked native TX unwinds with child14 and clean parent return. Actual DOS virtual modem, TCP hangup, exact raw serial/query/control bytes and passive prompt/owner/frame observations. Eight linked groups also cover closed UART and first-error preservation. No physical modem, full parent carrier/status or whole-application acceptance.')
    paths['output'].write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,modem_cases=4,linked_groups=8,process_cases=56,near_code_remaining=65536-near_end)))


if __name__=='__main__':main()
