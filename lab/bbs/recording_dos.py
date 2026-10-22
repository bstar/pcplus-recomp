#!/usr/bin/env python3
"""Record read-only BBS navigation through File/C, compile in DOS and replay.

Uses only the existing loopback synthetic accounts. Credentials precede Record
and are not stored in the generated script. Each attempt uses fresh owned files.
"""
import argparse,asyncio,contextlib,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
import test_dos

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


async def main(args):
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    stage=ROOT/'build/bbs-lab/recording'/args.name/args.label
    assert not stage.exists();stage.mkdir(parents=True)
    inputs={}
    runner='aspect-match-trace' if args.trace else 'aspect-runner'
    for directory,binary in (('terminal','TERMINAL.EXE'),(runner,'ASPECT.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')):
        base=ROOT/'build'/directory;manifest=read(base/'manifest.json')
        assert sha(base/binary)==manifest['binary_sha256']
        if directory==runner:assert bool(manifest['diagnostic_build'])==args.trace
        for name,digest in manifest['sources'].items():
            assert sha(ROOT/name)==digest,name
            assert name not in inputs or inputs[name]==digest
            inputs[name]=digest
        for file in (base/binary,base/'manifest.json'):inputs[str(file.relative_to(ROOT))]=sha(file)
        shutil.copy2(base/binary,stage/binary)
    support=['lab/bbs/test_dos.py','lab/bbs/modem.py','lab/bbs/editor-recipes.json',
        'standalone/test_terminal.py','standalone/terminal_config_fixtures.py',
        'standalone/modem_fixtures.py','standalone/directory_fixtures.py',
        'standalone/directory_test_support.py','src/aspect/compiler.py',
        'build/bbs-lab/'+('synchronet/provenance.json' if args.name=='synchronet' else 'enigma/metadata.json')]
    for path in (Path(__file__).resolve(),*(ROOT/p for p in support)):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        target=stage/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,target);assert sha(target)==digest
    if args.name=='synchronet':
        port=23231
        login='p13000 L A B U S E R enter p2000 L A B P A S S 4 2 enter p8000 space p3000 Q enter p5000 space p4000 '
        navigation='T p3500 Q p3500 '
        payload=b'TQ'
        log=None
    else:
        port=23233
        canonical=read(ROOT/'lab/bbs/editor-recipes.json')['enigma_unsaved']['keyboard_input']
        login=canonical[:canonical.index('M enter')]
        navigation='M enter p3500 Q enter p3500 '
        payload=b'M\rQ\r'
        log=ROOT/'build/bbs-lab/enigma/source/logs/enigma-bbs.log'
    schedules={
        'record':login+'a-z p300 c p300 enter p500 '+navigation+'a-z p300 c p500 escape escape',
        'replay':login+'a-z p300 a p300 r e c o r d . a s x enter p14000 '+navigation,
    }
    if args.trace:
        # Observe a complete 30-second timeout before testing parent return.
        # This is diagnostic timing, never a production acceptance shortcut.
        schedules['replay']=schedules['replay'].replace('p14000','p45000')
    for keys in schedules.values():assert len('ADDKEY p1000 '+keys+' p2000 a-x')<500
    prediction=dict(inputs=inputs,schedules=schedules,expected_payload_hex=payload.hex(),server=args.name,port=port,
        binary_sha256=sha(stage/'TERMINAL.EXE'),diagnostic_build=args.trace,initialization_wait_seconds=args.init_wait,
        runner_sha256=sha(stage/'ASPECT.EXE'),scope=__doc__)
    (stage/'start.json').write_text(json.dumps(prediction,indent=2)+'\n')
    runs={};semantics={}
    for mode,keys in schedules.items():
        label=args.label+'-'+mode;out=ROOT/'build/bbs-lab/results'/args.name/label
        assert not out.exists();out.mkdir(parents=True)
        offset=log.stat().st_size if log else None;inode=log.stat().st_ino if log else None
        options=argparse.Namespace(name=args.name,label=label,port=port,com=2,baud=19200,flow='HARD',packet_delay_ms=0,
            dial_fixture=True,directory_fixture=False,directory_browser=False,entry=3,binary=stage/'TERMINAL.EXE',
            config_fixture=False,keymap_fixture=None,server_log=log,keys=keys,wait=2,timeout=170,init_wait=args.init_wait)
        with (out/'harness.log').open('w') as capture,contextlib.redirect_stdout(capture):
            code=await test_dos.run(options)
        run=read(out/'result.json');runs[mode]=run
        display=(out/'display.bin').read_bytes()
        clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437',errors='replace')
        (out/'display-clean.txt').write_text(clean)
        from modem import Telnet
        wire,_=Telnet().feed((out/'bbs-sent.bin').read_bytes())
        # Remove only terminal device/cursor replies, not arbitrary controls.
        user=re.sub(rb'\x1b\[(?:\?[0-9;]*c|[0-9]+;[0-9]+R)',b'',wire)
        # The declared Hayes model forwards the configured +++~ATH^M shutdown
        # sequence to its TCP peer; it does not emulate escape-to-command mode.
        # Keep this limitation explicit and require its exact suffix rather
        # than treating those modem-owner bytes as recorded user navigation.
        hangup=b'+++ATH\r'
        expected=payload if mode=='record' else payload*2
        checks=dict(DOS_and_hardware=code==0 and run['passed'],
            configured_modem_hangup_observed=user.endswith(hangup),
            actual_navigation_bytes=user.endswith(expected+hangup),
            recording_unchanged_in_replay=mode=='record' or sha(stage/'PCPLUS.ASP')==recorded_sha,
            no_unsupported_terminal='unsupported terminal' not in clean.lower())
        if args.name=='synchronet':
            file_at=clean.find('■ File ■')
            checks.update(authenticated='Logging on to LoC Protocol Lab as LABUSER' in clean,
                file_menu='List Files in dir' in clean and clean.count('■ File ■')==(1 if mode=='record' else 2),
                main_return=file_at>=0 and '■ Main ■' in clean[clean.rfind('■ File ■'):],
                no_unrecognized_command='Unrecognized command' not in clean)
        else:
            assert log.stat().st_ino==inode,'Server log rotated; preserve attempt'
            with log.open('rb') as f:
                f.seek(offset);rows=[json.loads(line) for line in f if line.strip()]
            sessions={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
            own=[r for r in rows if r.get('sessionId') in sessions]
            menus=[r['menuName'] for r in own if r.get('menuName')]
            (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
            start=menus.index('mainMenu') if 'mainMenu' in menus else len(menus)
            expected_route=['mainMenu']+['messageBaseMainMenu','mainMenu']*(1 if mode=='record' else 2)
            checks.update(unique_authenticated_session=len(sessions)==1,
                actual_menu_route=menus[start:]==expected_route)
        semantics[mode]=dict(passed=all(checks.values()),checks=checks,user_hex=user.hex(),
            result=str((out/'result.json').relative_to(ROOT)),artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()})
        if mode=='record':
            source=(stage/'PCPLUS.ASP').read_bytes() if (stage/'PCPLUS.ASP').exists() else b''
            recorded_sha=hashlib.sha256(source).hexdigest()
            recorded=b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
            checks.update(complete_source=source.endswith(b'endproc\r\n'),exact_user_payload=recorded==payload,
                          no_credentials=b'LABUSER' not in source and b'loclab' not in source)
            semantics[mode]['passed']=all(checks.values())
            if not semantics[mode]['passed']:break
            config=fr'''[sdl]
output=surface
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{stage}"
c:
ASPCOMP PCPLUS.ASP RECORD.ASX
if errorlevel 1 goto failed
echo PASS>COMPILE.OK
:failed
exit
'''
            (stage/'compile.conf').write_text(config)
            with (stage/'compile.log').open('w') as capture:
                compiled=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(stage/'compile.conf')],
                    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=capture,stderr=capture,timeout=45)
            assert compiled.returncode==0 and (stage/'COMPILE.OK').exists()
            assert (stage/'RECORD.ASX').read_bytes()==compile_source(source.decode('ascii'))
    checks=dict(both_sessions=len(semantics)==2 and all(s['passed'] for s in semantics.values()),
        sources_unchanged=all(sha(ROOT/name)==digest for name,digest in inputs.items()),
        no_retained_temporary_files=not list(stage.glob('LPR*.TMP')) and not list(stage.glob('LPR*.BAK')))
    result=dict(passed=all(checks.values()),checks=checks,inputs=inputs,sessions=semantics,
        initialization_wait_seconds=args.init_wait,diagnostic_build=args.trace,runner_sha256=sha(stage/'ASPECT.EXE'),
        binary_sha256=prediction['binary_sha256'],expected_payload_hex=payload.hex(),
        artifacts={str(p.relative_to(stage)):sha(p) for p in stage.iterdir() if p.is_file()},
        scope='Actual DOS File/C recording, DOS compilation and File/A replay of read-only menu navigation, followed by a second manual navigation proving parent return, on the existing loopback synthetic BBS account. The Hayes model forwards configured shutdown hangup bytes; escape-to-command modem behavior is not modeled. No audio, physical modem, file transfers or full application acceptance.')
    (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,sessions={k:v['checks'] for k,v in semantics.items()})),flush=True)
    assert result['passed'],'Preserve failed attempt and inspect captures'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('name',choices=('synchronet','enigma'));p.add_argument('--label',required=True)
    p.add_argument('--init-wait',type=int,choices=range(32768),help='Explicit initialization acknowledgement deadline for both DOS sessions')
    p.add_argument('--trace',action='store_true',help='Separate diagnostic ASPECT observer; no production acceptance')
    asyncio.run(main(p.parse_args()))
