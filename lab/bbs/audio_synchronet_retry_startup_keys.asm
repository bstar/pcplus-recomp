; BIOS-only same-call cancel/retry observer; no product state or UART access.
bits 16
cpu 8086
org 100h
jmp install
%ifdef AUDIO_SYNC_RETRY_FAST
%define INITIAL_WAIT 2
%define KEY_WAIT 1
%define SETTLE_WAIT 1
%define FINAL_WAIT 2
%else
%define INITIAL_WAIT 180
%define KEY_WAIT 3
%define SETTLE_WAIT 36
%define FINAL_WAIT 180
%endif
%ifndef AUDIO_SYNC_RETRY_WATCHDOG
%define AUDIO_SYNC_RETRY_WATCHDOG 21600
%endif
old_vector:dd 0
phase:dw 0
mode:db 0
retired:db 0
ticks:dw 0
key_at:dw 0
watchdog:dw AUDIO_SYNC_RETRY_WATCHDOG
m_hangup:db 'Hang up after transfer?',0
m_local:db 'Upload: XMODEM/1K',0
m_sending:db 'Sending XMODEM/1K',0
m_canceled:db 'TX canceled',0
m_pause:db '[Hit a key]',0
m_files:db 'List Files in dir',0
m_file_footer:db 'PCPlus Lab',0
m_filename:db 'Filename:',0
m_confirm:db 'to Main PCPlus Lab?',0
m_retry_name:db 'SXRUP003.BIN',0
m_description:db 'Enter a description now.',0
m_protocol:db 'Protocol, ',0
m_crc:db 'XMODEM-1K/CRC',0
m_main:db 'Read/Post Messages',0
m_main_footer:db 'Local [',0
k_alt_s:dw 0x1f00,0x0
k_source:dw 0x2044,0x273a,0x2b5c,0x1f53,0x1245,0x314e,0x2044,0x2b5c,0x1352,0x1245,0x1454,0x1352,0x1559,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x0
k_escape:dw 0x11b,0x0
k_none:dw 0x0
k_space:dw 0x3920,0x0
k_upload:dw 0x1655,0x0
k_name:dw 0x1f53,0x2d58,0x1352,0x1655,0x1950,0xb30,0xb30,0x433,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x0
k_yes:dw 0x1579,0x0
k_description:dw 0x1f53,0x1579,0x316e,0x1474,0x2368,0x1265,0x1474,0x1769,0x2e63,0x3920,0x1950,0x2e43,0x1950,0x266c,0x1675,0x1f73,0x3920,0x1e61,0x1675,0x2064,0x1769,0x186f,0x3920,0x1372,0x1265,0x1474,0x1372,0x1579,0x1c0d,0x0
k_protocol:dw 0x231,0x0
k_start:dw 0x316e,0x1f00,0x0
k_quit:dw 0x1051,0x0
k_exit:dw 0x2d00,0x0
steps:
dw m_hangup,0,0,k_alt_s,INITIAL_WAIT,0
dw m_local,0,0,k_source,SETTLE_WAIT,0
dw m_sending,0,0,k_escape,1,1
dw m_canceled,0,0,k_none,1,0
dw m_pause,0,m_sending,k_space,SETTLE_WAIT,0
dw m_files,m_file_footer,m_pause,k_upload,SETTLE_WAIT,0
dw m_filename,0,0,k_name,SETTLE_WAIT,0
dw m_confirm,m_retry_name,0,k_yes,SETTLE_WAIT,0
dw m_description,0,0,k_description,SETTLE_WAIT,0
dw m_protocol,m_crc,0,k_protocol,SETTLE_WAIT,0
dw m_hangup,0,0,k_start,SETTLE_WAIT,0
dw m_local,0,0,k_source,SETTLE_WAIT,0
dw m_sending,0,0,k_none,1,0
dw m_pause,0,m_sending,k_space,SETTLE_WAIT,0
dw m_files,m_file_footer,m_pause,k_quit,SETTLE_WAIT,0
dw m_main,m_main_footer,0,k_exit,FINAL_WAIT,0
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
 cmp byte [retired],1
 je .done
 dec word [watchdog]
 jnz .normal
 mov cx,2d00h
 call queue
 jc .restore
 inc word [watchdog]
 jmp .done
.normal:
 cmp byte [mode],1
 je .count
 mov bx,[phase]
 mov ax,bx
 shl bx,1
 add bx,ax
 shl bx,1
 shl bx,1
 add bx,steps
 mov si,[bx]
 call visible
 jnc .done
 mov si,[bx+2]
 or si,si
 jz .forbid
 call visible
 jnc .done
.forbid:
 mov si,[bx+4]
 or si,si
 jz .progress
 call visible
 jc .done
.progress:
 cmp word [bx+10],0
 je .start
 cmp word [es:3680+70*2],1f31h
 jb .done
 cmp word [es:3680+70*2],1f39h
 ja .done
.start:
 mov ax,[bx+6]
 mov [key_at],ax
 mov ax,[bx+8]
 mov [ticks],ax
 mov byte [mode],1
 jmp .done
.count:
 dec word [ticks]
 jnz .done
 mov bx,[key_at]
 mov cx,[bx]
 jcxz .advance
 call queue
 jnc .retry
 add word [key_at],2
 mov bx,[key_at]
 cmp word [bx],0
 je .advance
 mov word [ticks],KEY_WAIT
 jmp .done
.advance:
 cmp word [phase],15
 je .restore
 inc word [phase]
 mov byte [mode],0
 jmp .done
.retry:
 mov word [ticks],1
 jmp .done
.restore:
 mov byte [retired],1
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
