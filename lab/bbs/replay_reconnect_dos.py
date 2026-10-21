#!/usr/bin/env python3
"""Causal captured-byte DOS replay to isolate the second-script audio failure.

This is a diagnostic peer, not a live BBS/audio compatibility test. It sends
unaltered captured online bytes and requires the recorded DOS input in order.
Idle/audio transmission time is shortened; ASPECT's own waits remain real.
"""
import argparse,asyncio,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
from audio_synchronet import ROOT,sha
sys.path.insert(0,str(ROOT/'standalone'))
from carrier_notice_watch import SAMPLER

def groups(folder,flex_cpr=False):
    upstream=(folder/'serial-in.bin').read_bytes();downstream=(folder/'serial-out.bin').read_bytes()
    assert upstream.startswith(b'ATZ\rATD1\r') and downstream.startswith(b'\r\nOK\r\n\r\nCONNECT 1200\r\n')
    node=json.loads((folder/'node-result.json').read_text());anchor=next(e for e in node['events'] if 'monotonicNs' in e)
    events=[]
    for direction,name,raw,skip in [('up','serial-input-events.jsonl',upstream,9),('down','serial-write-events.jsonl',downstream,22)]:
        cursor=0
        for line in (folder/name).read_text().splitlines():
            row=json.loads(line);assert row['offset']==cursor;cursor+=row['length'];at=max(skip,row['offset'])
            if cursor<=at:continue
            clock=(int(row['monotonicNs'])-int(anchor['monotonicNs']))/1e9+anchor['seconds'] if direction=='up' else row['submittedAt']
            events.append((clock,direction,raw[at:cursor]))
        assert cursor==len(raw)
    events.sort(key=lambda x:x[0]);pending=bytearray();result=[]
    for _,direction,body in events:
        if direction=='down':pending.extend(body)
        else:result.append((bytes(pending),body));pending.clear()
    result.append((bytes(pending),b''))
    assert b''.join(x for x,y in result)==downstream[22:]
    assert b''.join(y for x,y in result)==upstream[9:]
    if not flex_cpr:return [(x,y,False) for x,y in result]
    flat=[];trailing=b''
    for emitted,wanted in result:
        if not wanted:trailing+=emitted;continue
        flat.extend((emitted if i==0 else b'',bytes([v])) for i,v in enumerate(wanted))
    spans={m.start():m.end() for m in re.finditer(rb'\x1b\[\d+;\d+R',upstream[9:])}
    merged=[];i=0
    while i<len(flat):
        end=spans.get(i,i+1)
        merged.append((b''.join(x for x,y in flat[i:end]),b''.join(y for x,y in flat[i:end]),i in spans));i=end
    merged.append((trailing,b'',False))
    assert b''.join(x for x,y,z in merged)==downstream[22:]
    assert b''.join(y for x,y,z in merged)==upstream[9:]
    return merged

