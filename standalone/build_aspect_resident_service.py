#!/usr/bin/env python3
"""Original-free parent/child COM proof of DS=SS far-service stack switching."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-resident-service'
PARENT=r'''
BITS 16
CPU 8086
ORG 100h
jmp main
%include "resident_service.asm"
main:
 cli
 mov ax,cs
 mov ss,ax
 mov sp,main_stack_top
 mov ds,ax
 mov es,ax
 cld
 sti
 mov [resident_service_parent_ds],ax
 mov [resident_service_descriptor+RS_PARENT_DS],ax
 mov [resident_service_descriptor+RS_PARENT_PSP],ax
 mov word [resident_service_descriptor+RS_MAGIC],0x5253
 mov word [resident_service_descriptor+RS_ENTRY],resident_service_entry
 mov [resident_service_descriptor+RS_ENTRY+2],ax
 mov [exec_block+4],ax
 mov [exec_block+8],ax
 mov [exec_block+12],ax
 mov di,tail+1
 call hexword
 mov al,':'
 stosb
 mov ax,resident_service_descriptor
 call hexword
 mov bx,(program_end-$$+0x100+15)/16
 mov ah,0x4a
 int 0x21
 jc failed
 mov [saved_sp],sp
 mov ax,0x4b00
 mov dx,child_name
 mov bx,exec_block
 int 0x21
 pushf
 pop word [cs:exec_flags]
 cli
 mov ax,cs
 mov ss,ax
 mov sp,[cs:saved_sp]
 mov ds,ax
 mov es,ax
 sti
 test word [exec_flags],1
 jnz failed
 mov ah,0x4d
 int 0x21
 or ax,ax
 jnz failed
 cmp word [resident_service_descriptor+RS_FAILURES],0
 jne failed
 cmp word [resident_service_descriptor+RS_CALLS],32
 jne failed
 cmp word [resident_service_descriptor+RS_REFUSED],32
 jne failed
 cmp word [resident_service_descriptor+RS_PARENT_CHECKS],32
 jne failed
 cmp word [resident_service_descriptor+RS_CALLBACKS],32
 jne failed
 cmp word [resident_service_descriptor+RS_INJECTED],96
 jne failed
 cmp word [resident_service_descriptor+RS_TIMER_PARENT],0
 je failed
 cmp word [resident_service_descriptor+RS_BUSY],0
 jne failed
 mov si,resident_service_stack_low
 mov cx,32
 mov al,0xa6
 call guard
 mov si,resident_service_stack_high
 mov cx,32
 mov al,0x5a
 call guard
 ; Sentinel high-water is observed touched stack extent, not peakSP proof.
 mov si,resident_service_stack
 mov cx,RS_STACK_BYTES
.scan:
 cmp byte [si],0xcc
 jne .used
 inc si
 loop .scan
.used:
 mov ax,resident_service_stack_top
 sub ax,si
 mov [resident_service_descriptor+RS_LOW_SP],ax
 mov dx,report_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,resident_service_descriptor
 mov cx,RS_DESCRIPTOR_BYTES
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,RS_DESCRIPTOR_BYTES
 jne failed
 mov ah,0x3e
 int 0x21
 mov dx,success
 mov ah,9
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
guard:
 cmp byte [si],al
 jne failed
 inc si
 loop guard
 ret
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
child_name: db 'CHILD.COM',0
report_name: db 'PARENT.BIN',0
success: db 'PASS resident service32 cases',13,10,'$'
exec_block: dw 0,tail,0,0x5c,0,0x6c,0
tail: db 9,'0000:0000',13
 times 127 db 0
main_stack: times 1024 db 0
main_stack_top:
program_end:
'''
CHILD=r'''
BITS 16
CPU 8086
ORG 100h
%include "resident_service.inc"
jmp main
parent_ds: dw 0
descriptor: dw 0
service: dw 0,0
old60: dw 0,0
old1c: dw 0,0
child_psp: dw 0
saved_sp: dw 0
mode: dw 0
cases: dw 0
failures: dw 0
injected: dw 0
timer_parent: dw 0
callbacks: dw 0
callback_ss: dw 0
callback_sp: dw 0
callback_flags: dw 0
callback_result: dw 0
before_flags: dw 0
after_flags: dw 0
; These handlers run in the child code segment even while SS/DS name parent.
; Save DS before installing child DS; chain timer through its original vector.
irq60:
 push ax
 push bx
 push ds
 push cs
 pop ds
 inc word [injected]
 mov ax,ss
 cmp ax,[parent_ds]
 jne .done
 inc word [parent_interrupts]
.done:
 pop ds
 pop bx
 pop ax
 iret
parent_interrupts: dw 0
irq1c:
 push ax
 push ds
 push cs
 pop ds
 mov ax,ss
 cmp ax,[parent_ds]
 jne .done
 inc word [timer_parent]
.done:
 pop ds
 pop ax
 jmp far [cs:old1c]
callback:
 RS_SAVE_FRAME
 mov bp,sp
 cli
 mov ax,ss
 mov [cs:callback_ss],ax
 mov [cs:callback_sp],sp
 mov ax,[ss:bp+RS_FRAME_FLAGS]
 mov [cs:callback_flags],ax
 mov ax,cs
 mov ss,ax
 mov sp,callback_top
 mov ds,ax
 mov ax,[callback_flags]
 and ax,0xfbff
 push ax
 popf
 inc word [callbacks]
 ; Verify typed request from parent before volatile DOS work.
 mov es,[callback_ss]
 mov bp,[callback_sp]
 cmp word [es:bp+RS_FRAME_AX],0
 jne cb_bad
 cmp word [es:bp+RS_FRAME_BX],0x3fd
 jne cb_bad
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne cb_bad
 mov ax,ss
 cmp ax,[child_psp]
 jne cb_bad
 mov ah,0x62
 int 0x21
 cmp bx,[child_psp]
 jne cb_bad
 mov ax,0x9999
 mov bx,0x8888
 call far [service]
 cmp ax,0xfffe
 jne cb_bad
 cmp bx,0x8888
 jne cb_bad
 pushf
 pop ax
 xor ax,[callback_flags]
 test ax,0x200
 jnz cb_bad
 int 0x60
 mov dx,0x3fd
 in al,dx ;Real emulated child-owned COM1 LSR, no parent UART ownership.
 xor ah,ah
 mov [callback_result],ax
 jmp cb_restore
cb_bad:
 inc word [failures]
cb_restore:
 cli
 mov ax,[callback_ss]
 mov dx,[callback_sp]
 mov ss,ax
 mov sp,dx
 mov ds,ax
 mov bp,sp
 mov ax,[cs:callback_result]
 mov [ss:bp+RS_FRAME_AX],ax
 RS_RESTORE_FRAME
main:
 mov ax,cs
 mov ds,ax
 mov [child_psp],ax
 mov si,0x81
 call parse
 mov [parent_ds],ax
 inc si
 call parse
 mov [descriptor],ax
 mov bx,ax
 mov es,[parent_ds]
 cmp word [es:bx+RS_MAGIC],0x5253
 jne failed
 mov ax,[es:bx+RS_ENTRY]
 mov [service],ax
 mov ax,[es:bx+RS_ENTRY+2]
 mov [service+2],ax
 mov ax,cs
 mov [es:bx+RS_CHILD_PSP],ax
 mov [es:bx+RS_CHILD_DS],ax
 mov word [es:bx+RS_CALLBACK],callback
 mov [es:bx+RS_CALLBACK+2],ax
 mov ax,0x3560
 int 0x21
 mov [old60],bx
 mov [old60+2],es
 mov dx,irq60
 mov ax,0x2560
 int 0x21
 mov ax,0x351c
 int 0x21
 mov [old1c],bx
 mov [old1c+2],es
 mov dx,irq1c
 mov ax,0x251c
 int 0x21
.next:
 mov [saved_sp],sp
 mov ax,0x1234
 mov bx,0x2345
 mov cx,0x3456
 mov dx,0x4567
 mov si,0x5678
 mov di,0x6789
 mov bp,0x789a
 push ax
 mov ax,0x1357
 mov es,ax
 pop ax
 test word [mode],1
 jz .if_clear
 sti
 jmp .invoke
.if_clear:
 cli
.invoke:
 stc
 std
 pushf
 pop word [before_flags]
 call far [service]
 pushf
 pop word [after_flags]
 cld
 cmp ax,0x3456
 jne .bad
 cmp bx,0x2345
 jne .bad
 cmp cx,0x3456
 jne .bad
 cmp dx,0x4567
 jne .bad
 cmp si,0x5678
 jne .bad
 cmp di,0x6789
 jne .bad
 cmp bp,0x789a
 jne .bad
 mov ax,es
 cmp ax,0x1357
 jne .bad
 mov ax,ds
 cmp ax,[child_psp]
 jne .bad
 mov ax,ss
 cmp ax,[child_psp]
 jne .bad
 mov ax,[before_flags]
 cmp ax,[after_flags]
 jne .bad
 cmp sp,[saved_sp]
 jne .bad
 jmp .checked
.bad:
 inc word [failures]
.checked:
 sti
 inc word [cases]
 inc word [mode]
 cmp word [cases],32
 jb .next
 ; Check child-owned callback redzones before returning memory to DOS.
 mov si,callback_low
 mov cx,32
 mov al,0xa6
 call guard
 mov si,callback_high
 mov cx,32
 mov al,0x5a
 call guard
 mov es,[parent_ds]
 mov bx,[descriptor]
 mov ax,[failures]
 add [es:bx+RS_FAILURES],ax
 mov ax,[injected]
 mov [es:bx+RS_INJECTED],ax
 mov ax,[timer_parent]
 mov [es:bx+RS_TIMER_PARENT],ax
 mov ax,[callbacks]
 mov [es:bx+RS_CALLBACKS],ax
 mov ax,[cases]
 mov [es:bx+RS_CHILD_CASES],ax
 cmp word [parent_interrupts],64
 je .restore
 inc word [es:bx+RS_FAILURES]
.restore:
 mov dx,[old60]
 mov ds,[old60+2]
 mov ax,0x2560
 int 0x21
 push cs
 pop ds
 mov dx,[old1c]
 mov ds,[old1c+2]
 mov ax,0x251c
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c02
 int 0x21
guard:
 cmp byte [si],al
 je .good
 inc word [failures]
.good:
 inc si
 loop guard
 ret
parse:
 xor ax,ax
 mov cx,4
.loop:
 mov dl,[si]
 inc si
 sub dl,'0'
 cmp dl,9
 jbe .digit
 sub dl,7
.digit:
 shl ax,1
 shl ax,1
 shl ax,1
 shl ax,1
 xor dh,dh
 or ax,dx
 loop .loop
 ret
callback_low: times 32 db 0xa6
callback_stack: times RS_STACK_BYTES db 0xcc
callback_top:
callback_high: times 32 db 0x5a
'''
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 for name,source in [('PARENT',PARENT),('CHILD',CHILD)]:
  (OUT/(name+'.asm')).write_text(source)
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'src/aspect')+'/',str(OUT/(name+'.asm')),'-o',str(OUT/(name+'.COM')),'-l',str(OUT/(name+'.lst'))],check=True)
 manifest=dict(kind='isolated-source-owned-8086-far-service',stack_slice_bytes=1024,redzone_bytes=32,
  binaries={name:sha(OUT/name) for name in ['PARENT.COM','CHILD.COM']},
  sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/aspect/resident_service.asm',ROOT/'src/aspect/resident_service.inc']},original_inputs=[])
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
