#!/usr/bin/env python3
"""Link the actual OMF resident bridge into an isolated cross-EXEC DOS proof."""
import hashlib,json,subprocess
from pathlib import Path
from build_aspect_resident_service import CHILD as BASE_CHILD
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-resident-bridge'
PARENT=r'''
BITS 16
CPU 8086
%include "resident_bridge.inc"
%include "resident_service.inc"
SEGMENT _TEXT public class=CODE use16
global parent_main,body,forward_callback,descriptor,parent_stack_low,parent_stack_top
extern resident_bridge_initialize,resident_bridge_disable,resident_bridge_entry
extern resident_bridge_callback,resident_bridge_abort
parent_main:
 cli
 mov ax,DGROUP
 mov ss,ax
 mov sp,parent_stack_end
 mov ds,ax
 sti
 mov es,ax
 cld
 mov ah,0x62
 int 0x21
 mov [descriptor+RS_PARENT_PSP],bx
 mov ax,ds
 mov [descriptor+RS_PARENT_DS],ax
 mov dx,cs
 cmp ax,dx ;Diagnostic must actually exercise different CS and DS.
 je failed
 mov [exec_block+4],ax
 mov ax,[descriptor+RS_PARENT_PSP]
 mov [exec_block+8],ax
 mov [exec_block+12],ax
 mov di,tail+1
 mov ax,ds
 call hexword
 mov al,':'
 stosb
 mov ax,descriptor
 call hexword
 mov di,parent_stack_low
 mov cx,2048
 mov al,0xcc
 rep stosb
 call configure
 or ax,ax
 jnz failed
 ; Each rejected reconfiguration must leave the prior valid lease installed.
 mov bx,parent_stack_low
 mov cx,parent_stack_top
 xor dx,dx
 mov si,cs
 mov di,forward_callback
 call resident_bridge_initialize
 cmp ax,RB_ARGUMENT
 jne failed
 inc word [invalid_checks]
 mov bx,1
 call invalid
 mov bx,parent_stack_low+1
 call invalid
 mov bx,parent_stack_low
 mov cx,parent_stack_top+1
 call invalid
 mov cx,parent_stack_low+510
 call invalid
 mov cx,parent_stack_low
 call invalid
 mov cx,0xfff2
 call invalid
 mov cx,sp
 call invalid
 mov cx,parent_stack_top
 xor si,si
 xor di,di
 mov dx,body
 call resident_bridge_initialize
 cmp ax,RB_ARGUMENT
 jne failed
 inc word [invalid_checks]
 ; DS!=SS must refuse without replacing the still-valid old lease.
 push ds
 push cs
 pop ds
 call resident_bridge_initialize
 pop ds
 cmp ax,RB_ARGUMENT
 jne failed
 inc word [invalid_checks]
 ; Retain parent only through end of DGROUP stack before DOS EXEC.
 mov ax,ss
 mov bx,sp
 add bx,15
 mov cl,4
 shr bx,cl
 add bx,ax
 sub bx,[descriptor+RS_PARENT_PSP]
 mov es,[descriptor+RS_PARENT_PSP]
 mov ah,0x4a
 int 0x21
 jc failed
 push ds
 pop es
 mov [cs:saved_sp],sp
 mov ax,0x4b00
 mov dx,child_name
 mov bx,exec_block
 int 0x21
 pushf
 pop word [cs:exec_flags]
 cli
 mov ax,DGROUP
 mov ss,ax
 mov sp,[cs:saved_sp]
 mov ds,ax
 mov es,ax
 cld
 sti
 cmp sp,parent_stack_end
 jne failed
 test word [cs:exec_flags],1
 jnz failed
 mov ah,0x4d
 int 0x21
 or ax,ax
 jnz failed
 ; Disable and invalid-reconfigure must retain the disabled state.
 call resident_bridge_disable
 or ax,ax
 jnz failed
 call far [entry_pointer]
 cmp ax,RB_INACTIVE
 jne failed
 xor dx,dx
 call resident_bridge_initialize
 cmp ax,RB_ARGUMENT
 jne failed
 inc word [invalid_checks]
 call far [entry_pointer]
 cmp ax,RB_INACTIVE
 jne failed
 cmp word [descriptor+RS_FAILURES],0
 jne failed
 cmp word [descriptor+RS_CALLS],32
 jne failed
 cmp word [descriptor+RS_PARENT_CHECKS],32
 jne failed
 cmp word [descriptor+RS_CALLBACKS],8
 jne failed
 cmp word [descriptor+RS_INJECTED],48
 jne failed
 cmp word [descriptor+RS_TIMER_PARENT],0
 je failed
 cmp word [abort_fell_through],0
 jne failed
 ; Final intact guards after child repaired each deliberate corruption.
 mov si,parent_stack_low-16
 mov cx,16
 mov al,0xa6
 call guard
 mov si,parent_stack_top
 mov cx,16
 mov al,0x5a
 call guard
 mov si,parent_stack_low
 mov cx,2048
.scan:
 cmp byte [si],0xcc
 jne .used
 inc si
 loop .scan
.used:
 mov ax,parent_stack_top
 sub ax,si
 mov [descriptor+RS_LOW_SP],ax
 mov dx,stack_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,parent_stack_low
 mov cx,2048
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
 mov dx,report_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,descriptor
 mov cx,54
 mov ah,0x40
 int 0x21
 jc failed
 mov ah,0x3e
 int 0x21
 mov ax,0x4c00
 int 0x21
configure:
 mov bx,parent_stack_low
 mov cx,parent_stack_top
 mov dx,body
 mov si,cs
 mov di,forward_callback
 call resident_bridge_initialize
 ret
invalid:
 mov dx,body
 mov si,cs
 mov di,forward_callback
 call resident_bridge_initialize
 cmp ax,RB_ARGUMENT
 jne failed
 inc word [invalid_checks]
 ret
body:
 inc word [descriptor+RS_CALLS]
 mov [current_op],ax
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne failed
 cmp ax,[descriptor+RS_PARENT_DS]
 jne failed
 inc word [descriptor+RS_PARENT_CHECKS]
 mov ah,0x62
 int 0x21
 mov [descriptor+RS_LAST_PSP],bx
 cmp bx,[descriptor+RS_CHILD_PSP]
 je .psp_ok
 inc word [descriptor+RS_FAILURES]
.psp_ok:
 int 0x60
 cmp word [current_op],1
 je .abort
 cmp word [current_op],2
 je .low
 cmp word [current_op],3
 je .high
 xor ax,ax
 mov bx,0x3fd
 call resident_bridge_callback
 and ax,0x60
 cmp ax,0x60
 je .callback_ok
 inc word [descriptor+RS_FAILURES]
.callback_ok:
 pushf
 pop ax
 test ax,0x200
 jz .no_wait
 xor ax,ax
 int 0x1a
 mov si,dx
.wait:
 xor ax,ax
 int 0x1a
 cmp dx,si
 je .wait
.no_wait:
 int 0x60
 mov ax,0x3456
 ret
.abort:
 call deep_one
 inc word [abort_fell_through]
 ret
.low:
 mov byte [parent_stack_low-1],0
 mov ax,0x3456
 ret
.high:
 mov byte [parent_stack_top],0
 mov ax,0x3456
 ret
deep_one:
 sub sp,64
 call deep_two
 inc word [abort_fell_through]
 ret
deep_two:
 sub sp,64
 mov ax,0x4321
 call resident_bridge_abort
 inc word [abort_fell_through]
 ret
forward_callback:
 call far [descriptor+RS_CALLBACK]
 retf
guard:
 cmp byte [si],al
 jne failed
 inc si
 loop guard
 ret
failed:
 mov [failure_ax],ax
 mov dx,failure_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .exit
 mov bx,ax
 mov dx,descriptor
 mov cx,58
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
.exit:
 mov ax,0x4c01
 int 0x21
hexword:
 push ax
 mov cl,12
.shift:
 pop ax
 push ax
 shr ax,cl
 and al,15
 add al,'0'
 cmp al,'9'
 jbe .digit
 add al,7
.digit:
 stosb
 sub cl,4
 jnc .shift
 pop ax
 ret
saved_sp: dw 0
exec_flags: dw 0
SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA STACK
descriptor: dw 0x5253,0,0,resident_bridge_entry,seg resident_bridge_entry
 times 18 dw 0
 dw parent_stack_low,parent_stack_top
invalid_checks: dw 0
abort_fell_through: dw 0
current_op: dw 0
failure_ax: dw 0
entry_pointer: dw resident_bridge_entry,seg resident_bridge_entry
child_name: db 'CHILD.COM',0
report_name: db 'PARENT.BIN',0
stack_name: db 'STACK.BIN',0
failure_name: db 'FAILURE.BIN',0
exec_block: dw 0,tail,0,0x5c,0,0x6c,0
tail: db 9,'0000:0000',13
 times 127 db 0
SEGMENT STACK stack align=16 class=STACK use16
 times 32 db 0
parent_stack_low: times 2048 db 0
parent_stack_top:
 times 6112 db 0
parent_stack_end:
'''

