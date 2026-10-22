#!/usr/bin/env python3
"""Actual DOS pre-CONNECT cancellation with an explicitly patched DCD lab UART."""
import argparse,inspect,json,re,shutil,struct,subprocess,types
from pathlib import Path
import test_connection_dos as connection
from test_aspect_script_window_dos import symbols
from directory_fixtures import directory,prm
from audit_aspect_transmit_wait import ROOT,sha,read,ESC


class Backend:
    def __init__(self,path):self.path=str(path)
    def __getattr__(self,name):return getattr(subprocess,name)
    def run(self,argv,*args,**kwargs):
        if argv[0]=='dosbox-x':argv=[self.path,*argv[1:]]
        return subprocess.run(argv,*args,**kwargs)


def adapter(out,events,gap,backend):
    text=inspect.getsource(connection.run).replace("out=ROOT/'build/connection-dos'/name",'out=CASE_OUT/name')
    start=text.index(' def peer():');end=text.index(' thread=threading.Thread',start)
    peer=r''' def event(kind,data=b''):
  events.append(dict(kind=kind,time=time.monotonic(),hex=data.hex()))
 def peer():
  nonlocal attempts
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.03);escape=False;phase='initial';paused=False;line=bytearray();last_status=None;online=False;queried=False
    conn.sendall(b'\xff\x81');event('DCD-low',b'\xff\x81')
    while not stop.is_set():
     try:block=conn.recv(1)
     except socket.timeout:continue
     if not block:break
     event('transport-receive',block);value=block[0]
     if escape:
      escape=False
      if value!=255:
       event('modem-status',bytes([value]))
       if paused and phase=='initial' and last_status is not None and last_status&2 and not value&2:
        phase='DTR-low';line.clear();event('cancel-DTR-low')
       elif phase=='DTR-low' and value&2:
        phase='retry';event('cancel-DTR-restored')
       last_status=value;continue
     elif value==255:escape=True;continue
     block=bytes([value]);wire.extend(block);event('receive',block)
     if not paused:
      assert value==ord('A');conn.sendall(b'\x13');event('XOFF-first-init',b'\x13');paused=True;continue
     if phase in ('initial','DTR-low'):raise AssertionError('Unexpected data during initial XOFF')
     line.append(value)
     if online:
      if not queried and b'ready' in line:conn.sendall(b'\x1b[6n');event('query',b'\x1b[6n');queried=True
      if line.endswith(b'+++ATH\r'):
       checks['configured_hangup_reached_wire']=True;conn.sendall(b'\xff\x81\r\nOK\r\n');event('DCD-low-hangup',b'\xff\x81');line.clear();online=False
      continue
     if value!=13:continue
     command=bytes(line[:-1]);line.clear();commands.append(command.decode('ascii','replace'))
     if command==b'ATZ':conn.sendall(b'\r\nOK\r\n')
     elif command==b'ATD'+target:
      attempts+=1;conn.sendall(b'\xff\x8bCONNECT\r\n'+banner);event('DCD-high-CONNECT',b'\xff\x8b');online=True
     else:checks['unexpected_modem_command']=True
  except (OSError,AssertionError) as error:
   if not stop.is_set():errors.append(str(error))
'''
    text=text[:start]+peer+text[end:]
    for tag in ('B','A'):
        needle='D:'+chr(92)*2+'SNAP '+tag;assert text.count(needle)==1
        text=text.replace(needle,needle+'\nD:'+chr(92)*2+'VECT '+tag)
    text=text.replace('transparent:1','transparent:0').replace('cputype=386','cputype=8086')
    needle="commands[:2]==['ATZ',('ATD'+target.decode('ascii'))]";assert text.count(needle)==1
    text=text.replace(needle,"commands==([] if EXPECT_GAP else ['ATZ','ATD'+target.decode('ascii')])")
    text=text.replace("if mode in ('success','hangup','redial','direct'):","if not EXPECT_GAP and mode in ('success','hangup','redial','direct'):")
    module=types.ModuleType('manual_cancel_lab');module.__dict__.update(connection.__dict__)
    module.__dict__.update(CASE_OUT=out,events=events,EXPECT_GAP=gap,subprocess=Backend(backend))
    exec(compile(text,__file__,'exec'),module.__dict__);return module


def observer(out,map_path):
    names=symbols(map_path);path=out/'observer.asm';shutil.copy2(ROOT/'standalone/manual_cancel_watch.asm',path)
    definitions={key:str(names[name][1]) for key,name in [('STATE','connection_state'),('STATUS','connection_status'),('CARRIER_SEEN','connection_carrier_seen'),('PAUSED','uart_tx_paused')]}
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in definitions.items()],str(path),'-o',str(out/'WATCH.COM')],check=True)
    (out/'offsets.json').write_text(json.dumps(definitions,indent=2)+'\n');return (out/'WATCH.COM').read_bytes()


