#!/usr/bin/env python3
"""Independent raw command, socket, flow and cleanup audit of modem reconnect."""
import argparse,hashlib,json,re,shutil,struct
from pathlib import Path
from audit_aspect_abort_carrier import ROOT,sha,read,verify_process,verify_modem
from directory_test_support import accounting_check
ESC=b'\x1b'
PREFIX=b'\x13\x11'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'
SECOND=PREFIX+ESC+b'[1;22RSECONDOK\x13\x11ready'+ESC+b'[1;25R'


def verify(folder,gap):
    r=read(folder/'checks.json')
    assert r['passed'] and r['gap_reproduced']==gap and r['compatibility_accepted']!=gap
    for name,digest in r['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    assert {row['case'] for row in r['cases']}=={'soft','both'}
    results={}
    for row in r['cases']:
        assert row['passed'] and all(row['checks'].values())
        case=folder/row['case']
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256'] and sha(case/'ASPECT.EXE')==r['runner_sha256']
        raw=(case/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw)
        assert head[:4]==(0x524e,1,1,1) and head[6]==14
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        disconnected,stale,reconnected=struct.unpack('<3H',raw[-6:])
        assert disconnected>18 and reconnected>18 and stale==0
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        assert (case/'PASS.TXT').is_file() and not (case/'FAIL.TXT').exists()
        assert (case/'SECOND.OK').read_bytes()==b'RECONNECTED'
        assert accounting_check((case/'DIAL.IN').read_bytes(),(case/'TEST.DIR').read_bytes(),1,2)
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case']=='both'))
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        assert [e['session'] for e in events if e['kind']=='connected']==[1,2]
        for kind in ('first-hangup','completed-hangup','xoff'):
            assert sum(e['kind']==kind for e in events)==1
        first_drop=next(e['time'] for e in events if e['kind']=='first-hangup')
        second_connect=next(e['time'] for e in events if e['kind']=='connected' and e['session']==2)
        assert second_connect>first_drop
        assert next(e['time'] for e in events if e['kind']=='xoff')<first_drop
        wires={session:b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and e['session']==session) for session in (1,2)}
        assert wires[1]==PREFIX and wires[2]==SECOND
        assert (case/'serial.bin').read_bytes()==PREFIX+SECOND
        assert bytes.fromhex(next(e['hex'] for e in events if e['kind']=='xoff'))==b'\x13'
        banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0cLOGIN:'
        assert [(e['session'],bytes.fromhex(e['hex'])) for e in events if e['kind']=='send']==[(1,banner),(2,banner),(2,ESC+b'[6nEND'),(2,ESC+b'[6n')]
        query=next(e['time'] for e in events if e['kind']=='send' and e['hex']==(ESC+b'[6n').hex())
        tail=b'';replied=None
        for e in events:
            if e['kind']=='receive' and e['session']==2 and e['time']>=query:
                tail+=bytes.fromhex(e['hex'])
                if ESC+b'[1;25R' in tail:replied=e['time'];break
        assert replied is not None and 0<=replied-query<1
        assert replied<next(e['time'] for e in events if e['kind']=='completed-hangup')
        log=(case/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
        dial=(case/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
        assert dial.startswith('127.0.0.1:') and commands==['ATZ','ATD'+dial,('\x13\x11' if gap else '')+'ATZ','ATD'+dial]
        replies=re.findall(r'Modem response: (.*)',log)
        assert replies==['OK','CONNECT 57600','NO CARRIER','ERROR' if gap else 'OK','CONNECT 57600','NO CARRIER']
        assert len((case/'SCREEN.BIN').read_bytes())==4000
        assert (case/'SCREEN.BIN').read_bytes()[3840+71*2:3840+79*2:2]==b'OFF-LINE'
        results[row['case']]=dict(passed=True,connections=2,first_child_exit=14,second_script='RECONNECTED',native_call_accounting_delta=2,
            dirty_initialization=gap,modem_error_count=int(gap),modem_command_kinds=['ATZ','ATD',('XOFF+XON+ATZ' if gap else 'ATZ'),'ATD'],
            first_wire_bytes=len(PREFIX),second_wire_bytes=len(SECOND),second_wire_sha256=hashlib.sha256(wires[2]).hexdigest(),
            whole_wire_sha256=sha(case/'serial.bin'),
            manual_query_seconds=replied-query,disconnected_ticks=disconnected,reconnected_ticks=reconnected,
            parent_stale_pause_seen=stale)
    return r,results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','model','flow-success','flow-entry','flow-fault','CTS','source-proof','diagnostic-proof','process','program','confirmation','modem','parent-carrier','cohort','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();paths={k:v.resolve() for k,v in vars(a).items()}
    assert paths['output'].is_relative_to(ROOT/'docs/validation') and not paths['output'].exists()
    assert paths['cohort'].is_relative_to(ROOT/'build') and not paths['cohort'].exists()
    old,baseline=verify(paths['baseline'],True);current,fixed=verify(paths['fixed'],False)
    assert old['parent_sha256']!=current['parent_sha256'] and old['runner_sha256']!=current['runner_sha256']
    model=read(paths['model']);assert model['passed'] and len(model['cases'])==42 and all(c['passed'] for c in model['cases'])
    assert model['parent_sha256']==current['parent_sha256'] and model['runner_sha256']==current['runner_sha256']
    for name,digest in model['inputs'].items():assert sha(ROOT/name)==sha(paths['model'].parent/'inputs'/name)==digest,name
    from audit_aspect_flow_handoff import success,faults
    resumed=success(paths['flow_success'],False,current['parent_sha256'],current['runner_sha256'])
    entry=success(paths['flow_entry'],True,current['parent_sha256'],current['runner_sha256'])
    flow,flow_fault=faults(paths['flow_fault'],False)
    assert flow['parent_sha256']==current['parent_sha256'] and flow['runner_sha256']==current['runner_sha256']
    cts=read(paths['CTS']);assert cts['passed'] and len(cts['cases'])==2
    assert cts['parent_sha256']==current['parent_sha256'] and cts['runner_sha256']==current['runner_sha256']
    proof=read(paths['source_proof']);diagnostic=read(paths['diagnostic_proof'])
    for r,count in [(proof,26),(diagnostic,23)]:
        assert r['passed'] and r['original_inputs']==[] and len(r['products'])==count
        assert all(p['actual']==p['expected'] for p in r['products'].values())
        for name,digest in r['sources'].items():assert sha(ROOT/name)==digest,name
    assert proof['products']['terminal/TERMINAL.EXE']['actual']==current['parent_sha256']
    assert proof['products']['aspect-runner/ASPECT.EXE']['actual']==current['runner_sha256']
    verify_process(paths['process'],diagnostic['products']['aspect-process/ASPECT.EXE']['actual'])
    program=read(paths['program']);assert program['passed'] and len(program['cases'])==13
    assert program['parent_sha256']==proof['products']['terminal-process/TERMINAL.EXE']['actual']
    assert all(row['passed'] and all(row['checks'].values()) for row in program['cases'])
    confirmation=read(paths['confirmation']);assert confirmation['passed'] and len(confirmation['results'])==10
    assert confirmation['parent_sha256']==current['parent_sha256'] and confirmation['runner_sha256']==current['runner_sha256']
    modem,_=verify_modem(paths['modem'],parent_status=True)
    assert modem['parent_sha256']==current['parent_sha256'] and modem['runner_sha256']==current['runner_sha256']
    from audit_parent_carrier_status import parent_capture
    carrier,_=parent_capture(paths['parent_carrier'],False)
    assert carrier['parent_sha256']==current['parent_sha256'] and carrier['runner_sha256']==current['runner_sha256']
    freeze=[paths[k] for k in ('baseline','fixed','confirmation','modem','parent_carrier','flow_success','flow_entry','flow_fault','CTS')]
    freeze += [paths[k].parent for k in ('model','source_proof','diagnostic_proof','process','program')]
    variants={}
    for directory in ('terminal','terminal-mouse','terminal-process'):
        folder=ROOT/'build'/directory;m=read(folder/'manifest.json');assert sha(folder/'TERMINAL.EXE')==m['binary_sha256']
        assert m['memory_layout']['aspect_handoff_bytes']==50
        variants[directory]=dict(sha256=m['binary_sha256'],data_spare=m['memory_layout']['near_spare_bytes'],code_spare=m['memory_layout']['resident_code_spare_bytes'])
        freeze += [folder/'TERMINAL.EXE',folder/'terminal.map',folder/'manifest.json']
    legacy=read(ROOT/'build/modem-carrier-flow/old-child-01/checks.json')
    assert legacy['passed'] and legacy['runner_sha256']==old['runner_sha256'] and legacy['descriptor_version']==6
    assert legacy['UART_writes']==legacy['renderer_requests']==0 and legacy['typed_status']==1
    freeze.append(ROOT/'build/modem-carrier-flow/old-child-01')
    for name in ('legacy-v5-01','parent-v6-01','status-normal-01','status-mouse-01'):
        folder=ROOT/'build/modem-carrier-flow'/name;r=read(folder/'checks.json');assert r['passed']
        freeze.append(folder)
    freeze += [Path(__file__),ROOT/'standalone/test_modem_reconnect_dos.py',ROOT/'standalone/check_modem_carrier_flow.py',
               ROOT/'standalone/audit_aspect_abort_carrier.py',ROOT/'standalone/audit_parent_carrier_status.py',ROOT/'standalone/audit_aspect_flow_handoff.py',
               ROOT/'build/modem-reconnect-dos/baseline-01',ROOT/'build/modem-carrier-flow/model-01',
               ROOT/'build/modem-carrier-model-01.stderr',ROOT/'build/modem-carrier-diagnostic-build-01.stderr']
    segment=re.search(r'^_TEXT\s+CODE\s+AUTO\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',(ROOT/'build/aspect-process/ASPECT.map').read_text(),re.M|re.I)
    assert segment;near_end=int(segment[2],16)+int(segment[3],16);assert near_end<=65536
    cohort=paths['cohort'];cohort.mkdir()
    for source in freeze:
        target=cohort/source.relative_to(ROOT)
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_dir():shutil.copytree(source,target)
        else:shutil.copy2(source,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,clean_virtual_modem_reconnect_accepted=True,full_application_accepted=False,
        parent_sha256=current['parent_sha256'],runner_sha256=current['runner_sha256'],variants=variants,baseline=baseline,fixed=fixed,
        linked_policy_cases=42,actual_DOS_reconnect_cases=2,actual_DOS_modem_regressions=4,actual_DOS_parent_carrier_cases=1,
        actual_DOS_flow_resume_cases=2,actual_DOS_flow_entry_cases=2,actual_DOS_flow_fault_cases=4,actual_DOS_CTS_cases=2,
        flow_resume=resumed,flow_entry=entry,flow_fault=flow_fault,
        confirmation_DOS_cases=10,process_cases=56,attached_PROGRAM_cases=13,source_only_products=dict(application=26,diagnostic=23),
        diagnostic_near_code_remaining=65536-near_end,ABI='ASIOv6 remains50bytes; bit0 is peer TX pause, bit1 identifies a MODEM session with parent-observed high DCD. Legacy1..5 remain supported; renderer capabilities12/13 are unchanged.',
        cohort=str(cohort.relative_to(ROOT)),frozen_files=len(files),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope='SOFT/BOTH actual8086 DOSBox-X virtual modem, first remote TCP drop under XOFF, native disconnect TRANSMIT fails14, Alt-D redial, second automatic script, exact BBS streams/manual query and two call-accounting updates. Old/current BBS streams match; raw modem commands distinguish old XOFF+XON+ATZ/ERROR from new clean ATZ/OK. First-child JFT/file owners and overall hardware are checked; the observer does not capture the second child frame.',
        remaining=['Initially-low or never-observed-high DCD retains the old flow policy. Late/transient DCD, manual hangup/cancel reconnect paths and other modem behavior remain open.',
                   'Configurable longer transmit stalls, long CTS fault handback, RTS/sustained RX pressure, software-audio fault/reconnect, physical Boca/SPA2102 and every full F01–F16 gate remain open.'])
    paths['output'].write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,reconnect_cases=2,linked_cases=42,frozen_files=len(files))))


if __name__=='__main__':main()
