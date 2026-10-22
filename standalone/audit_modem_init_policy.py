#!/usr/bin/env python3
"""Bind optional init transactions, retry traces and DOS compiler memory regressions."""
import argparse,json,re,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read


def inputs(folder,r):
    for name,digest in r['inputs'].items():assert sha(ROOT/name)==sha(folder/'inputs'/name)==digest


def received(events):
    wire=bytearray();times=[]
    for e in events:
        if e['kind']=='receive':
            data=bytes.fromhex(e['hex']);wire.extend(data);times.extend([e['time']]*len(data))
    return bytes(wire),times


def dos(folder,parent):
    r=read(folder/'checks.json');assert r['passed'] and r['parent_sha256']==parent and len(r['cases'])==9;inputs(folder,r);rows=[]
    expected={('OK',3,True),('delayed',3,True),('error',3,False),('quiet',0,True),('quiet',1,False),('numeric-OK',3,True),('numeric-error',3,False),('multi',3,True),('echo',3,True)}
    assert {(v['policy'],v['wait_seconds'],v['connected']) for v in r['cases']}==expected
    for row in r['cases']:
        case=folder/row['case'];assert row['passed'] and all(row['checks'].values()) and sha(case/'TERMINAL.EXE')==parent
        for name,digest in row['captures'].items():assert sha(case/name)==digest
        events=read(case/'peer-events.json');assert events==row['events'] and all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        wire,times=received(events);prefix=b'ATZ\r'+(b'ATE0\r' if row['policy']=='multi' else b'')
        assert wire==(case/'serial.bin').read_bytes()==prefix+(b'ATDCaseTest:23\r\x1b[1;16R\x1b[?1;2c+++ATH\r' if row['connected'] else b'\x1b')
        assert not any(e['kind']=='dial-before-ready' for e in events)
        replies=[e for e in events if e['kind']=='response']
        if row['connected']:
            start=times[len(prefix)];prior=[bytes.fromhex(e['hex']) for e in replies if e['time']<start]
            if row['policy']=='quiet':assert prior==[]
            elif row['policy']=='numeric-OK':assert prior==[b'\r\n0\r\n']
            elif row['policy']=='echo':assert prior==[b'ATZ\r\nBOOK\r\n OK \r\n']
            else:assert prior==[b'\r\nOK\r\n']*(2 if row['policy']=='multi' else 1)
            if row['policy'] in ('delayed','multi'):
                pending=next(e for e in events if e['kind']==('initialization-pending' if row['policy']=='delayed' else 'second-initialization-pending'))
                ready=next(e for e in events if e['kind']=='initialization-ready' and e['time']>pending['time'])
                assert ready['time']-pending['time']>=pending['delay'] and start>ready['time']
            assert any(bytes.fromhex(e['hex']).startswith(b'CONNECT\r\n') for e in replies)
        elif row['policy']=='quiet':
            assert replies==[] and .9<=times[-1]-times[3]<=2
        else:assert [bytes.fromhex(e['hex']) for e in replies]==([b'\r\nERROR\r\n'] if row['policy']=='error' else [b'\r\n4\r\n'])
        assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes() and (case/'BEFORE.BIN').stat().st_size==42
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists()
        run=read(case/'result.json');assert run['passed'] and run['command'].endswith('/I:'+str(row['wait_seconds']))
        assert 'cputype=8086' in (case/'dosbox.conf').read_text()
        rows.append(dict(case=row['case'],connected=row['connected'],wait_seconds=row['wait_seconds'],wire_hex=wire.hex(),captures=row['captures']))
    return dict(report_sha256=sha(folder/'checks.json'),cases=rows,source_inputs=r['inputs'])