def vectors(out):
    source=r'''BITS 16
CPU 8086
ORG 100h
push cs
pop ds
xor ax,ax
mov es,ax
pushf
cli
mov ax,[es:0x84]
mov [buffer],ax
mov ax,[es:0x86]
mov [buffer+2],ax
mov ax,[es:0x70]
mov [buffer+4],ax
mov ax,[es:0x72]
mov [buffer+6],ax
popf
mov dx,old_name
cmp byte [0x82],'B'
je write
mov dx,new_name
write:
xor cx,cx
mov ah,0x3c
int 0x21
jc fail
mov bx,ax
mov dx,buffer
mov cx,8
mov ah,0x40
int 0x21
jc fail
cmp ax,8
jne fail
mov ah,0x3e
int 0x21
jc fail
mov ax,0x4c00
int 0x21
fail:
mov ax,0x4c01
int 0x21
old_name: db 'D:\VECOLD.BIN',0
new_name: db 'D:\VECNEW.BIN',0
buffer: times 8 db 0
'''
    path=out/'vectors.asm';path.write_text(source);subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'VECT.COM')],check=True)
    return (out/'VECT.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--baseline-from',type=Path);a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/manual-cancel-dos'/a.label;out.mkdir(parents=True,exist_ok=False);gap=a.baseline_from is not None;inputs={};paths={}
    backend=(ROOT/'build/dosbox-dcd-lab/bin/dosbox-x').resolve();assert backend.is_file()
    if gap:
        origin=a.baseline_from.resolve();assert origin.is_relative_to(ROOT/'build');old=read(origin/'checks.json');assert old['passed'] and old['gap_reproduced']
        binary=origin/'soft/TERMINAL.EXE';assert sha(binary)==old['parent_sha256']
        for name,digest in old['inputs'].items():inputs[name]=digest;paths[name]=origin/'inputs'/name
        map_path=ROOT/'build/program-startup-bank/fixed-01/terminal.map';assert sha(binary)==sha(map_path.with_suffix('.EXE'))
    else:
        binary=ROOT/'build/terminal/TERMINAL.EXE';m=read(binary.parent/'manifest.json');assert sha(binary)==m['binary_sha256'];map_path=binary.parent/'terminal.map'
        for name,digest in m['sources'].items():inputs[name]=digest;paths[name]=ROOT/name
    for path in (Path(__file__),ROOT/'standalone/manual_cancel_watch.asm',ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/test_aspect_script_window_dos.py',ROOT/'standalone/directory_fixtures.py',ROOT/'nix/dosbox-dcd-lab.nix',ROOT/'nix/dosbox-dcd-lab-default.nix',ROOT/'tools/build-dcd-lab',ROOT/'nix/patches/dosbox-dcd-control.patch',ROOT/'nix/flake.lock',ROOT/'build/dosbox-dcd-lab-build.json'):
        name=str(path.relative_to(ROOT));inputs[name]=sha(path);paths[name]=path
    for name,digest in inputs.items():
        assert sha(paths[name])==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(paths[name],target)
    shutil.copy2(binary,out/'admitted.EXE');shutil.copy2(map_path,out/'admitted.map');compiled=observer(out,map_path);vector_probe=vectors(out);rows=[]
    for hard in (0,1):
        name='both' if hard else 'soft';folder=out/name;folder.mkdir();events=[];peer=adapter(out,events,gap,backend)
        shutil.copy2(binary,folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        try:
            r=peer.run(name,'success','p1600 escape p3000 a-d p8000 r e a d y p700 a-x',directory=directory(profile=4),prm=prm(soft=1,hard=hard),profile=4,working_drive='d',observer='WATCH',files={'WATCH.COM':compiled,'VECT.COM':vector_probe},accounting_delta=0 if gap else 1,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0c')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        sample=struct.unpack('<12H',(folder/'CANCEL.BIN').read_bytes());wire=(folder/'serial.bin').read_bytes()
        expected=b'A'+(b'' if gap else b'ATZ\rATDCaseTest:23\r'+ESC+b'[1;16R'+ESC+b'[?62;2cready'+ESC+b'[1;16R+++ATH\r')
        checks=dict(r['checks'],observer_admitted=sample[0]==0x434d and sample[1]!=0 and sample[2]>18 and sample[11]==1,
            actual_initialization_XOFF=sample[3]>8,never_high_before_cancel=sample[4]==sample[5]==0,DTR_low_observed=sample[6]>8,
            actual_cancel_idle=sample[7]==1 and sample[8]==int(gap) and sample[9]==0,
            expected_online=(sample[10]==0 if gap else sample[10]>18),whole_wire_exact=wire==expected,
            observer_vectors_restored=len((folder/'VECOLD.BIN').read_bytes())==8 and (folder/'VECOLD.BIN').read_bytes()==(folder/'VECNEW.BIN').read_bytes())
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,sample=list(sample),wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,sample=list(sample))),flush=True)
    wrapped=backend.with_name('.dosbox-x-wrapped');result=dict(passed=all(r['passed'] for r in rows),gap_reproduced=gap,compatibility_accepted=not gap,cases=rows,parent_sha256=sha(binary),inputs=inputs,
        emulator={'test_backend':True,'wrapper':str(backend),'wrapper_sha256':sha(backend),'binary_sha256':sha(wrapped),'patch_sha256':sha(ROOT/'nix/patches/dosbox-dcd-control.patch')},
        scope=__doc__+' Patched lab DOSBox-X2026.07.02 exposes DCD via opt-in FF bit7/bit3; stock DOSBox nullmodem cannot. Two actual8086 SOFT/BOTH cases with external first-init XOFF, DCD low until retry CONNECT, real Escape/Alt-D, passive MSR/controller observations and hardware/accounting restoration. No product-memory or handler injection. Not stock-emulator, physical UART/modem or full application acceptance.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
