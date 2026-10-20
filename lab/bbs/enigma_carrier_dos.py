#!/usr/bin/env python3
"""Interrupt a real DOS receive, observe carrier loss, redial and retry."""
import argparse,asyncio,json,os,re,shutil,struct,sys
from pathlib import Path
from test_transfer_dos import timestamp,offset_after
from carrier_relay import carrier_relay
from carrier_notice_watch import SAMPLER
from enigma_key_stream_fixture import ROOT,PORT,owned,verify_running
from enigma_notes_dos import sha,messages
from enigma_script_login import source as login_source
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
sys.path.insert(0,str(ROOT/'standalone'))
from directory_fixtures import prm,directory
from directory_test_support import accounting_check
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
import zlib


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    candidate=owned(args.candidate);log=verify_running(candidate)
    fixture=json.loads((candidate/'search-instance.json').read_text());assert fixture['transfer_bytes']>=32768
    inputs={p:candidate/p for p in [*fixture['fixture_inputs'],*fixture['source_modules']]}
    for p,h in {**fixture['fixture_inputs'],**fixture['source_modules']}.items():assert sha(inputs[p])==h,p
    archive=fixture['archives'][1];archive_path=candidate/'file_base/pcplus_games'/archive['name']
    payload=archive_path.read_bytes();assert sha(archive_path)==archive['sha256']
    wire_name=archive['name'].upper();local=f'{zlib.crc32(wire_name.encode()):08X}.ZIP'
    out=ROOT/'build/bbs-lab/results/enigma'/args.label;out.mkdir(parents=True,exist_ok=False)
    stage=out/'program';stage.mkdir();target=out/'RECV';target.mkdir()
    for rel in ('terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE'):
        original=ROOT/'build'/rel;shutil.copyfile(original,stage/original.name);inputs[rel]=original;inputs['staged/'+original.name]=stage/original.name
    script=login_source();(stage/'LOGON.ASP').write_bytes(script.replace('\n','\r\n').encode('ascii'))
    inputs.update(login=stage/'LOGON.ASP',runner=Path(__file__),relay=ROOT/'lab/bbs/carrier_relay.py',
        observer=ROOT/'lab/bbs/carrier_notice_watch.py',observer_base=ROOT/'lab/bbs/zmodem_label_watch.py',
        sampler_base=ROOT/'standalone/test_terminal.py',auditor=ROOT/'lab/bbs/audit_zmodem.py',modem_codec=ROOT/'lab/bbs/modem.py')
    before={p:sha(f) for p,f in inputs.items()};posts=messages(candidate)
    boundary=dict(inode=log.stat().st_ino,byte_offset=log.stat().st_size)
    (out/'server-log-start.json').write_text(json.dumps(boundary)+'\n')
    sampler=SAMPLER
    for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(0x2f8+off))
    (out/'sampler.asm').write_text(sampler)
    import subprocess
    subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    menu='c-y F enter p1600 S enter p1600 P C P L U S space P R O B E space 0 1 enter p2000 enter p1600 '
    keys='p85000 '+menu+'d p1500 a p1000 enter p15000 enter p1200 a-d p85000 '+menu+'d p1500 a p1000 enter p65000 enter p1200 n p1600 p2000 a-x'
    assert len('ADDKEY '+keys)<500
    snapshots=[];finished=asyncio.Event()
    async with carrier_relay(PORT) as (relay_port,sessions):
        image=bytearray(prm(port=2,baud=5,soft=0,hard=1))
        init=b'AT&K3^M';image[0x18:0x47]=init.ljust(47,b'\0')
        image[0x42c:0x42e]=b'\x01\0';path=b'D:\\RECV\\\0';image[0x31c:0x31c+len(path)]=path
        (out/'TEST.PRM').write_bytes(image)
        book=bytearray(directory(entry=3,target=f'127.0.0.1:{relay_port}'.encode(),port=2,baud=5))
        at=250+2*114;book[at+52:at+61]=b'LOGON\0\0\0\0';(out/'TEST.DIR').write_bytes(book)
        async def watch():
            while not finished.is_set():
                partial=target/'PCRX.$$$'
                if len(sessions)==1 and not sessions[0].interrupted and partial.is_file() and partial.stat().st_size>=1024:
                    data=partial.read_bytes();assert data==payload[:len(data)] and len(data)<len(payload)
                    snapshots.append(dict(kind='partial-before-interruption',bytes=len(data),sha256=sha(partial),files=sorted(p.name for p in target.iterdir())))
                    trace=stage/'LOGIN.LOG';snapshots[-1]['first_login_trace']=trace.read_text() if trace.exists() else None
                    sessions[0].interrupt()
                if len(sessions)>=2 and len(snapshots)==1:
                    snapshots.append(dict(kind='before-second-login',files=sorted(p.name for p in target.iterdir())))
                await asyncio.sleep(.05)
        watcher=asyncio.create_task(watch())
        config=f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=modem listenport:0
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{stage}"
mount d "{out}"
c:
ASPCOMP LOGON.ASP LOGON.ASX >D:\\COMPILE.TXT
if errorlevel 1 goto failed
D:\\SNAP B
ADDKEY {keys}
TERMINAL @D:\\TEST.PRM /E:D:\\TEST.DIR /N:3
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\SNAP A
exit
'''
        (out/'dosbox.conf').write_text(config)
        try:
            with (out/'dosbox.log').open('w') as capture:
                process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf'),
                    cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=capture,stderr=capture)
                try:code=await asyncio.wait_for(process.wait(),330)
                except asyncio.TimeoutError:
                    process.terminate()
                    try:await asyncio.wait_for(process.wait(),5)
                    except asyncio.TimeoutError:process.kill();await process.wait()
                    code=-1
        finally:finished.set();await watcher
    for session in sessions:session.save(out/f'connection-{session.index}')
    (out/'snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
    raw=(out/'LABELS.BIN').read_bytes() if(out/'LABELS.BIN').exists() else b''
    notices=[]
    if len(raw)==2566:
        magic,count,ticks=struct.unpack_from('<3H',raw)
        if magic==0x4e5a and 0<count<=16:notices=[raw[6+i*160:6+(i+1)*160:2].decode('cp437') for i in range(count)]
    initial=(out/'BEFORE.BIN').read_bytes() if(out/'BEFORE.BIN').exists() else b''
    final=(out/'AFTER.BIN').read_bytes() if(out/'AFTER.BIN').exists() else b''
    checks=dict(DOS_normal_exit=code==0 and(out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists(),
        hardware_restored=len(initial)==42 and initial==final,
        inputs_unchanged=before=={p:sha(f) for p,f in inputs.items()},
        PRM_unchanged=(out/'TEST.PRM').read_bytes()==image,
        DOS_compiler_exact=(stage/'LOGON.ASX').exists() and(stage/'LOGON.ASX').read_bytes()==compile_source(script),
        both_script_logins=snapshots and snapshots[0].get('first_login_trace')=='STARTAUTHREADY' and(stage/'LOGIN.LOG').exists() and(stage/'LOGIN.LOG').read_bytes()==b'STARTAUTHREADY',
        two_network_connections=len(sessions)==2 and sessions[0].interrupted and not sessions[1].interrupted,
        partial_removed_before_reconnect=len(snapshots)==2 and snapshots[1]['files']==[],
        actual_carrier_loss_notice=any('carrier lost' in text.lower() for text in notices),
        confirmed_finish_notice=any('RX complete' in text for text in notices) and not any('unconfirmed' in text for text in notices),
        retry_file_exact=(target/local).is_file() and(target/local).read_bytes()==payload,
        only_expected_file={p.name for p in target.iterdir()}=={local},no_post_saved=posts==messages(candidate),
        directory_two_connections=accounting_check(bytes(book),(out/'TEST.DIR').read_bytes(),3,2))
    errors=[];protocol={}
    try:
        assert len(sessions)==2
        first=sessions[0];offers=[h for h in scan(first.display) if h['type']==4]
        assert offers and metadata(packet(first.display,offers[0]['end'],offers[0]['format'])['payload'])==(wire_name,len(payload))
        assert not any(h['type']==11 for h in scan(first.display)),'First transfer completed before network loss'
        second=sessions[1];retry=audit_batch(bytes(second.display),{wire_name:payload})
        post=bytes(second.keyboard).index(b'n',offset_after(second.trace,'dos',timestamp(second.trace,'bbs',retry['end']-1)))
        when=timestamp(second.trace,'dos',post);retry['controls']=audit_controls(retry,bytes(second.keyboard),second.trace,'bbs',when,False)
        after=offset_after(second.trace,'bbs',when);assert after is not None
        assert b'NFO | lines 1-15/24' in second.display[after:] and b'PCPLUS NFO LINE 01 : synthetic game 01' in second.display[after:]
        for f in retry['files']:f.pop('source')
        protocol=retry;checks['exact_retry_protocol_then_NFO']=True
    except (AssertionError,ValueError,TypeError) as e:errors.append(str(e));checks['exact_retry_protocol_then_NFO']=False
    assert log.stat().st_ino==boundary['inode']
    rows=[json.loads(l) for l in log.read_bytes()[boundary['byte_offset']:].splitlines() if l.strip()]
    authenticated={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
    own=[r for r in rows if r.get('sessionId') in authenticated]
    (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
    checks['two_authenticated_sessions']=len(authenticated)==2
    result=dict(passed=all(checks.values()) and not errors,checks=checks,errors=errors,notices=notices,snapshots=snapshots,
        terminal_sha256=before['terminal/TERMINAL.EXE'],input_hashes=before,protocol=protocol,
        scope='One real DOS process, built-in DOSBox-X Hayes modem with RTS/CTS and emulated DCD, Telnet-only bridge. Deliberate first-link abort after actual partial file write; redial and source-built ASPECT login, exact ZIP retry and NFO. Isolated ENiGMA; not physical Wi-Fi firmware acceptance.')
    (out/'carrier-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,errors=errors,notices=notices),indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    raise SystemExit(asyncio.run(run(p.parse_args())))
