#!/usr/bin/env python3
"""One DOS process, real SIP/audio bridge failure, fresh call and download retry."""
import argparse,asyncio,datetime,json,os,shutil,struct,subprocess,sys,time
from pathlib import Path
from audio_synchronet import ROOT,RUNTIME,PORT,snapshot,message_bodies,statistics,sha
from synthmodem_posttrain_validation import validate
from synthmodem_synchronet_download_audio_dos import script
from audio_synchronet_download import source as download_source
from audio_carrier_adapter import audio_carrier_adapter,PREFIX
from audio_reconnect_bbs_relay import relay
from audio_reconnect_boundary import acknowledged_prefix
from carrier_notice_watch import SAMPLER
sys.path.insert(0,str(ROOT/'standalone'));sys.path.insert(0,str(ROOT/'src/aspect'))
from directory_fixtures import prm,directory
from directory_test_support import accounting_check
from compiler import compile_source

async def run(a):
    out=a.output.resolve();runtime=a.runtime.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    diagnostic=a.diagnostic_terminal is not None
    assert diagnostic or a.diagnostic_watchdog is None
    assert a.diagnostic_watchdog is None or 3600<=a.diagnostic_watchdog<=21600
    runtime_inputs=validate(runtime);server=snapshot();bodies=message_bodies();stats=statistics()
    keys=json.loads(a.key_checks.read_text());assert keys['passed']
    assert all(sha(ROOT/n)==h for n,h in keys['inputs'].items())
    names=['lab/bbs/synthmodem_synchronet_reconnect_dos.py','lab/bbs/audio_carrier_adapter.py',
        'lab/bbs/audio_reconnect_bbs_relay.py','lab/bbs/audio_synchronet_reconnect_keys.asm',
        'lab/bbs/audio_reconnect_boundary.py','lab/bbs/modem.py',
        'lab/bbs/synthmodem_audio_serial.js','lab/bbs/serial_io_evidence.js','lab/bbs/internal_sip_capture.js',
        'lab/bbs/synthmodem_synchronet_download_audio_dos.py','lab/bbs/audio_synchronet.py',
        'lab/bbs/audio_synchronet_download.py','lab/bbs/synchronet.py','lab/bbs/carrier_notice_watch.py',
        'lab/bbs/zmodem_label_watch.py','standalone/test_terminal.py','lab/bbs/audio_get_vector.asm',
        'standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/directory_test_support.py',
        'src/aspect/compiler.py','nix/flake.nix','nix/flake.lock','tools/modem-dev']
    frozen={n:sha(ROOT/n) for n in names};source=download_source();expected=source.read_bytes();source_sha=sha(source)
    out.mkdir(parents=True);stage=out/'program';stage.mkdir();recv=out/'RECV';recv.mkdir()
    for rel in ('terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE'):
        p=ROOT/'build'/rel;frozen['build/'+rel]=sha(p);shutil.copyfile(p,stage/p.name)
    if diagnostic:
        terminal=a.diagnostic_terminal.resolve()
        assert terminal.is_relative_to(ROOT/'build') and terminal.name=='TERMINAL.EXE'
        frozen[str(terminal.relative_to(ROOT))]=sha(terminal)
        shutil.copyfile(terminal,stage/'TERMINAL.EXE')
    (out/'sampler.asm').write_text(SAMPLER)
    for p,dst in [(out/'sampler.asm',out/'SNAP.COM'),(ROOT/'lab/bbs/audio_synchronet_reconnect_keys.asm',stage/'EXITKEY.COM'),(ROOT/'lab/bbs/audio_get_vector.asm',stage/'KEYVEC.COM')]:
        flags=['-DAUDIO_SYNC_DOWNLOAD_WATCHDOG='+str(a.diagnostic_watchdog)] if p.name=='audio_synchronet_reconnect_keys.asm' and a.diagnostic_watchdog else []
        subprocess.run(['nasm','-fbin',*flags,str(p),'-o',str(dst)],check=True)
    date=datetime.datetime.strptime(stats['Global']['date'],'%b %d %Y')
    log=RUNTIME/'data/logs'/date.strftime('%m%d%y.log');boundary=(log.stat().st_ino,log.stat().st_size)
    partials=[];finished=asyncio.Event();code=None
    async with relay(PORT,out) as (bbs_port,bbs),audio_carrier_adapter(ROOT,runtime,out) as (port,calls):
        asp=script(bbs_port);(stage/'AUDIO.ASP').write_text(asp)
        profile=bytearray(prm(port=1,baud=6,soft=0,hard=1))
        struct.pack_into('<H',profile,10,120)
        profile[0x18:0x47]=b'AT&K3^M'.ljust(47,b'\0');profile[0x79:0x92]=bytes(25)
        profile=bytes(profile);(out/'MODEM.PRM').write_bytes(profile)
        contact=bytearray(directory(entry=1,target=f'127.0.0.1:{port}'.encode(),port=1,baud=6))
        contact[250+52:250+61]=b'AUDIO\0\0\0\0';contact=bytes(contact);(out/'CALL.DIR').write_bytes(contact)
        async def watch():
            while not finished.is_set():
                p=recv/'PCRX.$$$'
                if len(calls)==1 and not calls[0].interrupted and p.is_file() and p.stat().st_size>=1024:
                    value=p.read_bytes();assert expected.startswith(value) and len(value)<len(expected)
                    delivered=acknowledged_prefix(calls[0].up,bbs[0]['input']) if len(bbs)==1 else None
                    if delivered:
                        ns=str(time.monotonic_ns())
                        calls[0].event('acknowledged-prefix-before-stop',**delivered)
                        partials.append(dict(kind='before-bridge-stop',bytes=len(value),sha256=sha(p),files=sorted(x.name for x in recv.iterdir()),monotonic_ns=ns,acknowledged_prefix=delivered))
                        (out/'interrupted-partial.bin').write_bytes(value)
                        calls[0].interrupt()
                if len(calls)==2 and len(partials)==1:
                    partials.append(dict(kind='before-second-audio-training',files=sorted(x.name for x in recv.iterdir()),monotonic_ns=str(time.monotonic_ns())))
                await asyncio.sleep(.05)
        watcher=asyncio.create_task(watch())
        config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=modem listenport:0
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{stage}"
mount d "{out}"
c:
ASPCOMP AUDIO.ASP AUDIO.ASX >D:\\COMPILE.TXT
if errorlevel 1 goto failed
D:\\SNAP B
EXITKEY
TERMINAL @D:\\MODEM.PRM /E:D:\\CALL.DIR /N:1
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
KEYVEC
D:\\SNAP S
D:\\SNAP A
exit
'''
        (out/'dosbox.conf').write_text(config)
        try:
            with (out/'dosbox.log').open('wb') as capture:
                child=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf'),
                    stdout=capture,stderr=capture,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
                try:code=await asyncio.wait_for(child.wait(),1500)
                except asyncio.TimeoutError:
                    child.terminate()
                    try:await asyncio.wait_for(child.wait(),5)
                    except asyncio.TimeoutError:child.kill();await child.wait()
                    code=-1
        finally:
            finished.set();await watcher
            deadline=time.monotonic()+20
            while any(not c.done for c in calls) and time.monotonic()<deadline:await asyncio.sleep(.1)
    read=lambda n:(out/n).read_bytes() if (out/n).exists() else b''
    assert log.stat().st_ino==boundary[0]
    with log.open('rb') as f:f.seek(boundary[1]);session_log=f.read()
    (out/'server-session.log').write_bytes(session_log)
    raw=read('LABELS.BIN');notices=[]
    if len(raw)==2566:
        magic,count,ticks=struct.unpack_from('<3H',raw)
        if magic==0x4e5a and 0<count<=16:notices=[raw[6+i*160:6+(i+1)*160:2].decode('cp437') for i in range(count)]
    after=statistics();checks=dict(normal_DOS_exit=code==0 and read('PASS.TXT') and not read('FAIL.TXT'),
        hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),
        timer_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'),
        DOS_compiler_exact=(stage/'AUDIO.ASX').read_bytes()==compile_source(asp),
        two_calls=len(calls)==2 and all(c.done and not c.errors and c.process.returncode==0 for c in calls),
        first_bridge_interrupted=len(calls)==2 and calls[0].interrupted and not calls[1].interrupted,
        partial_removed_before_second_call=len(partials)==2 and partials[1]['files']==[],
        carrier_loss_observed=any('RX carrier lost' in s for s in notices),
        complete_retry_observed=any('RX complete' in s for s in notices),
        exact_retry=read('RECV/SYNC.BIN')==expected+b'\x1a'*127,
        only_expected_receive={p.name for p in recv.iterdir()}=={'SYNC.BIN'},
        two_BBS_connections=len(bbs)==2 and all(b['done'] and not b['errors'] for b in bbs),
        profile_unchanged=read('MODEM.PRM')==profile,directory_two_calls=accounting_check(contact,read('CALL.DIR'),1,2),
        source_unchanged=sha(source)==source_sha,server_inputs_preserved=snapshot()==server,
        message_bodies_preserved=message_bodies()==bodies,
        no_message_mail_upload_writes=all(stats['Total'][k]==after['Total'][k] for k in ('uploads','uploadb','posts','email','feedback')),
        inputs_preserved=all(sha(ROOT/n)==h for n,h in frozen.items()) and all(sha(Path(n))==h for n,h in runtime_inputs.items()))
    checks={k:bool(v) for k,v in checks.items()}
    result=dict(passed=all(checks.values()) and not diagnostic,diagnostic=diagnostic,
        diagnostic_watchdog=a.diagnostic_watchdog,checks=checks,notices=notices,partials=partials,
        frozen_inputs=frozen,runtime_inputs=runtime_inputs,server=server,statistics_before=stats,statistics_after=after,
        source_sha256=source_sha,source_bytes=len(expected),stages=read('STAGES.LOG').decode(),
        scope='One source-built DOS process; DOSBox built-in Hayes/DCD and test-only TCP-to-real-SIP/audio adapter. Stop first owned bridge with SIGTERM only after verified partial file write; actual frontend shutdown EOF drops emulated DCD. Each call has a fresh frontend/VM and real DSP training. Numeric lab network dialing is not a Boca profile. This producer alone is not independent protocol/byte/audio acceptance, waveform-loss detection, physical DCD/DTR or F01-F16 completion.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],checks=checks)))
    assert result['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--key-checks',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--diagnostic-terminal',type=Path,help='Instrumented terminal under ignored build storage; result cannot count as compatibility acceptance')
    p.add_argument('--diagnostic-watchdog',type=int,help='Diagnostic-only BIOS watchdog ticks (3600..21600)')
    asyncio.run(run(p.parse_args()))
