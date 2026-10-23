; Optional startup identity, before mouse/UART ownership. No DGROUP storage.
BITS 16
CPU 8086
%ifdef TERMINAL_SPECIAL_EDITION
SEGMENT SPLASH_CODE public class=CODE use16
global terminal_special_splash
terminal_special_splash:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 cld
 mov ax,3
 int 0x10
 mov ax,0x0600
 mov bh,0x5f
 xor cx,cx
 mov dx,0x184f
 int 0x10
 push cs
 pop ds
 mov si,title
 mov dx,0x071a
 call line
 mov si,edition
 mov dx,0x091b
 call line
 mov si,credit
 mov dx,0x0b1e
 call line
 mov si,prompt
 mov dx,0x101b
 call line
 xor ax,ax
 int 0x16
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf
line:
 xor bh,bh
 mov ah,2
 int 0x10
.next:
 lodsb
 or al,al
 jz .done
 mov ah,9
 mov bx,0x005f
 mov cx,1
 int 0x10
 inc dl
 mov ah,2
 int 0x10
 jmp .next
.done:
 ret
title: db 'P R O C O M M   P L U S',0
edition: db 'LoC SPECIAL EDITION',0
credit: db 'LoSs oF CoNtRoL',0
prompt: db 'Press any key to begin',0
%endif