async def run(a):
    source=a.cohort.resolve();out=a.output.resolve()
    assert source.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    receipt=json.loads((ROOT/'docs/validation/current-synchronet-reconnect-audio-01.json').read_text())
    assert not receipt['passed'] and ROOT/receipt['cohort']==source
    for n,h in receipt['capture_sha256'].items():assert sha(source/n)==h,n
    flow=groups(source/'call-1',a.flex_cpr);out.mkdir(parents=True);stage=out/'program';stage.mkdir();(out/'RECV').mkdir()
    frozen={n:sha(ROOT/n) for n in ('lab/bbs/replay_reconnect_dos.py','lab/bbs/audio_synchronet_reconnect_keys.asm','lab/bbs/carrier_notice_watch.py','lab/bbs/zmodem_label_watch.py','standalone/test_terminal.py','lab/bbs/audio_get_vector.asm')}
    keys=ROOT/'lab/bbs/audio_synchronet_reconnect_keys.asm'
    if a.keys:
        keys=a.keys.resolve();assert keys.is_relative_to(ROOT/'build') and keys.name=='audio_synchronet_reconnect_keys.asm'
        frozen[str(keys.relative_to(ROOT))]=sha(keys)
    for name in ('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','AUDIO.ASP','AUDIO.ASX'):shutil.copyfile(source/'program'/name,stage/name)
    if a.terminal:
        terminal=a.terminal.resolve();assert terminal.is_relative_to(ROOT/'build') and terminal.name=='TERMINAL.EXE'
        shutil.copyfile(terminal,stage/'TERMINAL.EXE')
    if a.runner:
        runner=a.runner.resolve();assert runner.is_relative_to(ROOT/'build') and runner.name=='ASPECT.EXE'
        shutil.copyfile(runner,stage/'ASPECT.EXE')
    (out/'sampler.asm').write_text(SAMPLER)
    for src,dst,flags in [(out/'sampler.asm',out/'SNAP.COM',[]),(keys,stage/'EXITKEY.COM',['-DAUDIO_SYNC_DOWNLOAD_WATCHDOG=3600']),(ROOT/'lab/bbs/audio_get_vector.asm',stage/'KEYVEC.COM',[])]:
        subprocess.run(['nasm','-fbin',*flags,str(src),'-o',str(dst)],check=True)
    sessions=[];owners=set()
    async def accept(reader,writer):
        owner=asyncio.current_task();owners.add(owner);row=dict(up=bytearray(),down=bytearray(),error=None,done=False,query_variations=[])
        sessions.append(row)
        try:
            for emitted,expected,is_cpr in flow:
                for at in range(0,len(emitted),32):
                    chunk=emitted[at:at+32];writer.write(chunk);await writer.drain();row['down'].extend(chunk)
                    await asyncio.sleep(len(chunk)/1200)
                if expected:
                    actual=await asyncio.wait_for(reader.readuntil(b'R') if is_cpr else reader.readexactly(len(expected)),25)
                    row['up'].extend(actual)
                    if is_cpr:
                        match=re.fullmatch(rb'\x1b\[(\d{1,2});(\d{1,2})R',actual)
                        assert match and 1<=int(match[1])<=25 and 1<=int(match[2])<=80,('Invalid native CPR',actual)
                        if actual!=expected:row['query_variations'].append(dict(expected=expected.hex(),actual=actual.hex()))
                    else:assert actual==expected,('Replay input mismatch',len(row['up']),actual.hex(),expected.hex())
        except Exception as error:
            if isinstance(error,asyncio.IncompleteReadError):row['up'].extend(error.partial)
            row['error']=repr(error)
        finally:
            writer.close();await writer.wait_closed();row['done']=True;owners.discard(owner)
    server=await asyncio.start_server(accept,'127.0.0.1',0)
    try:
        port=server.sockets[0].getsockname()[1]
        profile=(source/'MODEM.PRM').read_bytes();(out/'MODEM.PRM').write_bytes(profile)
        book=bytearray((source/'CALL.DIR').read_bytes());book[275:296]=f'127.0.0.1:{port}'.encode().ljust(21,b'\0');(out/'CALL.DIR').write_bytes(book)
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
        with (out/'dosbox.log').open('wb') as log:
            child=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf'),stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
            try:code=await asyncio.wait_for(child.wait(),230)
            except asyncio.TimeoutError:
                child.terminate()
                try:await asyncio.wait_for(child.wait(),5)
                except asyncio.TimeoutError:child.kill();await child.wait()
                code=-1
    finally:
        server.close()
        for owner in list(owners):owner.cancel()
        await asyncio.gather(*list(owners),return_exceptions=True);await server.wait_closed()
    results=[]
    for i,row in enumerate(sessions,1):
        for n in ('up','down'):(out/f'call-{i}-{n}.bin').write_bytes(row[n])
        results.append(dict(input_bytes=len(row['up']),output_bytes=len(row['down']),error=row['error'],done=row['done'],query_variations=row['query_variations']))
    read=lambda n:(out/n).read_bytes() if (out/n).exists() else b''
    b=read('SCREEN.BIN');screen='\n'.join(b[i*160:i*160+160:2].decode('cp437') for i in range(25)) if len(b)==4000 else ''
    result=dict(normal_DOS_exit=code==0 and bool(read('PASS.TXT')) and not read('FAIL.TXT'),
        hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),
        timer_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'),
        reproduced_D4_error='error 3, opcode D4, step 2' in screen,
        screen=screen,stages=read('STAGES.LOG').decode(),sessions=results,
        script_sha256=sha(stage/'AUDIO.ASX'),terminal_sha256=sha(stage/'TERMINAL.EXE'),runner_sha256=sha(stage/'ASPECT.EXE'),
        inputs=frozen,inputs_unchanged=all(sha(ROOT/n)==h for n,h in frozen.items()),
        flexible_native_CPR=a.flex_cpr,
        receipt_sha256=sha(ROOT/'docs/validation/current-synchronet-reconnect-audio-01.json'),
        scope='Diagnostic causal replay of retained online audio frontend bytes and expected DOS input; real DOS terminal/compiler output/ASPECT child, built-in modem/DCD and BIOS helper. Shortened host transmission/idle times, unchanged script waits. Optional flexible CPR records bounded native coordinate differences, merging corresponding host emissions; all other input stays exact. Optional diagnostic terminal identity is explicit. No live BBS, SIP/audio or compatibility acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cohort',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--terminal',type=Path);p.add_argument('--runner',type=Path);p.add_argument('--keys',type=Path);p.add_argument('--flex-cpr',action='store_true')
    asyncio.run(run(p.parse_args()))
