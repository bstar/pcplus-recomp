#!/usr/bin/env python3
"""Independently audit raw production BBS replay and preserve diagnostic origins."""
import argparse,hashlib,json,re,shutil,struct,sys
from pathlib import Path
from modem import Telnet
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True)
    p.add_argument('--synchronet-label',help='Separate preserved cohort label when the Synchronet attempt differs')
    p.add_argument('--init-wait',type=int,choices=range(32768),help='Require explicit initialization wait in every captured DOS invocation')
    p.add_argument('--native',type=Path,required=True);p.add_argument('--cohort',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--synchronet-logon-fixture',type=Path,help='Declared temporary synthetic-account daily-logon exemption, restored after this attempt')
    p.add_argument('--mouse-sound',action='store_true',help='Audit the matching combined mouse/sound builds and DOS-child replay wrapper')
    p.add_argument('--notice-input',action='store_true',help='Audit matching capability16 native notice-input products')
    p.add_argument('--notice-help',action='store_true',help='Audit the child-owned PROGRAM help variant')
    p.add_argument('--help-resource',action='store_true',help='Audit the streamed HLP/search variant')
    a=p.parse_args()
    assert not a.notice_input or a.mouse_sound
    assert not a.notice_help or a.notice_input
    assert not a.help_resource or a.notice_help
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    if a.synchronet_label:assert re.fullmatch(r'[A-Za-z0-9_-]+',a.synchronet_label)
    cohort=a.cohort.resolve();output=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    selected={Path(__file__).resolve(),ROOT/'lab/bbs/modem.py',ROOT/'src/aspect/compiler.py',
        ROOT/'nix/flake.nix',ROOT/'nix/flake.lock',ROOT/'tools/bbs-dev'};servers={}
    parent='terminal-mouse-notice-sound' if a.mouse_sound else 'terminal'
    runner='aspect-notice-sound-parent' if a.mouse_sound else 'aspect-runner'
    if a.notice_input:parent='terminal-mouse-notice-input';runner='aspect-notice-input-parent'
    if a.notice_help:runner='aspect-notice-help-parent'
    if a.help_resource:runner='aspect-help-resource-parent'
    for name,payload in (('synchronet',b'TQ'),('enigma',b'M\rQ\r')):
        stage=ROOT/'build/bbs-lab/recording'/name/(a.synchronet_label if name=='synchronet' and a.synchronet_label else a.label);r=read(stage/'result.json');start=read(stage/'start.json')
        assert r['passed'] and all(r['checks'].values()) and not r['diagnostic_build']
        if a.init_wait is not None:
            assert r['initialization_wait_seconds']==start['initialization_wait_seconds']==a.init_wait
        assert not start['diagnostic_build'] and set(r['sessions'])=={'record','replay'}
        assert sha(stage/'TERMINAL.EXE')==r['binary_sha256']==sha(ROOT/'build'/parent/'TERMINAL.EXE')
        assert sha(stage/'ASPECT.EXE')==r['runner_sha256']==sha(ROOT/'build'/runner/'ASPECT.EXE')
        if a.help_resource:
            resource=read(ROOT/'build'/runner/'help-resource.json')
            assert resource['topics']==26 and not resource['original_inputs']
            assert sha(stage/'LOCHELP.HLP')==sha(ROOT/'build'/runner/'LOCHELP.HLP')==resource['sha256']
        assert not read(stage/'frozen-source/build'/runner/'manifest.json')['diagnostic_build']
        for path,digest in r['inputs'].items():assert sha(ROOT/path)==sha(stage/'frozen-source'/path)==digest,path
        for path,digest in r['artifacts'].items():assert sha(stage/path)==digest,path
        source=(stage/'PCPLUS.ASP').read_bytes()
        transmitted=b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
        assert transmitted==payload and b'waitfor loc_prompt 30' in source
        assert re.search(rb'transmitraw "[0-9A-F]+"\r\nendproc\r\n$',source),'Stop-only RX must not add a wait'
        assert (stage/'COMPILE.OK').read_bytes().strip()==b'PASS' and (stage/'RECORD.ASX').stat().st_size>0
        assert (stage/'RECORD.ASX').read_bytes()==compile_source(source.decode('ascii'))
        assert bool(r.get('native_notice_input'))==bool(start.get('native_notice_input'))==a.notice_input
        assert bool(r.get('notice_help'))==bool(start.get('notice_help'))==a.notice_help
        assert bool(r.get('help_resource'))==bool(start.get('help_resource'))==a.help_resource
        assert bool(r.get('mouse_sound'))==bool(start.get('mouse_sound'))==a.mouse_sound
        assert bool(r.get('program_probe'))==bool(start.get('program_probe'))==a.mouse_sound
        if a.mouse_sound:
            prefix=b'run "ABSENT.COM"\r\nif success\r\ntransmitraw "424144"\r\nexit\r\nendif\r\nrun "SUCCESS.COM"\r\nif failure\r\ntransmitraw "424144"\r\nexit\r\nendif\r\n'
            assert source.count(b'proc main\r\n')==1 and not (stage/'ABSENT.COM').exists()
            derived=source.replace(b'proc main\r\n',b'proc main\r\n'+prefix)
            assert (stage/'SOUND.ASP').read_bytes()==derived
            assert (stage/'SOUND.ASX').read_bytes()==compile_source(derived.decode('ascii'))
            assert (stage/'SUCCESS.OK').read_bytes()==b'OK'

        sessions={}
        for mode,session in r['sessions'].items():
            assert session['passed'] and all(session['checks'].values())
            folder=(ROOT/session['result']).parent;run=read(folder/'result.json')
            assert run['passed'] and all(run['checks'].values()) and run['binary_sha256']==r['binary_sha256']
            if a.init_wait is not None:
                assert run['initialization_wait_seconds']==a.init_wait
                command=run['configuration']['command']
                assert command.split().count(f'/I:{a.init_wait}')==1
                assert '\n'+command+'\n' in (folder/'dosbox.conf').read_text()
                port=23231 if name=='synchronet' else 23233
                prefix=f'ATZ\rATDlab.local:{port}\r'.encode('ascii')
                assert (folder/'serial-received.bin').read_bytes().startswith(prefix)
                modem=read(folder/'modem.json')
                commands=[e['command'] for e in modem['events'] if e['kind']=='modem-command']
                assert commands==['ATZ',f'ATDLAB.LOCAL:{port}']
                errors=[e for e in modem['events'] if e['kind']=='error']
                if errors:
                    # Cohorts can close the DOS serial socket with RST
                    # after normal DOS exit. Do not admit an earlier transport
                    # failure or a reset in place of the semantic checks below.
                    assert errors==[modem['events'][-1]]
                    assert errors[0]['message']=='[Errno 104] Connection reset by peer'
                    assert 0<=run['seconds']-errors[0]['seconds']<1
                    assert run['checks']['dos_normal_exit'] and (folder/'PASS.TXT').exists()
                    assert modem['events'][-2]['kind']=='bbs-connected'
            assert run['keyboard_input']==start['schedules'][mode]
            if a.mouse_sound:
                fixture=(folder/'TEST.PRM').read_bytes()
                assert sha(folder/'TEST.PRM')==run['configuration']['sha256']
                assert struct.unpack_from('<H',fixture,0x1bc)==(1,)
                assert struct.unpack_from('<HH',fixture,0x4e4)==(8,4)
                assert run['configuration']['program_sound_word']==1
                if mode=='replay':
                    assert 's o u n d . a s x enter' in run['keyboard_input']
                    assert session['checks']['successful_DOS_child']

            assert (folder/'BEFORE.BIN').stat().st_size==42
            assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
            for path,digest in session['artifacts'].items():assert sha(folder/path)==digest,path
            wire,_=Telnet().feed((folder/'bbs-sent.bin').read_bytes())
            user=re.sub(rb'\x1b\[(?:\?[0-9;]*c|[0-9]+;[0-9]+R)',b'',wire)
            assert user==bytes.fromhex(session['user_hex'])
            assert user.endswith(payload*(1 if mode=='record' else 2)+b'+++ATH\r')
            if a.mouse_sound:assert b'BAD' not in user
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
            sessions[mode]=dict(result=str((folder/'result.json').relative_to(ROOT)),seconds=run['seconds'],checks=session['checks'],transport_close=read(folder/'modem.json')['events'][-1])
            selected.update(p for p in folder.rglob('*') if p.is_file())
        selected.update(p for p in stage.rglob('*') if p.is_file())
        servers[name]=dict(binary_sha256=r['binary_sha256'],runner_sha256=r['runner_sha256'],
            source_sha256=sha(stage/'PCPLUS.ASP'),bytecode_sha256=sha(stage/'RECORD.ASX'),payload_hex=payload.hex(),sessions=sessions)
        if a.mouse_sound:
            servers[name].update(replay_source_sha256=sha(stage/'SOUND.ASP'),
                replay_bytecode_sha256=sha(stage/'SOUND.ASX'),successful_child_sha256=sha(stage/'SUCCESS.COM'),
                compiler_sha256=sha(stage/'ASPCOMP.EXE'),program_sound_word=1,mouse_scales=[8,4])
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
    prerequisites=[]
    if a.mouse_sound:
        failed=ROOT/'build/bbs-lab/recording/enigma/mouse-sound-bbs-03'
        failure=read(failed/'result.json')
        assert not failure['passed'] and set(failure['sessions'])=={'record'}
        checks=failure['sessions']['record']['checks']
        assert not checks['actual_menu_route'] and all(v for k,v in checks.items() if k!='actual_menu_route')
        folder=(ROOT/failure['sessions']['record']['result']).parent
        for path,digest in failure['artifacts'].items():assert sha(failed/path)==digest
        for path,digest in failure['inputs'].items():assert sha(failed/'frozen-source'/path)==digest
        for path,digest in failure['sessions']['record']['artifacts'].items():assert sha(folder/path)==digest
        selected.update(p for p in failed.rglob('*') if p.is_file())
        selected.update(p for p in folder.rglob('*') if p.is_file())
        prerequisites.append(dict(result=str((failed/'result.json').relative_to(ROOT)),
            sha256=sha(failed/'result.json'),passed=False,failed_check='actual_menu_route',
            cause='Fixed-time login recipe advanced before login art completed; navigation was recorded during new-file scan. Separate retry increases login page waits and declines scan explicitly.'))
    cohort.mkdir();kept={}
    for path in sorted(selected):
        target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target);assert sha(target)==sha(path)
        kept[str(target.relative_to(ROOT))]=sha(target)
    result=dict(passed=True,selected_modern_BBS_recorder_workflows_accepted=True,full_F13_accepted=False,
        servers=servers,initialization_wait_seconds=a.init_wait,native_prompt_cases=68,custody_sha256=kept,synchronet_logon_fixture=logon_fixture,
        earlier_failures='docs/validation/bbs-recording-failure.json',
        mouse_sound=a.mouse_sound,program_probe=a.mouse_sound,native_notice_input=a.notice_input,notice_help=a.notice_help,help_resource=a.help_resource,prerequisite_failures=prerequisites,
        scope=('Four actual DOS sessions on the combined mouse/sound build: record read-only BBS navigation, compile the original and a separate DOS-child wrapper with DOS ASPCOMP, replay the wrapper, navigate manually afterward, then exact UART/DOS restoration. The wrapper first runs a missing target and a successful child; conditional BAD wire output is absent. Sound PRM word is enabled; audible output and mouse movement are not observed by this BBS harness. Loopback Hayes model; no physical modem, transfers or full application acceptance.' if a.mouse_sound else 'Four production actual DOS sessions: record read-only navigation, compile with DOS ASPCOMP, replay the unedited source in a fresh authenticated BBS session, navigate manually afterward, then normal exit and exact UART/DOS restoration. Separate diagnostic observer and native CPU evidence explain the overlap/stop-only wait fixes. Loopback Hayes model forwards configured shutdown bytes. No software audio, physical modem, transfers, arbitrary prompts or full application acceptance.'))
    with output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,production_sessions=4,custody_files=len(kept))))


if __name__=='__main__':main()
