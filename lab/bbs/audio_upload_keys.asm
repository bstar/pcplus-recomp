; Test-only upload BIOS keys. Observe visible text/cursor; no product state,
; DOS calls in the timer, UART reads, protocol replies or fabricated pass files.
bits 16
cpu 8086
org 100h
jmp install
%ifdef AUDIO_UPLOAD_FAST_TEST
%define LOCAL_WAIT 2
%define FIELD_WAIT 2
%define REMOTE_WAIT 2
%define FINAL_WAIT 3
%else
%define LOCAL_WAIT 4
%define FIELD_WAIT 36
%define REMOTE_WAIT 54
%define FINAL_WAIT 360
%endif
%macro keys 5
 mov byte [state],%1
 mov word [key_at],%2
 mov byte [next_state],%3
 mov word [key_delay],%4
 mov word [ticks],%5
 jmp .done
%endmacro
old_vector: dd 0
state: db 0
next_state: db 0
key_result: db 0
watchdog: dw 21240
ticks: dw 0
cooldown: dw 0
stable: dw 0
previous_cursor: dw 0ffffh
pause_count: db 0
key_delay: dw 0
key_at: dw 0
banner: db 'No socket descriptor specified',0
local_prompt: db 'Upload: XMODEM/1K',0
sending: db 'Sending ZMODEM',0
checker: db 'UPLOAD CHECKER',0
pause_text: db 'smash your keyboard',0
details: db 'UPLOAD DETAILS - ',0
filename_marker: db 'AUDIOUP.BIN',0
button: db 'CONTINUE',0
file_menu: db 'File Base',0
menu_footer: db '...cmd:',0
search_title: db 'FILE SEARCH',0
search_footer: db 'ESC : cancel',0
list_title: db 'QUEUED',0
failure_timeout: db 'TX timeout',0
failure_cancel: db 'TX canceled',0
start_keys: dw 1f00h,0
file_keys: dw 3c00h,3c00h,2044h,273ah,2b5ch,1f53h,1245h,314eh,2044h,2b5ch,1e41h,1655h,2044h,1749h,184fh,1655h,1950h,342eh,3042h,1749h,314eh,1c0dh,0
enter_keys: dw 1c0dh,0
search_keys: dw 1f53h,1c0dh,0
query_keys: dw 1e41h,1655h,2044h,1749h,184fh,1655h,1950h,342eh,3042h,1749h,314eh,1c0dh,1c0dh,0
exit_keys: dw 2d00h,0
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
 cmp byte [state],14
 je .done
 dec word [watchdog]
 jnz .watch
 mov cx,2d00h
 call inject
 jz .restore
 inc word [watchdog]
 jmp .done
.watch:
 cmp word [cooldown],0
 je .dispatch
 dec word [cooldown]
 jmp .done
.dispatch:
 mov al,[state]
 cmp al,1
 je .emit
 cmp al,3
 je .emit
 cmp al,6
 je .emit
 cmp al,9
 je .emit
 cmp al,11
 je .emit
 cmp al,13
 je .emit
 cmp al,0
 jne .local
 mov si,banner
 call visible
 jnc .done
 keys 1,start_keys,2,LOCAL_WAIT,FIELD_WAIT
.local:
 cmp al,2
 jne .transfer
 mov si,local_prompt
 call visible
 jnc .done
 keys 3,file_keys,4,LOCAL_WAIT,LOCAL_WAIT
.transfer:
 cmp al,4
 jne .checker
 mov si,sending
 call visible
 jnc .done
 mov byte [state],5
 jmp .done
.checker:
 cmp al,5
 jne .details
 mov si,failure_timeout
 call visible
 jc .failed
 mov si,failure_cancel
 call visible
 jc .failed
 mov si,sending
 call visible
 jc .done
 mov si,checker
 call visible
 jnc .done
 mov si,pause_text
 call visible
 jnc .done
 keys 6,enter_keys,7,REMOTE_WAIT,FIELD_WAIT
