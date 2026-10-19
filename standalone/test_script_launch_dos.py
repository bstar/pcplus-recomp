#!/usr/bin/env python3
"""Actual source-built ASPECT child from live terminal menu and duplex resume.
All files are synthetic under build; no vendor executable/private script used.
"""
import argparse,hashlib,json,shutil,struct,subprocess,sys
from pathlib import Path
import test_connection_dos as harness
ROOT=harness.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
OUT=ROOT/'build/script-launch-dos'

def watcher():
 base=(ROOT/'standalone/command_menu_watch.asm').read_text()
 tail=base[base.index('resident_end:'):].replace('10246','8').replace('D:\\MVIEW.BIN','D:\\SCRIPT.BIN')
 head=r'''BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dw 0,0
sample: dw 4d43h,0,0,0
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 inc word [sample+4]
 mov ax,0b800h
 mov es,ax
 mov si,success
 mov bx,1
 call scan
 mov si,failure
 mov bx,2
 call scan
 mov si,prompt
 mov bx,4
 call scan
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_vector]
scan:
 xor di,di
.next:
 push si
 push di
.match:
 lodsb
 or al,al
 jz .found
 cmp al,[es:di]
 jne .miss
 add di,2
 cmp di,4000
 jb .match
.miss:
 pop di
 pop si
 add di,2
 cmp di,4000
 jb .next
 ret
.found:
 pop di
 pop si
 or [sample+2],bx
 ret
success: db 'SCRIPT LIVE',0
failure: db 'Program could not run.',0
prompt: db 'Press a key to return to the terminal.',0
'''
 (OUT/'watch.asm').write_text(head+tail)
 subprocess.run(['nasm','-f','bin',str(OUT/'watch.asm'),'-o',str(OUT/'SCRIPT.COM')],check=True)
 return (OUT/'SCRIPT.COM').read_bytes()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--case');parser.add_argument('--expected-exit',type=int,default=0);args=parser.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 terminal=harness.BINARY;runner=ROOT/'build/aspect-runner/ASPECT.EXE'
 assert runner.is_file(),'Build source-only ASPECT runner first'
 digest=hashlib.sha256(terminal.read_bytes()).hexdigest();rdigest=hashlib.sha256(runner.read_bytes()).hexdigest()
 observer=watcher();cases=[]
 compiled=compile_source('proc main\nmessage "SCRIPT LIVE"\nendproc\n')
 # Unsupported native opcode FD is a declared interpreter error, not execution
 # of arbitrary original instructions. Preserve a valid header/procedure prefix.
 unsupported=bytes.fromhex('00 cf fd 94')
 for name,data,helper,escape,want in [
  ('script-child-success',compiled,True,False,5),
  ('script-serial-handback',compile_source('proc main\ntransmit "READY^M"\nwaitfor "MATCH" 5\nmessage "SCRIPT LIVE"\nendproc\n'),True,False,5),
  ('script-child-unsupported',unsupported,True,False,2),
  ('script-child-missing',compiled,False,False,2),
  ('script-prompt-cancel',compiled,True,True,0)]:
  if args.case and name!=args.case:continue
  fixture=OUT/name;fixture.mkdir(exist_ok=True)
  shutil.copyfile(terminal,fixture/'TERMINAL.EXE')
  (fixture/'ASPECT.EXE').unlink(missing_ok=True)
  if helper:shutil.copyfile(runner,fixture/'ASPECT.EXE')
  harness.BINARY=fixture/'TERMINAL.EXE'
  keys='p2200 a-z p300 a p300 '+('escape p300 escape' if escape else 't e s t . a s x enter '+('p3000' if name=='script-serial-handback' else 'p1100')+' space')+' p500 r e a d y p700 a-x'
  serial=name=='script-serial-handback'
  result=harness.run(name,'success' if serial else 'direct',keys,expected=args.expected_exit,working_drive='d',arguments='@D:\\TEST.PRM'+(' /D:CaseTest:23' if serial else ''),files={'TEST.ASX':data,'SCRIPT.COM':observer},observer=None if serial else 'SCRIPT',online_updates=[(4,b'MATCH\x1b[2;1HREMAINDER')] if serial else ())
  folder=ROOT/'build/connection-dos'/name
  magic,bits,ticks,_=(0,0,0,0) if serial else struct.unpack('<4H',(folder/'SCRIPT.BIN').read_bytes())
  if not serial:result['checks']['observed_expected_child_console']=magic==0x4d43 and ticks>0 and bits==want
  result['checks'].update(ordinary_keyboard_resumes=b'ready' in (folder/'serial.bin').read_bytes(),
   runner_and_terminal_unchanged=hashlib.sha256(terminal.read_bytes()).hexdigest()==digest and hashlib.sha256(runner.read_bytes()).hexdigest()==rdigest)
  if serial:
   wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
   result['checks'].update(native_script_transmit_on_actual_owned_port=b'READY\r' in wire,unread_serial_suffix_reaches_parent_parser=screen[160:178:2]==b'REMAINDER')
  result['passed']=all(result['checks'].values());result['observer_bits']=None if serial else bits
  (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  assert result['passed'],result;cases.append(result)
 harness.BINARY=terminal
 history=[]
 for old in ['failed-serial-handback-observer','failed-serial-handback-no-observer','failed-serial-handback-exit6']:
  folder=OUT/old
  if folder.exists():
   prior=json.loads((folder/'result.json').read_text())
   identity_path=folder/'identity.json';identity=None
   if identity_path.exists():
    identity=json.loads(identity_path.read_text())
    assert identity['result_sha256']==hashlib.sha256((folder/'result.json').read_bytes()).hexdigest()
    assert identity['terminal_sha256']==prior['binary_sha256']
   history.append(dict(case=old,terminal_sha256=prior['binary_sha256'],runner_sha256=identity['runner_sha256'] if identity else None,
    runner_identity_source=str(identity_path.relative_to(ROOT)) if identity else 'Unknown: no archived runner identity; never substitute current binary',
    runner_identity_sha256=hashlib.sha256(identity_path.read_bytes()).hexdigest() if identity else None,
    failed_checks=[k for k,v in prior['checks'].items() if not v],
    confirmed_terminal_exit=6,characterization=old.endswith('exit6'),
    reason='Parent UART IRQ/IER remained disabled during PROGRAM return-key wait; trailing incoming UART bytes overran RBR. Script-only serviced prompt restores parent ISR and polls flow before waiting.',
    artifact_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(folder.iterdir()) if f.name in ['result.json','serial.bin','SCREEN.BIN','BEFORE.BIN','AFTER.BIN','dosbox.conf']}))
 result=dict(passed=True,cases=cases,terminal_sha256=digest,runner_sha256=rdigest,regression_history=history,case_filter=args.case,expected_terminal_exit=args.expected_exit,
  limitations=['Virtual UART/nullmodem and DOSBox-X only; physical hardware remains unverified.','Child console output independently sampled by INT1C. Dedicated ASIOv1 lease returns unread bytes; raw child receive is distinct from terminal screen rendering.'],
  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Script launch actual DOS:',len(cases),'cases passed')
if __name__=='__main__':main()
