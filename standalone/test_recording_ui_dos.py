#!/usr/bin/env python3
"""Real DOS menu recording -> DOS compiler -> UART replay on owned media."""
import argparse,hashlib,json,os,re,shutil,socket,subprocess,threading,time
from pathlib import Path
from test_terminal import ROOT,SAMPLER


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--mode',choices=('new','replace','cancel'),default='new')
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    original=b'ORIGINAL\x1aKEEP\r\n'
    if args.mode!='new':(out/'PCPLUS.ASP').write_bytes(original)
    frozen={}
    for directory,binary in (('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')):
        base=ROOT/'build'/directory;manifest=json.loads((base/'manifest.json').read_text())
        assert sha(base/binary)==manifest['binary_sha256']
        if directory=='terminal':assert manifest['binary_sha256']==args.sha256
        else:assert not manifest['original_inputs']
        for source,digest in manifest['sources'].items():
            assert sha(ROOT/source)==digest,source
            assert source not in frozen or frozen[source]==digest
            frozen[source]=digest
        for source in (base/binary,base/'manifest.json'):
            frozen[str(source.relative_to(ROOT))]=sha(source)
        shutil.copy2(base/binary,out/binary)
    for source in (Path(__file__).resolve(),ROOT/'standalone/test_terminal.py'):
        frozen[str(source.relative_to(ROOT))]=sha(source)
    for source,digest in frozen.items():
        copy=out/'frozen-source'/source;copy.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/source,copy);assert sha(copy)==digest
    (out/'start.json').write_text(json.dumps(dict(inputs=frozen),indent=2)+'\n')
    (out/'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    # The standalone ASPECT lease deliberately requires a connected/asserted
    # DTR baseline. Keep that baseline across terminal exit and replay.
    (out/'setup.asm').write_text('BITS 16\nCPU 8086\nORG 100h\nmov dx,3fbh\nmov al,80h\nout dx,al\nmov dx,3f8h\nmov al,12\nout dx,al\ninc dx\nxor al,al\nout dx,al\nmov dx,3fbh\nmov al,3\nout dx,al\nmov dx,3fch\nmov al,1\nout dx,al\nmov ax,4c00h\nint 21h\n')
    subprocess.run(['nasm','-fbin',str(out/'setup.asm'),'-o',str(out/'SETUP.COM')],check=True)
    server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(15)
    wire=bytearray();sent=bytearray();events=[];errors=[];stop=threading.Event()
    prompt=b'Name? \x1b[6n';dsr=re.compile(rb'\x1b\[[0-9]+;[0-9]+R')
    def peer():
        try:
            conn,_=server.accept()
            with conn:
                conn.settimeout(.1);last_probe=0;prompt_count=0;ready=False
                while not stop.is_set():
                    now=time.monotonic()
                    if not ready and now-last_probe>.2:
                        conn.sendall(b'\x1b[6n');sent.extend(b'\x1b[6n');last_probe=now
                    try:data=conn.recv(4096)
                    except socket.timeout:continue
                    if not data:break
                    wire.extend(data);ready=bool(dsr.search(wire))
                    markers=list(re.finditer(b'm1',wire))
                    if len(markers)>prompt_count:
                        conn.sendall(prompt);sent.extend(prompt);prompt_count+=1
                        events.append(dict(marker=prompt_count,wire_offset=markers[-1].start(),
                            original_intact=(out/'PCPLUS.ASP').read_bytes()==original if args.mode!='new' and prompt_count==1 else None))
        except OSError as error:
            if not stop.is_set():errors.append(repr(error))
        finally:server.close()
    thread=threading.Thread(target=peer,daemon=True);thread.start()
    accept='p300 y ' if args.mode!='new' else ''
    finish='d p300 y' if args.mode=='cancel' else 'c'
    keys=f'p1800 a-z p300 c p300 enter {accept}p700 m 1 p1000 b s t a r enter p1000 a-z p300 {finish} p500 escape escape p400 a-x'
    replay_commands='' if args.mode=='cancel' else r'''C:\ASPCOMP D:\PCPLUS.ASP D:\RECORD.ASX
if errorlevel 1 goto failed
C:\ASPECT D:\RECORD.ASX /S1:0003:03:N
if errorlevel 1 goto failed'''
    config=fr'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
d:
SETUP
SNAP B
ADDKEY {keys}
C:\TERMINAL COM1 38400 8N1 HARD
if errorlevel 1 goto failed
{replay_commands}
echo PASS>PASS.TXT
goto finish
:failed
echo FAIL>FAIL.TXT
:finish
SNAP S
SNAP A
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=100)
    stop.set();thread.join(2)
    assert not thread.is_alive()
    (out/'wire.bin').write_bytes(wire);(out/'peer.bin').write_bytes(sent)
    (out/'events.json').write_text(json.dumps(events,indent=2)+'\n')
    source=(out/'PCPLUS.ASP').read_bytes() if (out/'PCPLUS.ASP').exists() else b''
    payload=b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
    markers=list(re.finditer(b'm1',wire))
    manual=dsr.sub(b'',bytes(wire[markers[0].start():markers[1].start() if len(markers)==2 else len(wire)])) if markers else b''
    replay=bytes(wire[markers[1].start():]) if len(markers)==2 else b''
    checks=dict(normal_DOS_exit=process.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
        expected_real_sessions=len(markers)==len(events)==(1 if args.mode=='cancel' else 2),no_peer_errors=not errors,
        actual_user_session=manual in (b'm1bstar\r',b'm1bstar\r\n'),
        query_responses_seen=bool(dsr.search(wire)),
        temporary_files_resolved=not list(out.glob('LPR*.TMP')) and not list(out.glob('LPR*.BAK')),
        hardware_restored=(out/'BEFORE.BIN').is_file() and (out/'AFTER.BIN').is_file() and
            (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes() and (out/'BEFORE.BIN').stat().st_size==42)
    if args.mode=='cancel':
        checks.update(original_preserved_on_cancel=source==original,no_bytecode_on_cancel=not (out/'RECORD.ASX').exists())
    else:
        checks.update(menu_published_complete_source=source.endswith(b'endproc\r\n') and (out/'RECORD.ASX').is_file(),
            query_responses_excluded=payload==manual,exact_compiled_UART_replay=replay==payload and bool(payload),
            recorded_prompt_timeout=b'waitfor loc_prompt 30' in source)
    if args.mode!='new':checks['original_intact_during_recording']=bool(events and events[0]['original_intact'])
    for name,digest in frozen.items():assert sha(ROOT/name)==sha(out/'frozen-source'/name)==digest,name
    result=dict(passed=all(checks.values()),checks=checks,mode=args.mode,binary_sha256=args.sha256,manual_hex=manual.hex(),
        replay_hex=replay.hex(),recorded_payload_hex=payload.hex(),errors=errors,inputs=frozen,
        captures_sha256={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and not p.is_relative_to(out/'frozen-source')},
        scope=__doc__+' Independent loopback peer; actual BIOS menu keys, source-built DOS programs and real kernel files. No physical modem/BBS acceptance.')
    with (out/'result.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks)),flush=True)
    assert result['passed']


if __name__=='__main__':main()