.details:
 cmp al,7
 jne .menu
 mov si,details
 call visible
 jnc .reset
 mov si,filename_marker
 call visible
 jnc .reset
 mov si,button
 call visible
 jnc .reset
 mov ah,3
 xor bh,bh
 int 10h
 cmp dl,5
 jb .reset
 cmp dl,75
 ja .reset
 cmp dh,5
 je .focus
 cmp dl,51
 jb .reset
 cmp dl,70
 ja .reset
 cmp dh,8
 je .focus
 cmp dh,13
 jne .reset
.focus:
 cmp [previous_cursor],dx
 jne .changed
 inc word [stable]
 cmp word [stable],FIELD_WAIT
 jb .done
 mov cx,0f09h
 cmp dh,13
 jne .insert_field
 mov cx,1c0dh
.insert_field:
 call inject
 jnz .done
 mov word [stable],0
 mov word [cooldown],FIELD_WAIT
 cmp cx,1c0dh
 jne .done
 mov byte [state],8
 jmp .done
.changed:
 mov [previous_cursor],dx
.reset:
 mov word [stable],0
 jmp .done
.menu:
 cmp al,8
 jne .search
 mov si,file_menu
 call visible
 jnc .pause
 mov si,menu_footer
 call visible
 jnc .pause
 keys 9,search_keys,10,REMOTE_WAIT,FIELD_WAIT
.pause:
 cmp byte [pause_count],2
 jae .done
 mov si,pause_text
 call visible
 jnc .done
 mov cx,1c0dh
 call inject
 jnz .done
 inc byte [pause_count]
 mov word [cooldown],FIELD_WAIT
 jmp .done
.search:
 cmp al,10
 jne .list
 mov si,search_title
 call visible
 jnc .done
 mov si,search_footer
 call visible
 jnc .done
 keys 11,query_keys,12,REMOTE_WAIT,FIELD_WAIT
.list:
 cmp al,12
 jne .done
 mov si,list_title
 call visible
 jnc .done
 mov si,filename_marker
 call visible
 jnc .done
 keys 13,exit_keys,14,LOCAL_WAIT,FINAL_WAIT
.failed:
 keys 13,exit_keys,14,LOCAL_WAIT,FIELD_WAIT
.emit:
 dec word [ticks]
 jnz .done
 mov bx,[key_at]
 mov cx,[bx]
 call inject
 jnz .retry
 add word [key_at],2
 mov bx,[key_at]
 cmp word [bx],0
 je .phase_done
 mov ax,[key_delay]
 mov [ticks],ax
 jmp .done
.retry:
 inc word [ticks]
 jmp .done
.phase_done:
 mov al,[next_state]
 mov [state],al
 cmp al,14
 jne .done
.restore:
 mov byte [state],14
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
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 mov ah,5
 int 16h
 mov [cs:key_result],al
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 cmp byte [cs:key_result],0
 ret
; Fold ASCII text only. Visible CP437 cell matching never reads application data.
visible:
 push si
 mov ax,0b800h
 mov es,ax
 xor di,di
.search:
 pop si
 push si
 push di
.match:
 lodsb
 or al,al
 jz .found
 cmp di,4000
 jae .miss
 or al,20h
 mov ah,[es:di]
 or ah,20h
 cmp al,ah
 jne .miss
 add di,2
 jmp .match
.miss:
 pop di
 add di,2
 cmp di,4000
 jb .search
 pop si
 clc
 ret
.found:
 pop di
 pop si
 stc
 ret
resident_end:
filename: db 'D:\KEYOLD.BIN',0
install:
 mov ax,351ch
 int 21h
 mov [old_vector],bx
 mov [old_vector+2],es
 mov ah,3ch
 xor cx,cx
 mov dx,filename
 int 21h
 jc failure
 mov bx,ax
 mov ah,40h
 mov cx,4
 mov dx,old_vector
 int 21h
 pushf
 push ax
 mov ah,3eh
 int 21h
 pop ax
 popf
 jc failure
 cmp ax,4
 jne failure
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
failure:
 mov ax,4c01h
 int 21h
