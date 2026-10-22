#!/usr/bin/env python3
"""Independently audit raw production BBS replay and preserve diagnostic origins."""
import argparse,hashlib,json,re,shutil,struct
from pathlib import Path
from modem import Telnet
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True)
    p.add_argument('--native',type=Path,required=True);p.add_argument('--cohort',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--synchronet-logon-fixture',type=Path,help='Declared temporary synthetic-account daily-logon exemption, restored after this attempt')
    a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    cohort=a.cohort.resolve();output=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    selected={Path(__file__).resolve(),ROOT/'lab/bbs/modem.py'};servers={}
    for name,payload in (('synchronet',b'TQ'),('enigma',b'M\rQ\r')):
        stage=ROOT/'build/bbs-lab/recording'/name/a.label;r=read(stage/'result.json');start=read(stage/'start.json')
        assert r['passed'] and all(r['checks'].values()) and not r['diagnostic_build']
        assert not start['diagnostic_build'] and set(r['sessions'])=={'record','replay'}
        assert sha(stage/'TERMINAL.EXE')==r['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
        assert sha(stage/'ASPECT.EXE')==r['runner_sha256']==sha(ROOT/'build/aspect-runner/ASPECT.EXE')
        assert not read(stage/'frozen-source/build/aspect-runner/manifest.json')['diagnostic_build']
        for path,digest in r['inputs'].items():assert sha(ROOT/path)==sha(stage/'frozen-source'/path)==digest,path
        for path,digest in r['artifacts'].items():assert sha(stage/path)==digest,path
        source=(stage/'PCPLUS.ASP').read_bytes()
        transmitted=b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
        assert transmitted==payload and b'waitfor loc_prompt 30' in source
        assert re.search(rb'transmitraw "[0-9A-F]+"\r\nendproc\r\n$',source),'Stop-only RX must not add a wait'
        assert (stage/'COMPILE.OK').read_bytes().strip()==b'PASS' and (stage/'RECORD.ASX').stat().st_size>0
        sessions={}
        for mode,session in r['sessions'].items():
            assert session['passed'] and all(session['checks'].values())
            folder=(ROOT/session['result']).parent;run=read(folder/'result.json')
            assert run['passed'] and all(run['checks'].values()) and run['binary_sha256']==r['binary_sha256']
            assert run['keyboard_input']==start['schedules'][mode]
            assert (folder/'BEFORE.BIN').stat().st_size==42
            assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
            for path,digest in session['artifacts'].items():assert sha(folder/path)==digest,path
            wire,_=Telnet().feed((folder/'bbs-sent.bin').read_bytes())
            user=re.sub(rb'\x1b\[(?:\?[0-9;]*c|[0-9]+;[0-9]+R)',b'',wire)
            assert user==bytes.fromhex(session['user_hex'])
            assert user.endswith(payload*(1 if mode=='record' else 2)+b'+++ATH\r')
            plain=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',(folder/'display.bin').read_bytes()).decode('cp437')
            if name=='synchronet':
                assert 'Logging on to LoC Protocol Lab as LABUSER' in plain
                assert plain.count('■ File ■')==(1 if mode=='record' else 2)
                assert '■ Main ■' in plain[plain.rfind('■ File ■'):]
                assert '■ Main ■' in (folder/'screen.txt').read_text()
                assert 'Unrecognized command' not in plain
            else:
                rows=[json.loads(line) for line in (folder/'server-session.jsonl').read_text().splitlines()]
                ids={row['sessionId'] for row in rows if row.get('msg')=='User "loclab" successfully logged in'}
                assert len(ids)==1
                menus=[row['menuName'] for row in rows if row.get('menuName')]
                assert menus[menus.index('mainMenu'):]==['mainMenu']+['messageBaseMainMenu','mainMenu']*(1 if mode=='record' else 2)
            sessions[mode]=dict(result=str((folder/'result.json').relative_to(ROOT)),seconds=run['seconds'],checks=session['checks'])
            selected.update(p for p in folder.rglob('*') if p.is_file())
        selected.update(p for p in stage.rglob('*') if p.is_file())
        servers[name]=dict(binary_sha256=r['binary_sha256'],runner_sha256=r['runner_sha256'],
            source_sha256=sha(stage/'PCPLUS.ASP'),bytecode_sha256=sha(stage/'RECORD.ASX'),payload_hex=payload.hex(),sessions=sessions)
        # The observer proves the cause, not production acceptance. Its old
        # terminal source hashes need only match its preserved frozen copies.
        trace=ROOT/'build/bbs-lab/recording'/name/'recorder-trace-01';diagnostic=read(trace/'result.json')
        assert diagnostic['diagnostic_build'] and diagnostic['runner_sha256']!=r['runner_sha256']
        for path,digest in diagnostic['inputs'].items():assert sha(trace/'frozen-source'/path)==digest,path
        for path,digest in diagnostic['artifacts'].items():assert sha(trace/path)==digest,path
        records=list(struct.iter_unpack('<7H',(trace/'MATCH.BIN').read_bytes()))
        assert records[-1][0:2]==(3,0)
        script_sent=bytes(row[1] for row in records if row[0]==2 and row[3]==0xd7)
        assert script_sent==(b'TQ' if name=='synchronet' else b'M\r')
        assert records[-1][4]==0,'Diagnostic exposes the timed-out native wait'
        selected.update(p for p in trace.rglob('*') if p.is_file())
        for session in diagnostic['sessions'].values():selected.update(p for p in (ROOT/session['result']).parent.rglob('*') if p.is_file())
    native_path=a.native.resolve();assert native_path.is_relative_to(ROOT/'build')
    native=read(native_path);assert native['passed'] and native['native_cases']==68
    assert native['real_ENiGMA']['old_occurrence_present'] and not native['real_ENiGMA']['old_native_match'] and native['real_ENiGMA']['new_native_match']
    for path,digest in native['inputs'].items():assert sha(ROOT/path)==sha(native_path.parent/'frozen-source'/path)==digest,path
    selected.update(p for p in native_path.parent.rglob('*') if p.is_file())
    logon_fixture=None
    if a.synchronet_logon_fixture:
        path=a.synchronet_logon_fixture.resolve();assert path.is_relative_to(ROOT/'build/bbs-lab')
        state=read(path);assert state['user']=='LABUSER' and state['restored'] and state['before']==state['after']
        assert state['bit']==2048 and state['active']==state['before']|state['bit']
        for operation,restored in [('begin',False),('end',True)]:
            capture=path.with_suffix('.'+operation+'.stdout').read_text()
            values=[json.loads(line.partition('PCPLUS_FIXTURE ')[2]) for line in capture.splitlines() if line.startswith('PCPLUS_FIXTURE ')]
            assert len(values)==1 and values[0]['restored']==restored
            assert all(values[0][key]==state[key] for key in ('number','user','bit','before','active'))
            for suffix in ('.js','.stdout','.stderr'):selected.add(path.with_suffix('.'+operation+suffix))
        selected.update([path,ROOT/'lab/bbs/synchronet_logon_fixture.py'])
        logon_fixture=dict(record=str(path.relative_to(ROOT)),sha256=sha(path),user=state['user'],before=state['before'],active=state['active'],restored=state['restored'],after=state['after'],scope='Temporary owned-account daily-logon exemption, not a terminal compatibility fix or quota-policy test.')
    cohort.mkdir();kept={}
    for path in sorted(selected):
        target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target);assert sha(target)==sha(path)
        kept[str(target.relative_to(ROOT))]=sha(target)
    result=dict(passed=True,selected_modern_BBS_recorder_workflows_accepted=True,full_F13_accepted=False,
        servers=servers,native_prompt_cases=68,custody_sha256=kept,synchronet_logon_fixture=logon_fixture,
        earlier_failures='docs/validation/bbs-recording-failure.json',
        scope='Four production actual DOS sessions: record read-only navigation, compile with DOS ASPCOMP, replay the unedited source in a fresh authenticated BBS session, navigate manually afterward, then normal exit and exact UART/DOS restoration. Separate diagnostic observer and native CPU evidence explain the overlap/stop-only wait fixes. Loopback Hayes model forwards configured shutdown bytes. No software audio, physical modem, transfers, arbitrary prompts or full application acceptance.')
    with output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,production_sessions=4,custody_files=len(kept))))


if __name__=='__main__':main()
