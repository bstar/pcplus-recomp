#!/usr/bin/env python3
"""Measure DOS EXEC allocation thresholds for identical MZ load images."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
from mz_layout import align_header,inspect
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ASM=r'''
bits 16
cpu 8086
org 0x100
start:
 cli
 mov ax,cs
 mov ss,ax
 mov sp,4096
 sti
 mov ds,ax
 mov es,ax
 mov bx,256
 mov ah,0x4a
 int 0x21
 jc failed
 mov bx,1
 mov ah,0x48
 int 0x21
 jc failed
 mov [envseg],ax
 mov [params],ax
 mov es,ax
 xor ax,ax
 mov [es:0],ax
 mov word [es:2],1
 mov word [es:4],'X'
 mov ax,cs
 mov [params+4],ax
 mov [params+8],ax
 mov [params+12],ax
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov [loghandle],ax
 mov word [keep],64
.loop:
 mov word [which],0
.case:
 mov bx,0xffff
 mov ah,0x48
 int 0x21
 jnc failed
 mov [baseline],bx
 sub bx,[keep]
 dec bx
 mov ah,0x48
 int 0x21
 jc failed
 mov [filler],ax
 mov bx,0xffff
 mov ah,0x48
 int 0x21
 jnc failed
 mov [available],bx
 mov ax,cs
 mov es,ax
 mov bx,params
 mov dx,small
 cmp word [which],0
 je .exec
 mov dx,aligned
.exec:
 mov [cs:saved_sp],sp
 mov ax,0x4b00
 int 0x21
 mov [cs:exec_error],ax
 mov word [cs:exec_failed],0
 jnc .restore
 mov word [cs:exec_failed],1
.restore:
 cli
 mov ax,cs
 mov ss,ax
 mov sp,[cs:saved_sp]
 mov ds,ax
 sti
 mov word [child_status],0xffff
 cmp word [exec_failed],0
 jne .free
 mov word [exec_error],0
 mov ah,0x4d
 int 0x21
 mov [child_status],ax
.free:
 mov es,[filler]
 mov ah,0x49
 int 0x21
 jc failed
 mov bx,0xffff
 mov ah,0x48
 int 0x21
 jnc failed
 mov [after_free],bx
 cmp bx,[baseline]
 jne failed
 mov bx,[loghandle]
 mov dx,record
 mov cx,12
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,12
 jne failed
 inc word [which]
 cmp word [which],2
 jb .case
 inc word [keep]
 cmp word [keep],224
 jbe .loop
 mov bx,[loghandle]
 mov ah,0x3e
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
record:
which: dw 0
keep: dw 0
available: dw 0
exec_error: dw 0
child_status: dw 0
after_free: dw 0
baseline: dw 0
filler: dw 0
loghandle: dw 0
envseg: dw 0
exec_failed: dw 0
saved_sp: dw 0
params: dw 0,tail,0,0x5c,0,0x6c,0
tail: db 0,13
small: db 'MZ0.EXE',0
aligned: db 'MZ1.EXE',0
filename: db 'MEMEXEC.BIN',0
'''

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 # Authored five-byte DOS return0 program, explicit1KB extra allocation.
 header=struct.pack('<16H',0x5a4d,37,1,0,2,64,64,0,256,0,0,0,28,0,0,0)
 original=header+bytes.fromhex('b8004ccd21');aligned,layout=align_header(original)
 assert aligned[inspect(aligned)['header_bytes']:]==original[32:]
 (out/'MZ0.EXE').write_bytes(original);(out/'MZ1.EXE').write_bytes(aligned)
 (out/'probe.asm').write_text(ASM)
 subprocess.run(['nasm','-fbin',str(out/'probe.asm'),'-o',str(out/'PROBE.COM')],check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nPROBE\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 assert (out/'PASS.TXT').is_file() and not (out/'FAIL.TXT').exists()
 raw=(out/'MEMEXEC.BIN').read_bytes();assert len(raw)==161*2*12
 records=[dict(zip(['image','retained_free_paragraphs','measured_free_paragraphs','EXEC_error','child_status','free_after_release'],struct.unpack_from('<6H',raw,i))) for i in range(0,len(raw),12)]
 thresholds=[]
 for image in (0,1):
  rows=[r for r in records if r['image']==image];assert [r['retained_free_paragraphs'] for r in rows]==list(range(64,225))
  threshold=min(r['measured_free_paragraphs'] for r in rows if not r['EXEC_error']);thresholds.append(threshold)
  for r in rows:
   assert r['measured_free_paragraphs']==r['retained_free_paragraphs']
   assert r['EXEC_error']==(8 if r['measured_free_paragraphs']<threshold else 0)
   assert r['child_status']==(0xffff if r['EXEC_error'] else 0)
  assert len({r['free_after_release'] for r in rows})==1
 assert (thresholds[0]-thresholds[1])*16==layout['header_padding_added']==464
 report=dict(passed=True,original_inputs=[],cases=len(records),CPU='DOS8086',threshold_bytes=[n*16 for n in thresholds],layout=layout,
  sources={str(Path(__file__).relative_to(ROOT)):sha(__file__),'standalone/mz_layout.py':sha(ROOT/'standalone/mz_layout.py')},
  authored_original_sha256=sha(out/'MZ0.EXE'),authored_aligned_sha256=sha(out/'MZ1.EXE'),probe_sha256=sha(out/'PROBE.COM'),records_sha256=sha(out/'MEMEXEC.BIN'),
  scope=__doc__+'322 controlled-memory EXEC calls: DOS8 below threshold, return0 above, allocator fully restored. Same code/relocations/exact module minimum, different header padding/page threshold. Internal DOSBox loader observation, not real DOS/hardware capacity.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS MZ DOS calibration:',len(records),'EXEC calls; thresholds',report['threshold_bytes'])
if __name__=='__main__':main()
