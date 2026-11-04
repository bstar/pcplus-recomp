; Passive timer observer: two actual video snapshots one second apart in Pause.
; No product memory, input injection or serial replies.
BITS 16
CPU 8086
ORG 0x100
%ifndef PAUSE_ROWS
%define PAUSE_ROWS 25
%endif
%if PAUSE_ROWS != 25 && PAUSE_ROWS != 28 && PAUSE_ROWS != 43 && PAUSE_ROWS != 50
%error Unsupported owned pause observation height
%endif
%define PAUSE_BYTES (PAUSE_ROWS*160)
jmp start
old_vector: dw 0,0
observed: dw 0
pause_ticks: dw 0
message: db 'Screen paused.  Press any key to continue...'
screen: times PAUSE_BYTES db 0
later: times PAUSE_BYTES db 0
handler:
 pushf
 push ax
 push cx
 push si
 push di
 push ds
 push es
 cmp word [cs:observed],3
 je .done
 mov ax,0xb800
 mov es,ax
 mov di,(PAUSE_ROWS-1)*160+18*2
 mov si,message
 mov cx,44
.match:
 mov al,[cs:si]
 cmp al,[es:di]
 jne .done
 inc si
 add di,2
 loop .match
 cmp word [cs:observed],0
 jne .second
 mov di,screen
 mov word [cs:observed],1
 jmp .copy
.second:
 inc word [cs:pause_ticks]
 cmp word [cs:pause_ticks],18
 jb .done
 mov di,later
 mov word [cs:observed],3
.copy:
 cld
 mov ax,0xb800
 mov ds,ax
 push cs
 pop es
 xor si,si
 mov cx,PAUSE_BYTES/2
 rep movsw
.done:
 pop es
 pop ds
 pop di
 pop si
 pop cx
 pop ax
 popf
 jmp far [cs:old_vector]
resident_end:
start:
 mov ax,0x351c
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:observed],3
 jne failed
 mov ax,[es:old_vector+2]
 mov dx,[es:old_vector]
 push ds
 mov ds,ax
 mov ax,0x251c
 int 0x21
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 push ds
 push es
 pop ds
 mov dx,screen
 mov cx,PAUSE_BYTES*2
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,PAUSE_BYTES*2
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\PAUSE.BIN',0
