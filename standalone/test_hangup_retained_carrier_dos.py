#!/usr/bin/env python3
"""Actual DOS negative evidence: blocked hangup with an explicitly online peer."""
import argparse, inspect, json, shutil, struct, subprocess, types
from pathlib import Path
import test_manual_cancel_dos as base
from directory_fixtures import directory, prm
ROOT=base.ROOT


def adapter(out, events, backend):
    text=inspect.getsource(base.connection.run).replace("out=ROOT/'build/connection-dos'/name", 'out=CASE_OUT/name')
    start=text.index(' def peer():');end=text.index(' thread=threading.Thread',start)
    peer=r''' def event(kind,data=b''):
  events.append(dict(kind=kind,time=time.monotonic(),hex=data.hex()))
 def peer():
  nonlocal attempts
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.03);escape=False;online=False;line=bytearray();online_data=bytearray();paused=False
    conn.sendall(b'\xff\x81');event('DCD-low',b'\xff\x81')
    while not stop.is_set():
     try:block=conn.recv(1)
     except socket.timeout:continue
     if not block:break
     event('transport-receive',block);value=block[0]
     if escape:
      escape=False
      if value!=255:event('guest-control',bytes([value]));continue
     elif value==255:escape=True;continue
     wire.append(value)
     if online:
      online_data.append(value);event('online-data',bytes([value]))
      if not paused and online_data.endswith(b'arm'):
       conn.sendall(b'\x13');event('XOFF-online',b'\x13');paused=True
      # Deliberately retain online data mode and DCD across any DTR pulse.
      # AT-looking bytes here are data, never parsed as new modem commands.
      continue
     if value!=13:line.append(value);continue
     command=bytes(line);line.clear()
     if not command:continue
     commands.append(command.decode('ascii','replace'))
     if command==b'ATZ':conn.sendall(b'\r\nOK\r\n')
     elif command==b'ATD'+target:
      attempts+=1;online=True;conn.sendall(b'\xff\x8bCONNECT\r\n'+banner);event('online-CONNECT',b'\xff\x8b')
     else:checks['unexpected_modem_command']=True
  except (OSError,AssertionError) as error:
   if not stop.is_set():errors.append(str(error))
'''
    text=text[:start]+peer+text[end:]
    for tag in ('B','A'):
        needle='D:'+chr(92)*2+'SNAP '+tag
        assert text.count(needle)==1
        text=text.replace(needle,needle+'\nD:'+chr(92)*2+'VECT '+tag)
    text=text.replace('transparent:1','transparent:0').replace('cputype=386','cputype=8086')
    module=types.ModuleType('retained_carrier_peer');module.__dict__.update(base.connection.__dict__)
    module.__dict__.update(CASE_OUT=out,events=events,subprocess=base.Backend(backend))
    exec(compile(text,__file__,'exec'),module.__dict__)
    return module