def retry(folder,parent):
    r=read(folder/'checks.json');assert r['passed'] and r['parent_sha256']==parent and len(r['cases'])==4;inputs(folder,r);rows=[]
    for row in r['cases']:
        case=ROOT/row['cohort'];original=read(case.parent/'checks.json');assert original['passed'] and original['parent_sha256']==parent;inputs(case.parent,original)
        assert sha(case/'TERMINAL.EXE')==parent and read(case/'result.json')['command'].endswith(' /I:3')
        for name,digest in row['captures'].items():assert sha(case/name)==digest
        events=read(case/'peer-events.json');wire,times=received(events)
        assert wire==(case/'serial.bin').read_bytes()==b'A\rATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?62;2cready\x1b[1;16R+++ATH\r'
        assert 2.8<=times[2]-times[1]<=5 and abs(row['guard_seconds']-(times[2]-times[1]))<.000001
        sends=[e for e in events if e['kind']=='peer-send-completed'];errors=[e for e in sends if bytes.fromhex(e['hex'])==b'\r\nERROR\r\n']
        assert len(errors)==int(row['case'].startswith('retained'))
        if errors:assert times[1]<=errors[0]['time']<times[2]
        ack=next(e for e in sends if bytes.fromhex(e['hex'])==b'\r\nOK\r\n');assert times[5]<=ack['time']<times[6]
        decoded=bytearray();escaped=False
        for e in events:
            if e['kind']!='transport-receive':continue
            for value in bytes.fromhex(e['hex']):
                if escaped:
                    escaped=False
                    if value!=255:assert value<=7;continue
                elif value==255:escaped=True;continue
                decoded.append(value)
        assert not escaped and bytes(decoded)==wire
        sample=struct.unpack('<12H',(case/'CANCEL.BIN').read_bytes());assert sample[0]==0x434d and sample[1] and sample[3]>8 and sample[4]==sample[5]==0 and sample[6]>8 and sample[7:10]==(1,0,0) and sample[10]>18 and sample[11]==1
        assert (case/'BEFORE.BIN').read_bytes()==(case/'AFTER.BIN').read_bytes() and (case/'BEFORE.BIN').stat().st_size==42
        assert (case/'VECOLD.BIN').read_bytes()==(case/'VECNEW.BIN').read_bytes() and (case/'VECOLD.BIN').stat().st_size==8
        backend=original['emulator'];wrapper=Path(backend['wrapper']);assert sha(wrapper)==backend['wrapper_sha256'] and sha(wrapper.with_name('.dosbox-x-wrapped'))==backend['binary_sha256']
        assert sha(ROOT/'nix/patches/dosbox-dcd-control.patch')==backend['patch_sha256'] and backend['test_backend']
        rows.append(dict(case=row['case'],guard_seconds=row['guard_seconds'],sample=list(sample),captures=row['captures'],cohort=row['cohort']))
    return dict(report_sha256=sha(folder/'checks.json'),cases=rows,scope=r['scope'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('dos','retry','linked-normal','linked-mouse','regressions','compiler','stack','program','source-proof','cli','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();proof=read(a.source_proof/'checks.json');assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==3
    for name,digest in proof['products'].items():assert sha(ROOT/'build'/name)==sha(a.source_proof/'source/build'/name)==digest
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==sha(a.source_proof/'source'/name)==digest
    products=proof['products'];parent=products['terminal/TERMINAL.EXE'];models=[]
    for name,folder in [('terminal',a.linked_normal),('terminal-mouse',a.linked_mouse)]:
        r=read(folder/'checks.json');assert r['passed'] and r['parent_sha256']==products[name+'/TERMINAL.EXE'] and len(r['cases'])==37 and all(c['passed'] for c in r['cases']);inputs(folder,r)
        models.append(dict(product=name,cases=37,report_sha256=sha(folder/'checks.json')))
    actual=dos(a.dos,parent);retries=retry(a.retry,parent)
    reports={}
    for name in ('connection-checks.json','startup-checks.json','resync-normal.json','resync-mouse.json','carrier-normal/checks.json','carrier-mouse/checks.json','hangup-normal.json','hangup-mouse.json','manual-reconnect/checks.json','stock/build/connection-dos/result.json'):
        path=a.regressions/name;r=read(path);assert r['passed'];expected=products[('terminal-mouse' if 'mouse' in name else 'terminal')+'/TERMINAL.EXE']
        assert r.get('parent_sha256',r.get('binary_sha256'))==expected and all(c['passed'] for c in r['cases'])
        reports[name]=dict(sha256=sha(path),groups=len(r['cases']))
    cli=read(a.cli);assert cli['passed'] and cli['options_source_sha256']==sha(ROOT/'src/terminal/options.asm')
    compiler=read(a.compiler/'compiler/checks.json');unit=read(a.compiler/'unit/checks.json');stack=read(a.stack/'stack-checks.json')
    assert compiler['passed'] and compiler['case_count']==2025 and compiler['binary_sha256']==products['aspect-compiler-dos/ASPCOMP.EXE']
    assert unit['passed'] and unit['case_count']==2015
    assert stack['passed'] and stack['corpus_cases']==2043 and stack['candidate_CLI_stack_bytes']==24576 and stack['checked_API_stack_bytes']==16384 and stack['compiler_sha256']==compiler['binary_sha256']
    program=read(a.program);assert program['passed'] and len(program['cases'])==13 and program['parent_sha256']==sha(ROOT/'build/terminal-process/TERMINAL.EXE')
    assert program['child_sha256']==sha(ROOT/'build/aspect-process-parent/ASPECT.EXE')
    for name,digest in program['source_hashes'].items():assert sha(ROOT/name)==sha(a.program.parent/'sources'/name)==digest
    resource_size=10152+2*len(re.findall(r'X\((\w+)\)',(ROOT/'src/aspect/renderer_policy.h').read_text()))
    for case in program['cases']:
        assert case['passed'] and all(case['checks'].values()) and case['compared_parent_bytes']==resource_size
        folder=a.program.parent/case['case'];raw=(folder/'RENDER.BIN').read_bytes();assert raw[-2*resource_size:-resource_size]==raw[-resource_size:]
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and (folder/'BEFORE.BIN').stat().st_size==42
    failed=read(ROOT/'build/aspect-parent-process/init-result-01/result.json');assert not failed['passed']
    failures=[c['case'] for c in failed['cases'] if not c['passed']];assert len(failures)==8 and all(c.startswith('full-') for c in failures)
    result=dict(passed=True,selected_initialization_policy_accepted=True,current_BBS_audio_accepted=False,physical_hardware_accepted=False,full_F03_accepted=False,products=products,
        DOS=actual,retry=retries,linked=models,default_regressions=reports,legacy_CLI=dict(report_sha256=sha(a.cli),inputs=cli['inputs']),
        compiler_memory=dict(corpus_cases=2025,first_pass_cases=2015,checked_stack_cases=2043,CLI_stack_bytes=24576,checked_API_stack_bytes=16384,corpus_sha256=sha(a.compiler/'compiler/checks.json'),unit_sha256=sha(a.compiler/'unit/checks.json'),stack_sha256=sha(a.stack/'stack-checks.json'),program_sha256=sha(a.program),PROGRAM_cases=13,preceding_failed_PROGRAM_cases=failures,preceding_failed_report_sha256=sha(ROOT/'build/aspect-parent-process/init-result-01/result.json')),
        source_proof=dict(report_sha256=sha(a.source_proof/'checks.json'),source_files=len(proof['sources']),original_inputs=[]),source_inputs=proof['sources'],auditor_sha256=sha(Path(__file__)),
        scope='Selected configurable /I initialization policy.74 linked groups, nine actual DOS reply/quiet/multiple-command cases and four strict cancel/retry SOFT/BOTH cases with explicit patched DCD lab provenance; full configured guard drains stale replies before new commands. Peer submission timestamps are not guest consumption timestamps; arbitrary replies later than the configured guard cannot be correlated. Quiet means no initialization acknowledgement, not a fully silent dial. Compiler arenas, compact source ranges and recycled completed control blocks restore13 attached PROGRAM/compiler workflows without reducing24KB stack or grammar; DOS compiler/heap/checked-stack suites and three original-free product reproductions pass. Current-parent BBS/audio, further flow/foreground/physical and full application requirements remain open.')
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,linked=74,DOS=9,retries=4,compiler_cases=2025,PROGRAM_cases=13,source_products=3)))


if __name__=='__main__':main()
