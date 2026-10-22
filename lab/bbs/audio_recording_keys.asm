; Test-only screen-gated BIOS keys for normal Record -> ASP compile/replay.
; Private state only; never calls DOS or writes product/serial state in INT1C.
bits 16
cpu 8086
org 100h
jmp install
%ifndef RECORD_KEY_TICKS
%define RECORD_KEY_TICKS 3
%endif
%ifndef RECORD_DWELL_TICKS
%define RECORD_DWELL_TICKS 18
%endif
%ifndef RECORD_INITIAL_TICKS
%define RECORD_INITIAL_TICKS 90
%endif
%ifndef RECORD_WATCHDOG_TICKS
%define RECORD_WATCHDOG_TICKS 32000
%endif
old_vector: dd 0
report:
 dw 524bh
phase: dw 0
delivered: dw 0
reason: dw 0 ;0 pending,1 full recipe,2 watchdog
elapsed: dw 0
retries: dw 0
 dw 0,0
state: db 0 ;0 marker,1 dwell,2 keys,3 retired
ticks: dw 0
key_at: dw 0
watchdog: dw RECORD_WATCHDOG_TICKS
ready_marker: db 'RECORDER READY',0
file_marker: db 'File Base >> active filter:',0
menu_marker: db 'PCPLUS  Command Menu',0
path_marker: db 'Recording file: DOS 8.3 path',0
saved_marker: db 'Recording saved.',0
script_marker: db 'Script DOS 8.3 path:',0
search_marker: db 'ESC : cancel',0
replay_marker: db 'FILE SEARCH',0
open_menu: dw 2c00h,0
record_key: dw 2e43h,0
enter_key: dw 1c0dh,0
search_keys: dw 1f53h,1c0dh,0
escape_key: dw 011bh,0
close_keys: dw 011bh,011bh,0
script_key: dw 1e41h,0
script_path: dw 1970h,2e63h,1970h,266ch,1675h,1f73h,342eh,1e61h,1f73h,1970h,1c0dh,0
no_keys: dw 0
exit_keys: dw 2d00h,0
; marker, BIOS sequence, dwell. Stage11 observes the replay's Search page
; before stage12 accepts File Base; stale pre-script text cannot finish it.
stages:
 dw ready_marker,open_menu,RECORD_INITIAL_TICKS
 dw menu_marker,record_key,RECORD_DWELL_TICKS
 dw path_marker,enter_key,RECORD_DWELL_TICKS
 dw file_marker,search_keys,RECORD_DWELL_TICKS
 dw search_marker,escape_key,RECORD_DWELL_TICKS
 dw file_marker,open_menu,RECORD_DWELL_TICKS
 dw menu_marker,record_key,RECORD_DWELL_TICKS
 dw saved_marker,close_keys,RECORD_DWELL_TICKS
 dw file_marker,open_menu,RECORD_DWELL_TICKS
 dw menu_marker,script_key,RECORD_DWELL_TICKS
 dw script_marker,script_path,RECORD_DWELL_TICKS
 dw replay_marker,no_keys,1
 dw file_marker,search_keys,RECORD_DWELL_TICKS
 dw search_marker,exit_keys,RECORD_DWELL_TICKS
STAGE_COUNT equ ($-stages)/6
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
 cld
 cmp byte [state],3
 je .done
 inc word [elapsed]
 dec word [watchdog]
 jnz .watch
 mov cx,2d00h
 call inject
 jnz .retry_watchdog
 mov word [reason],2
 jmp .retire
.retry_watchdog:
 inc word [watchdog]
 jmp .done
.watch:
 mov bx,[phase]
 shl bx,1
 mov ax,bx
 shl bx,1
 add bx,ax ;phase*6
 cmp byte [state],2
 je .keys
 mov si,[stages+bx]
 call scan
 jnz .not_ready
 cmp byte [state],0
 jne .dwell
 mov ax,[stages+bx+4]
 mov [ticks],ax
 mov byte [state],1
 jmp .done
.not_ready:
 mov byte [state],0
 jmp .done
.dwell:
 dec word [ticks]
 jnz .done
 mov ax,[stages+bx+2]
 mov [key_at],ax
 mov byte [state],2
 mov word [ticks],1
 jmp .done
.keys:
 dec word [ticks]
 jnz .done
 mov si,[key_at]
 mov cx,[si]
 or cx,cx
 jz .next
 call inject
 jnz .queue_full
 inc word [delivered]
 add word [key_at],2
 mov si,[key_at]
 cmp word [si],0
 je .next
 mov word [ticks],RECORD_KEY_TICKS
 jmp .done
.queue_full:
 mov word [ticks],1
 jmp .done
.next:
 inc word [phase]
 cmp word [phase],STAGE_COUNT
 je .complete
 mov byte [state],0
 jmp .done
.complete:
 mov word [reason],1
.retire:
 mov byte [state],3
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov ax,[old_vector]
 mov [es:70h],ax
 mov ax,[old_vector+2]
 mov [es:72h],ax
 popf
.done:
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
inject:
 mov ah,5
 int 16h
 or al,al
 jz .ok
 inc word [retries]
.ok:
 or al,al
 ret
; ZF set only on a complete visible contiguous character match.
scan:
 push ax
 push si
 push di
 mov ax,0b800h
 mov es,ax
 xor di,di
.search:
 push si
 push di
.match:
 lodsb
 or al,al
 jz .found
 cmp di,4000
 jae .miss
 cmp al,[es:di]
 jne .miss
 add di,2
 jmp .match
.miss:
 pop di
 pop si
 add di,2
 cmp di,4000
 jb .search
 mov ax,1
 or ax,ax
 jmp .out
.found:
 pop di
 pop si
 xor ax,ax
.out:
 pop di
 pop si
 pop ax
 ret
resident_end:
pointer: dw 0
buffer: times 16 db 0
pointer_name: db 'D:\RECKEY.PTR',0
report_name: db 'D:\RECKEY.BIN',0
old_name: db 'D:\KEYOLD.BIN',0
install:
 cmp byte [82h],'R'
 je collect
 mov ax,351ch
 int 21h
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,old_name
 mov si,old_vector
 mov cx,4
 call write_file
 jc failure
 mov ax,cs
 mov [pointer],ax
 mov dx,pointer_name
 mov si,pointer
 mov cx,2
 call write_file
 jc failure
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 mov dx,pointer_name
 mov ax,3d00h
 int 21h
 jc failure
 mov bx,ax
 mov dx,pointer
 mov cx,2
 mov ah,3fh
 int 21h
 pushf
 push ax
 mov ah,3eh
 int 21h
 pop ax
 popf
 jc failure
 cmp ax,2
 jne failure
 mov es,[pointer]
 cmp word [es:report],524bh
 jne failure
 mov si,report
 mov di,buffer
 mov cx,16
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,report_name
 mov si,buffer
 mov cx,16
 call write_file
 jc failure
 mov ax,4c00h
 int 21h
write_file:
 push cx
 push si
 xor cx,cx
 mov ah,3ch
 int 21h
 pop dx
 pop cx
 jc .out
 mov bx,ax
 mov ah,40h
 int 21h
 pushf
 push ax
 mov ah,3eh
 int 21h
 pop ax
 popf
 jc .out
 cmp ax,cx
 jne .short
 clc
.out: ret
.short:
 stc
 ret
failure:
 mov ax,4c01h
 int 21h