def observer(out, map_path):
    text=(ROOT/'standalone/manual_cancel_watch.asm').read_text()
    start=text.index('sample:\n');end=text.index('sample_end:',start)
    text=text[:start]+'''sample:
magic: dw 0x4847
parent_ds: dw 0
ticks: dw 0
online_paused: dw 0
hangup_ticks: dw 0
hangup_DTR_low: dw 0
idle_ticks: dw 0
idle_paused: dw 0xffff
idle_carrier: dw 0
idle_status: dw 0xffff
retry_high: dw 0
done: dw 0
'''+text[end:]
    start=text.index('timer:\n');end=text.index('prm_name:',start)
    text=text[:start]+'''timer:
 save
 cld
 cmp word [cs:done],0
 jne .end
 mov ax,[cs:parent_ds]
 or ax,ax
 jz .end
 mov dx,ss
 cmp ax,dx
 jne .end
 mov es,ax
 inc word [cs:ticks]
 cmp word [es:STATE],6
 jne .hangup
 cmp word [es:PAUSED],1
 jne .online_status
 inc word [cs:online_paused]
.online_status:
 cmp word [es:STATUS],8
 jne .end
 inc word [cs:idle_ticks]
 mov ax,[es:PAUSED]
 mov [cs:idle_paused],ax
 mov word [cs:idle_status],8
 mov dx,0x3fe
 in al,dx
 test al,0x80
 jz .end
 inc word [cs:idle_carrier]
 jmp .end
.hangup:
 cmp word [es:STATE],9
 jne .dtr
 inc word [cs:hangup_ticks]
 jmp .end
.dtr:
 cmp word [es:STATE],8
 jne .idle
 mov dx,0x3fc
 in al,dx
 test al,1
 jnz .end
 inc word [cs:hangup_DTR_low]
 jmp .end
.idle:
 cmp word [cs:hangup_ticks],0
 je .end
 mov dx,0x3fe
 in al,dx
 test al,0x80
 jz .end
 cmp word [es:STATE],0
 jne .retry
 inc word [cs:idle_ticks]
 mov ax,[es:PAUSED]
 mov [cs:idle_paused],ax
 inc word [cs:idle_carrier]
 mov ax,[es:STATUS]
 mov [cs:idle_status],ax
 jmp .end
.retry:
 cmp word [es:STATE],1
 jb .end
 cmp word [es:STATE],5
 ja .end
 inc word [cs:retry_high]
.end:
 restore
 jmp far [cs:old1c]
'''+text[end:]
    text=text.replace('0x434d','0x4847').replace('D:\\CANCEL.BIN','D:\\RETAIN.BIN')
    source=out/'retained-watch.asm';source.write_text(text)
    names=base.symbols(map_path)
    definitions={key:str(names[name][1]) for key,name in [('STATE','connection_state'),('STATUS','connection_status'),('PAUSED','uart_tx_paused')]}
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in definitions.items()],str(source),'-o',str(out/'WATCH.COM')],check=True)
    (out/'offsets.json').write_text(json.dumps(definitions,indent=2)+'\n')
    return (out/'WATCH.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--expect-fixed',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    binary=ROOT/'build/terminal/TERMINAL.EXE';manifest=json.loads((binary.parent/'manifest.json').read_text());assert base.sha(binary)==manifest['binary_sha256']
    inputs=dict(manifest['sources'])
    for path in (Path(__file__),Path(base.__file__),ROOT/'standalone/manual_cancel_watch.asm',ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/directory_fixtures.py',ROOT/'standalone/modem_fixtures.py',ROOT/'nix/patches/dosbox-dcd-control.patch',ROOT/'nix/flake.lock'):
        inputs[str(path.relative_to(ROOT))]=base.sha(path)
    for name,digest in inputs.items():
        assert base.sha(ROOT/name)==digest;dest=out/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(binary,out/'admitted.EXE');shutil.copy2(binary.parent/'terminal.map',out/'admitted.map')
    compiled=observer(out,binary.parent/'terminal.map');vectors=base.vectors(out)
    backend=(ROOT/'build/dosbox-dcd-lab/bin/dosbox-x').resolve();rows=[]
    for drop in (0,1):
      for hard in (0,1):
        name=f'drop{drop}-'+('both' if hard else 'soft');folder=out/name;folder.mkdir();events=[];peer=adapter(out,events,backend)
        shutil.copy2(binary,folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        payload=bytearray(prm(soft=1,hard=hard));struct.pack_into('<H',payload,10,3);struct.pack_into('<H',payload,16,drop)
        try:
            r=peer.run(name,'success','p1800 a r m p600 a-h p5000 a-d p2200 a-x',directory=directory(profile=4),prm=bytes(payload),profile=4,working_drive='d',observer='WATCH',files={'WATCH.COM':compiled,'VECT.COM':vectors},accounting_delta=1,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        sample=struct.unpack('<12H',(folder/'RETAIN.BIN').read_bytes());wire=(folder/'serial.bin').read_bytes()
        online=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='online-data')
        checks=dict(r['checks'],observer_valid=sample[0]==0x4847 and sample[1]!=0 and sample[2]>18 and sample[11]==1,
            online_XOFF_observed=sample[3]>4,blocked_hangup_observed=sample[4]>30,DTR_policy_observed=(sample[5]>8 if drop else sample[5]==0),
            returned_idle_with_carrier=sample[6]>4 and sample[8]>4 and sample[9]==3,flow_retired=sample[7]==0,
            retry_while_carrier_high=sample[10]>4,modem_commands_only_before_connection=r['commands']==['ATZ','ATDCaseTest:23'],
            retry_commands_are_online_data=b'armATZ\rATDCaseTest:23\r' in online,hangup_not_transmitted=b'+++ATH\r' not in wire,
            observer_vectors_restored=(folder/'VECOLD.BIN').read_bytes()==(folder/'VECNEW.BIN').read_bytes() and len((folder/'VECOLD.BIN').read_bytes())==8)
        if a.expect_fixed:
            for key in ('returned_idle_with_carrier','flow_retired','retry_while_carrier_high','retry_commands_are_online_data'):del checks[key]
            checks.update(failed_hangup_retains_online=sample[6]>4 and sample[8]>4 and sample[9]==8,
                failed_hangup_retains_pause=sample[7]==1,no_retry_state=sample[10]==0,
                no_online_modem_commands=online==b'\x1b[1;16R\x1b[?62;2carm',
                whole_wire_exact=wire==b'ATZ\rATDCaseTest:23\r'+online)
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,sample=list(sample),online_data_hex=online.hex(),wire_hex=wire.hex(),captures={str(f.relative_to(folder)):base.sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],sample=list(sample),failed=[k for k,v in checks.items() if not v])),flush=True)
    wrapped=backend.with_name('.dosbox-x-wrapped')
    result=dict(passed=all(r['passed'] for r in rows),gap_reproduced=not a.expect_fixed and all(r['passed'] for r in rows),retained_carrier_policy_accepted=a.expect_fixed and all(r['passed'] for r in rows),compatibility_accepted=False,parent_sha256=base.sha(binary),cases=rows,inputs=inputs,
        emulator=dict(test_backend=True,wrapper_sha256=base.sha(backend),binary_sha256=base.sha(wrapped),patch_sha256=base.sha(ROOT/'nix/patches/dosbox-dcd-control.patch')),
        scope='Actual8086 DOS parent/controller/IRQ, real BIOS Alt-H/Alt-D, read-only timer observer, explicit patched lab DCD and owned online peer. Peer stays online and retains carrier across DTR. Expected-gap mode reproduces retry AT bytes as remote data; expected-fixed mode requires retained pause/status8 and no retry/abort bytes. Only this failed-hangup policy is covered; not full compatibility. No physical modem or carrier-ignore policy acceptance.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
