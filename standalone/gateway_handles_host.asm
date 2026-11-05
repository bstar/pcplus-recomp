; Source-only DOS inheritance probe. No CRT IO occurs inside the JFT lease.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern process_run,process_psp,process_keep_paragraphs,process_minimum_paragraphs
extern _process_handles_begin,_process_handles_end,_process_handles_recover
global handles_probe_start,handles_probe_stack_top
global _small_code_
_small_code_:
..start:
handles_probe_start:
 mov dx,es
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,handles_probe_stack_top
 sti
 cld
 mov [process_psp],dx
 sub ax,dx
 mov bx,handles_probe_stack_top
 add bx,15
 mov cl,4
 shr bx,cl
 add ax,bx
 mov [process_keep_paragraphs],ax
 mov [process_minimum_paragraphs],ax
 mov dx,private_name
 call create
 mov [fds],ax
 mov bx,ax
 mov dx,prefix
 call write_one
 mov ax,[fds]
 add al,'0'
 mov [tail+1],al
%ifdef TWO_HANDLES
 mov dx,second_name
 call create
 mov [fds+2],ax
 mov bx,ax
 mov dx,prefix
 call write_one
 mov ax,[fds+2]
 add al,'0'
 mov [tail+3],al
%endif
%ifndef UNISOLATED
 mov ax,handle_count
 push ax
 mov ax,fds
 push ax
 call far _process_handles_begin
 add sp,4
 or ax,ax
 jnz failed
%ifdef RECOVER_PARTIAL
 ; Model interruption halfway through BEGIN/END, then recover before retry.
 mov es,[process_psp]
 les di,[es:0x34]
 mov bx,[fds]
 mov al,[saved_entry]
 mov [es:di+bx],al
 call far _process_handles_recover
 or ax,ax
 jnz failed
 mov ax,handle_count
 push ax
 mov ax,fds
 push ax
 call far _process_handles_begin
 add sp,4
 or ax,ax
 jnz failed
%endif
%endif
 mov ax,result
 push ax
 mov ax,tail
 push ax
 mov ax,child_name
 push ax
 call process_run
 add sp,6
 mov [exec_status],ax
%ifndef UNISOLATED
 call far _process_handles_end
 or ax,ax
 jnz failed
%endif
 mov ax,[result+6]
 cmp ax,[process_keep_paragraphs]
 jne failed
 mov ax,[process_psp]
 dec ax
 mov es,ax
 mov ax,[process_keep_paragraphs]
 cmp [es:3],ax
 jne failed
%ifdef MISSING_CHILD
 cmp word [exec_status],3
 jne failed
 cmp word [result+2],2
 jne failed
%else
 cmp word [exec_status],0
 jne failed
 cmp word [result+4],37
 jne failed
%endif
%ifndef UNISOLATED
 mov bx,[fds]
 call check_position
 mov dx,suffix
 call write_one
 mov ah,0x3e
 int 0x21
 jc failed
%ifdef TWO_HANDLES
 mov bx,[fds+2]
 call check_position
 mov dx,suffix
 call write_one
 mov ah,0x3e
 int 0x21
 jc failed
%endif
%endif
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
create:
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 cmp ax,9
 ja failed
%ifdef RECOVER_PARTIAL
 push es
 push di
 push bx
 mov bx,ax
 mov es,[process_psp]
 les di,[es:0x34]
 mov dl,[es:di+bx]
 mov [saved_entry],dl
 pop bx
 pop di
 pop es
%endif
 ret
write_one:
 mov cx,1
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,1
 jne failed
 ret
check_position:
 mov ax,0x4201
 xor cx,cx
 xor dx,dx
 int 0x21
 jc failed
 cmp ax,1
 jne failed
 or dx,dx
 jnz failed
 ret
SEGMENT _DATA public align=16 class=DATA use16
private_name: db 'PRIVATE.DAT',0
second_name: db 'SECOND.DAT',0
%ifdef MISSING_CHILD
child_name: db 'MISSING.COM',0
%else
child_name: db 'CHILD.COM',0
%endif
prefix: db 'A'
suffix: db 'B'
tail: db ' 0 -',0
fds: dw 0,0
saved_entry: db 0
exec_status: dw 0
result: times 4 dw 0
%ifdef TWO_HANDLES
handle_count equ 2
%else
handle_count equ 1
%endif
SEGMENT STACK stack align=16 class=STACK use16
 resb 8192
handles_probe_stack_top:
