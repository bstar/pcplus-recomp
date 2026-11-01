; Test-only passive video observer for capture denial/open/close notices.
; No DOS/UART/keyboard calls or product-memory writes in the timer handler.
BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dd 0
sample: dw 0x434c,0,0,0,0,0,0
denied_frame: times 160 db 0
open_frame: times 160 db 0
closed_frame: times 160 db 0
denied: db 'Capture denied',0
opened: db 'Capture open',0
closed: db 'Capture closed',0
prompt: db 'Capture file [PCPLUS.LOG]',0
%macro observe 4
 test word [sample+2],%1
 jnz %%done
 mov si,%2
 call visible
 jnc %%done
 or word [sample+2],%1
 mov ax,[sample+4]
 mov [sample+%4],ax
 mov si,3840
 mov di,%3
 mov cx,160
%%copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop %%copy
%%done:
%endmacro
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
 inc word [sample+4]
 observe 1,denied,denied_frame,6
 observe 2,opened,open_frame,8
 observe 4,closed,closed_frame,10
 observe 8,prompt,denied_frame,12
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
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x434c
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,494
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[es:old_vector]
 mov ax,[es:old_vector+2]
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,494
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,494
 jne .close_failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
.close_failed:
 mov ah,3eh
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\PLCLAIM.BIN',0
buffer: times 494 db 0
