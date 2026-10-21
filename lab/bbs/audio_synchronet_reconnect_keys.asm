; Test-only BIOS receive/loss/redial/retry keys; visible screen only.
bits 16
cpu 8086
org 100h
jmp install
%ifdef AUDIO_SYNC_DOWNLOAD_FAST
%define INITIAL_WAIT 4
%define KEY_WAIT 2
%define FINAL_WAIT 4
%else
%define INITIAL_WAIT 180
%define KEY_WAIT 3
%define FINAL_WAIT 180
%endif
%ifndef AUDIO_SYNC_DOWNLOAD_WATCHDOG
%define AUDIO_SYNC_DOWNLOAD_WATCHDOG 21600
%endif
old_vector:dd 0
attempt:db 0
state:db 0
ticks:dw 0
watchdog:dw AUDIO_SYNC_DOWNLOAD_WATCHDOG
key_at:dw filename_keys
carrier_lost:db 'RX carrier lost',0
connection_lost:db 'Carrier lost',0
hangup:db 'Hang up after transfer?',0
download:db 'Download: XMODEM',0
receiving:db 'Receiving XMODEM',0
pause_prompt:db '[Hit a key]',0
files:db 'List Files in dir',0
file_footer:db 'PCPlus Lab',0
main_prompt:db 'Read/Post Messages',0
main_footer:db 'Local [',0
filename_keys:dw 0x2044,0x273a,0x2b5c,0x1352,0x1245,0x2e43,0x2f56,0x2b5c,0x1f53,0x1559,0x314e,0x2e43,0x342e,0x3042,0x1749,0x314e,0x1c0d,0
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
 cmp byte [state],9
 je .done
 cmp byte [state],10
 je .redial
 dec word [watchdog]
 jnz .watching
 mov cx,2d00h
 call queue
 jc .restore
 inc word [watchdog]
 jmp .done
.watching:
 ; A redial can retain the first download prompt while the next script logs in.
 ; Require its disappearance before accepting a new transfer prompt.
 cmp byte [state],11
 jne .fresh_prompt
 mov si,hangup
 call visible
 jc .done
 mov byte [state],0
 jmp .done
.fresh_prompt:
 cmp byte [state],0
 jne .initial
 mov si,hangup
 call visible
 jnc .done
 mov byte [state],1
 mov word [ticks],INITIAL_WAIT
 jmp .done
.initial:
 cmp byte [state],1
 jne .filename_prompt
 dec word [ticks]
 jnz .done
 mov cx,1300h
 call queue
 jnc .retry
 mov byte [state],2
 jmp .done
.filename_prompt:
 cmp byte [state],2
 jne .filename
 mov si,download
 call visible
 jnc .done
 mov byte [state],3
 mov word [ticks],KEY_WAIT
 jmp .done
.filename:
 cmp byte [state],3
 jne .running
 dec word [ticks]
 jnz .done
 mov bx,[key_at]
 mov cx,[bx]
 call queue
 jnc .retry
 add word [key_at],2
 mov bx,[key_at]
 cmp word [bx],0
 je .filename_done
 mov word [ticks],KEY_WAIT
 jmp .done
.filename_done:
 mov byte [state],4
 jmp .done
.running:
 cmp byte [state],4
 jne .pause
 mov si,receiving
 call visible
 jnc .done
 mov byte [state],5
 jmp .done
.redial:
 dec word [ticks]
 jnz .done
 mov cx,2000h
 call queue
 jnc .retry
 mov byte [attempt],1
 mov byte [state],11
 mov word [key_at],filename_keys
 jmp .done
.pause:
 cmp byte [state],5
 jne .file_menu
 cmp byte [attempt],0
 jne .retry_completion
 mov si,carrier_lost
 call visible
 jc .lost
 mov si,connection_lost
 call visible
 jnc .done
.lost:
 mov byte [state],10
 mov word [ticks],INITIAL_WAIT
 jmp .done
.retry_completion:
 mov si,receiving
 call visible
 jc .done
 mov si,pause_prompt
 call visible
 jnc .done
 mov cx,3920h
 call queue
 jnc .done
 mov byte [state],6
 jmp .done
.file_menu:
 cmp byte [state],6
 jne .main_menu
 mov si,pause_prompt
 call visible
 jc .done
 mov si,files
 call visible
 jnc .done
 mov si,file_footer
 call visible
 jnc .done
 mov cx,1051h
 call queue
 jnc .done
 mov byte [state],7
 jmp .done
.main_menu:
 cmp byte [state],7
 jne .final
 mov si,main_prompt
 call visible
 jnc .done
 mov si,main_footer
 call visible
 jnc .done
 mov byte [state],8
 mov word [ticks],FINAL_WAIT
 jmp .done
.final:
 dec word [ticks]
 jnz .done
 mov cx,2d00h
 call queue
 jc .restore
.retry:
 mov word [ticks],1
 jmp .done
.restore:
 mov byte [state],9
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
queue:
 mov ah,5
 int 16h
 cmp al,1
 ; BIOS AL=0 is queued; CF=1 gives one uniform success convention.
 ret
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
 cmp al,[es:di]
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