def child_source():
 s=BASE_CHILD.replace('mov ax,0x1234','mov ax,[current_request]').replace("test word [mode],1","test word [current_if],1")
 s=s.replace('mode: dw 0','mode: dw 0\ncurrent_request: dw 0\ncurrent_if: dw 0\nexpected_result: dw 0\ndivisor: dw 5')
 s=s.replace('.next:\n mov [saved_sp],sp','.next:\n mov ax,[mode]\n xor dx,dx\n div word [divisor]\n and ax,1\n mov [current_if],ax\n mov [current_request],dx\n mov ax,0xfffb\n cmp dx,1\n ja .expect\n mov ax,0x4321\n je .expect\n mov ax,0x3456\n.expect:\n mov [expected_result],ax\n cmp dx,4\n jne .prepared\n mov es,[parent_ds]\n mov bx,[descriptor]\n mov bx,[es:bx+46]\n mov byte [es:bx-1],0\n.prepared:\n mov [cs:saved_sp],sp')
 s=s.replace('cmp ax,0x3456\n jne .bad','cmp ax,[expected_result]\n jne .bad')
 s=s.replace('.checked:\n sti','.checked:\n mov es,[parent_ds]\n mov bx,[descriptor]\n mov dx,[es:bx+46]\n mov bx,dx\n mov byte [es:bx-1],0xa6\n mov bx,[descriptor]\n mov bx,[es:bx+48]\n mov byte [es:bx],0x5a\n sti')
 s=s.replace('cmp word [cases],32','cmp word [cases],40').replace('cmp word [parent_interrupts],64','cmp word [parent_interrupts],40')
 # Reentry counter is diagnostic evidence published by child after all calls.
 s=s.replace('mov ax,[callbacks]\n mov [es:bx+RS_CALLBACKS],ax','mov ax,[callbacks]\n mov [es:bx+RS_CALLBACKS],ax\n mov [es:bx+RS_REFUSED],ax')
 return s

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 for name,text in [('parent.asm',PARENT),('child.asm',child_source())]:(OUT/name).write_text(text)
 include='-I'+str(ROOT/'src/aspect')+'/'
 subprocess.run(['nasm','-fobj',include,str(OUT/'parent.asm'),'-o',str(OUT/'parent.obj')],check=True)
 subprocess.run(['nasm','-fobj',include,str(ROOT/'src/aspect/resident_bridge.asm'),'-o',str(OUT/'bridge.obj'),'-l',str(OUT/'bridge.lst')],check=True)
 subprocess.run(['wlink','system','dos','option','quiet','option','start=parent_main','option','map='+str(OUT/'parent.map'),'name',str(OUT/'PARENT.EXE'),'file',str(OUT/'parent.obj')+','+str(OUT/'bridge.obj')],check=True)
 subprocess.run(['nasm','-fbin',include,str(OUT/'child.asm'),'-o',str(OUT/'CHILD.COM'),'-l',str(OUT/'child.lst')],check=True)
 sources=[Path(__file__),ROOT/'src/aspect/resident_bridge.asm',ROOT/'src/aspect/resident_bridge.inc',ROOT/'src/aspect/resident_service.inc',ROOT/'standalone/build_aspect_resident_service.py']
 manifest=dict(kind='actual-OMF-resident-bridge-crossEXEC-proof',binaries={n:sha(OUT/n) for n in ['PARENT.EXE','CHILD.COM']},sources={str(p.relative_to(ROOT)):sha(p) for p in sources},original_inputs=[])
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
