#!/usr/bin/env python3
"""Audit v5 flow ownership from raw UART timing and passive DOS observations."""
import argparse,json,shutil,struct,re
from pathlib import Path
from audit_aspect_abort_carrier import ROOT,sha,read,verify_process,verify_modem
ESC=b'\x1b'
FIELDS=('child_paused_ticks','parent_return_ticks','parent_paused_after_return')


def custody(folder,report):
    for name,digest in report['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    for row in report['cases']:
        assert row['passed'] and all(row['checks'].values())
        for name,digest in row['captures'].items():assert sha(folder/row['case']/name)==digest,name


def raw_case(folder,case,parent,child,extra=0):
    assert sha(folder/'TERMINAL.EXE')==parent and sha(folder/'ASPECT.EXE')==child
    raw=(folder/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw)
    assert header[:4]==(0x524e,1,1,1) and header[6]==case
    assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
    before=(folder/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(folder/'AFTER.BIN').read_bytes()
    assert (folder/'PASS.TXT').is_file() and not (folder/'FAIL.TXT').exists()
    events=read(folder/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
    wire=(folder/'serial.bin').read_bytes()
    assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
    return raw,wire,events,struct.unpack('<%dH'%(3+extra),raw[-2*(3+extra):])


def faults(folder,gap):
    r=read(folder/'checks.json');assert r['passed'] and r['gap_reproduced']==gap and r['compatibility_accepted']!=gap
    custody(folder,r);results={}
    assert {row['case'] for row in r['cases']}=={'timeout-soft','timeout-both','cancel-soft','cancel-both'}
    for row in r['cases']:
        mode=row['case'].split('-')[0];case=folder/row['case'];cancel=mode=='cancel'
        raw,wire,events,state=raw_case(case,13 if cancel else 14,r['parent_sha256'],r['runner_sha256'])
        assert state[0]>8 and state[1]>18 and bool(state[2])!=gap
        assert state[2]==0 if gap else state[2]>18
        assert not (case/'BAD.OK').exists() and b'MUSTNOTSEND' not in wire
        expected=b'ATZ\rATDCaseTest:23\r\x13\x11'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY\x13\x11ready'+ESC+(b'[4;1R' if cancel else b'[5;1R')+b'+++ATH\r'
        assert wire==expected
        off=[e for e in events if e['kind']=='xoff-go'];on=[e for e in events if e['kind']=='xon']
        assert len(off)==len(on)==1 and bytes.fromhex(off[0]['hex'])==b'\x13GO' and bytes.fromhex(on[0]['hex'])==b'\x11'
        assert 4<=on[0]['time']-off[0]['time']<4.5
        leaked=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive' and off[0]['time']<e['time']<on[0]['time'])
        application=bytes(c for c in leaked if c not in (17,19))
        assert bool(application)==gap
        query=next(e['time'] for e in events if e['kind']=='parent-query')
        assert (query<on[0]['time'])==gap
        screen=(case/'SCREEN.BIN').read_bytes()[::2]
        assert (b'cancelled' in screen) if cancel else (b'serial 7' in screen)
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case'].endswith('both')))
        results[row['case']]=dict(child_exit=13 if cancel else 14,child_paused_ticks=state[0],parent_paused_ticks=state[2],
                                 premature_application_hex=application.hex(),parent_query_after_XON=not gap,wire_sha256=sha(case/'serial.bin'))
    return r,results


def success(folder,entry,parent,child):
    r=read(folder/'checks.json');assert r['passed'] and r['entry_pause']==entry and len(r['cases'])==2
    custody(folder,r);assert r['parent_sha256']==parent and r['runner_sha256']==child
    result={}
    for row in r['cases']:
        case=folder/row['case'];raw,wire,events,state=raw_case(case,0,parent,child,extra=int(entry))
        assert state[0]>12 and state[1]>18 and state[2]==0
        if entry:assert state[3]==1
        assert (case/'FLOW.OK').read_bytes()==b'RESUMED'
        expected=b'ATZ\rATDCaseTest:23\r\x13\x11'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+b'0123456789ABCDEF'*128+b'\x13\x11ready'+ESC+b'[1;24R+++ATH\r'
        assert wire==expected
        off=[e for e in events if e['kind']==('entry-xoff' if entry else 'xoff-go')];on=[e for e in events if e['kind']=='xon']
        assert len(off)==len(on)==1 and 1.2<=on[0]['time']-off[0]['time']<1.8
        for event in events:
            if event['kind']=='receive' and off[0]['time']<event['time']<on[0]['time']:
                assert set(bytes.fromhex(event['hex']))<={17,19}
        result[row['case']]=dict(child_paused_ticks=state[0],parent_pause_seen_at_entry=bool(entry),payload_bytes=2048,wire_bytes=len(wire),wire_sha256=sha(case/'serial.bin'))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','entry','success','child-model','parent-model','legacy','modem','parent-carrier','source-proof','diagnostic-proof','process','program','confirmation','cohort','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();paths={name:path.resolve() for name,path in vars(a).items()}
    assert paths['cohort'].is_relative_to(ROOT/'build') and not paths['cohort'].exists()
    assert paths['output'].is_relative_to(ROOT/'docs/validation') and not paths['output'].exists()
    old,baseline=faults(paths['baseline'],True);current,fixed=faults(paths['fixed'],False)
    assert old['parent_sha256']!=current['parent_sha256'] and old['runner_sha256']!=current['runner_sha256']
    legacy=read(paths['legacy']);assert legacy['passed'] and legacy['runner_sha256']==old['runner_sha256']
    assert legacy['typed_status']==1 and legacy['UART_writes']==legacy['renderer_requests']==0 and legacy['descriptor_unchanged']
    for name,digest in legacy['inputs'].items():assert sha(paths['legacy'].parent/'inputs'/name)==digest,name
    modem,_=verify_modem(paths['modem'],parent_status=True)
    assert modem['parent_sha256']==current['parent_sha256'] and modem['runner_sha256']==current['runner_sha256']
    from audit_parent_carrier_status import parent_capture
    carrier,_=parent_capture(paths['parent_carrier'],False)
    assert carrier['parent_sha256']==current['parent_sha256'] and carrier['runner_sha256']==current['runner_sha256']
    entry=success(paths['entry'],True,current['parent_sha256'],current['runner_sha256'])
    resumed=success(paths['success'],False,current['parent_sha256'],current['runner_sha256'])
    for key,count,identity in [('child_model',16,current['runner_sha256']),('parent_model',13,current['parent_sha256'])]:
        r=read(paths[key]);assert r['passed'] and len(r['cases'])==count and all(row['passed'] for row in r['cases'])
        assert r.get('runner_sha256',r.get('parent_sha256'))==identity
        for name,digest in r['inputs'].items():assert sha(ROOT/name)==sha(paths[key].parent/'inputs'/name)==digest,name
    proof=read(paths['source_proof']);diagnostic=read(paths['diagnostic_proof'])
    for report,count in [(proof,26),(diagnostic,23)]:
        assert report['passed'] and report['original_inputs']==[] and len(report['products'])==count
        assert all(row['actual']==row['expected'] for row in report['products'].values())
        for name,digest in report['sources'].items():assert sha(ROOT/name)==digest,name
    assert proof['products']['terminal/TERMINAL.EXE']['actual']==current['parent_sha256']
    assert proof['products']['aspect-runner/ASPECT.EXE']['actual']==current['runner_sha256']
    process=verify_process(paths['process'],diagnostic['products']['aspect-process/ASPECT.EXE']['actual'])
    program=read(paths['program']);assert program['passed'] and len(program['cases'])==13
    assert program['parent_sha256']==proof['products']['terminal-process/TERMINAL.EXE']['actual']
    for row in program['cases']:assert row['passed'] and all(row['checks'].values())
    confirmation=read(paths['confirmation']);assert confirmation['passed'] and len(confirmation['results'])==10
    assert confirmation['parent_sha256']==current['parent_sha256'] and confirmation['runner_sha256']==current['runner_sha256']
    variants={};freeze=[paths[k] for k in ('baseline','fixed','entry','success','confirmation','modem','parent_carrier')]
    freeze += [paths[k].parent for k in ('child_model','parent_model','legacy','source_proof','diagnostic_proof','process','program')]
    for directory in ('terminal','terminal-mouse','terminal-process'):
        folder=ROOT/'build'/directory;manifest=read(folder/'manifest.json');assert sha(folder/'TERMINAL.EXE')==manifest['binary_sha256']
        assert manifest['memory_layout']['aspect_handoff_bytes']==50
        variants[directory]=dict(sha256=manifest['binary_sha256'],data_spare=manifest['memory_layout']['near_spare_bytes'],code_spare=manifest['memory_layout']['resident_code_spare_bytes'])
        freeze += [folder/'TERMINAL.EXE',folder/'manifest.json',folder/'terminal.map']
    supports={}
    for directory,leaf,expected in [('aspect-render-client','checks.json',current['runner_sha256']),('aspect-keyboard','key-client-checks.json',current['runner_sha256']),('aspect-foreground-delay','checks.json',current['runner_sha256']),('aspect-abort-owner','checks.json',current['runner_sha256']),('terminal','script-launch-live-checks.json',current['parent_sha256']),('terminal-abort-confirm','checks.json',current['parent_sha256']),('terminal-abort-confirm-mouse','checks.json',variants['terminal-mouse']['sha256']),('parent-carrier-status/flow-handoff-normal-01','checks.json',current['parent_sha256']),('parent-carrier-status/flow-handoff-mouse-01','checks.json',variants['terminal-mouse']['sha256'])]:
        path=ROOT/'build'/directory/leaf;r=read(path);assert r['passed']
        assert r.get('runner_sha256',r.get('binary_sha256',r.get('parent_sha256',r.get('terminal_sha256'))))==expected
        supports[str(path.relative_to(ROOT))]=dict(cases=len(r['cases']),sha256=sha(path));freeze.append(path)
    serial_folder=ROOT/'build/aspect-serial';serial=read(serial_folder/'checks.json');serial_manifest=read(serial_folder/'manifest.json')
    assert serial['passed'] and serial['inputs']==108 and all(row['passed'] for row in serial['groups'])
    assert serial['binary_sha256']==serial_manifest['binary_sha256']==sha(serial_folder/'SERIAL.EXE')
    for name,digest in serial_manifest['sources'].items():assert sha(ROOT/name)==digest,name
    supports['build/aspect-serial/checks.json']=dict(groups=len(serial['groups']),inputs=108,sha256=sha(serial_folder/'checks.json'))
    freeze += [serial_folder/'checks.json',serial_folder/'manifest.json',serial_folder/'SERIAL.EXE',serial_folder/'serial.map',ROOT/'standalone/check_aspect_serial.py']
    freeze.append(ROOT/'standalone/audit_parent_carrier_status.py')
    segment=re.search(r'^_TEXT\s+CODE\s+AUTO\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',(ROOT/'build/aspect-process/ASPECT.map').read_text(),re.M|re.I)
    assert segment;end=int(segment[2],16)+int(segment[3],16);assert end<=65536
    freeze += [Path(__file__),ROOT/'standalone/test_aspect_flow_fault_dos.py',ROOT/'standalone/test_aspect_flow_return_dos.py',ROOT/'standalone/check_aspect_flow_handoff.py',ROOT/'standalone/check_parent_flow_handoff.py',ROOT/'standalone/audit_aspect_abort_carrier.py',ROOT/'build/aspect-flow-fault-dos/baseline-01',ROOT/'build/aspect-flow-handoff/parent-01']
    cohort=paths['cohort'];cohort.mkdir()
    for source in freeze:
        target=cohort/source.relative_to(ROOT)
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_dir():shutil.copytree(source,target)
        else:shutil.copy2(source,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,flow_handoff_accepted=True,full_application_accepted=False,
        parent_sha256=current['parent_sha256'],runner_sha256=current['runner_sha256'],variants=variants,
        baseline=baseline,fixed=fixed,entry=entry,resume=resumed,child_linked_cases=16,parent_linked_cases=13,legacy_child_rejection=legacy,supporting_checks=supports,
        actual_DOS_fault_cases=4,actual_DOS_entry_cases=2,actual_DOS_resume_cases=2,confirmation_DOS_cases=10,actual_DOS_modem_cases=4,actual_DOS_parent_carrier_cases=1,
        process_cases=56,attached_PROGRAM_cases=13,source_only_products=dict(application=26,diagnostic=23),
        diagnostic_near_code_remaining=65536-end,cohort=str(cohort.relative_to(ROOT)),frozen_files=len(files),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        ABI='ASIOv5 extends v4 from48 to50bytes with one guarded input/output peer-pause word. Legacy v1..v4 remain accepted. Renderer capabilities12/13 are unchanged; an older child rejects v5 before UART acquisition.',
        scope='Real DOSBox-X8086 SOFT/BOTH, remote XOFF/XON, exact complete wires and passive parent/child observations. Old/current fault wires are identical but their timing differs: old parent transmits ready/query before XON; current parent keeps TX paused. Native input preload precedes ISR installation; current parent adopts valid returned pause before UART restoration. Cleanup and source-only regression scopes are explicit.',
        remaining=['The transmit pending bound remains36BIOS ticks; configurable longer-stall policy is still required.',
                   'CTS/RTS stalls, sustained RX pressure, carrier reconnect, software-audio flow pressure and physical UART/modem timing remain open.',
                   'Every whole-application F01–F16 gate remains open.'])
    paths['output'].write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,actual_DOS_cases=8,frozen_files=len(files),diagnostic_near_code_remaining=65536-end)))


if __name__=='__main__':main()
