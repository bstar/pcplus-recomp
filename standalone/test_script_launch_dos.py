#!/usr/bin/env python3
"""Actual source-built ASPECT child from live terminal menu and duplex resume.
All files are synthetic under build; no vendor executable/private script used.
"""
import hashlib,json,shutil,struct,subprocess,sys
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
  ('script-child-unsupported',unsupported,True,False,2),
  ('script-child-missing',compiled,False,False,2),
  ('script-prompt-cancel',compiled,True,True,0)]:
  fixture=OUT/name;fixture.mkdir(exist_ok=True)
  shutil.copyfile(terminal,fixture/'TERMINAL.EXE')
  (fixture/'ASPECT.EXE').unlink(missing_ok=True)
  if helper:shutil.copyfile(runner,fixture/'ASPECT.EXE')
  harness.BINARY=fixture/'TERMINAL.EXE'
  keys='p2200 a-z p300 a p300 '+('escape p300 escape' if escape else 't e s t . a s x enter p1100 space')+' p500 r e a d y p700 a-x'
  result=harness.run(name,'direct',keys,working_drive='d',arguments='@D:\\TEST.PRM',files={'TEST.ASX':data,'SCRIPT.COM':observer},observer='SCRIPT')
  folder=ROOT/'build/connection-dos'/name
  magic,bits,ticks,_=struct.unpack('<4H',(folder/'SCRIPT.BIN').read_bytes())
  result['checks'].update(observed_expected_child_console=magic==0x4d43 and ticks>0 and bits==want,
   ordinary_keyboard_resumes=b'ready' in (folder/'serial.bin').read_bytes(),
   runner_and_terminal_unchanged=hashlib.sha256(terminal.read_bytes()).hexdigest()==digest and hashlib.sha256(runner.read_bytes()).hexdigest()==rdigest)
  result['passed']=all(result['checks'].values());result['observer_bits']=bits
  (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  assert result['passed'],result;cases.append(result)
 harness.BINARY=terminal
 result=dict(passed=True,cases=cases,terminal_sha256=digest,runner_sha256=rdigest,
  limitations=['Virtual UART/nullmodem and DOSBox-X only; physical hardware remains unverified.','Child console output independently sampled by INT1C; source-built interpreter does not receive live terminal UART scheduling.'],
  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Script launch actual DOS:',len(cases),'cases passed')
if __name__=='__main__':main()
