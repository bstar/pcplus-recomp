; Owned DOSBox fixture only. Track D:\PCPLUS.FON, perform its first real DOS
; close, then return error6/CF1 to model an uncertain close. Never patch product
; variables or executable bytes. Install before the separate passive observer.
BITS 16
CPU 8086
ORG 100h
jmp start
old_dos: dd 0
sample: dw 0x4346,0,0,0,0,0xffff
%define FIRED (sample+2)
%define CLOSE_CALLS (sample+4)
%define REAL_AX (sample+6)
%define REAL_FLAGS (sample+8)
%define HELD (sample+10)
path: db 'D:\PCPLUS.FON',0
handler:
 pushf
 push bp
 mov bp,sp
 cmp word [cs:FIRED],0
 jne .pass
 cmp ah,3eh
 je .close
 cmp ah,3ch
 je .open
 cmp ah,3dh
 je .open
 cmp ah,5bh
 jne .pass
.open:
 call matches
 jnc .pass
 pushf
 call far [cs:old_dos]
 jc .open_error
 mov [cs:HELD],ax
 and word [ss:bp+8],0xfffe
 jmp .return
.open_error:
 or word [ss:bp+8],1
 jmp .return
.close:
 cmp bx,[cs:HELD]
 jne .pass
 inc word [cs:CLOSE_CALLS]
 pushf
 call far [cs:old_dos]
 mov [cs:REAL_AX],ax
 pushf
 pop word [cs:REAL_FLAGS]
 mov word [cs:FIRED],1
 mov ax,6
 or word [ss:bp+8],1
.return:
 pop bp
 popf
 iret
.pass:
 pop bp
 popf
 jmp far [cs:old_dos]
matches:
 push ax
 push bx
 push cx
 push si
 mov si,dx
 add si,14
 jc .missing
 mov si,dx
 mov bx,path
 mov cx,14
.loop:
 mov al,[si]
 cmp al,[cs:bx]
 jne .missing
 inc si
 inc bx
 loop .loop
 pop si
 pop cx
 pop bx
 pop ax
 stc
 ret
.missing:
 pop si
 pop cx
 pop bx
 pop ax
 clc
 ret
resident_end:
start:
 mov ax,3521h
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_dos],bx
 mov [old_dos+2],es
 mov dx,handler
 mov ax,2521h
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4346
 jne failed
 mov si,sample
 mov di,buffer
 mov cx,12
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,[es:old_dos]
 mov ax,[es:old_dos+2]
 mov [old_dos],dx
 mov [old_dos+2],ax
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 mov ax,3521h
 int 21h
 cmp bx,[old_dos]
 jne failed
 mov ax,es
 cmp ax,[old_dos+2]
 jne failed
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,12
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,12
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
filename: db 'D:\CLOSE.BIN',0
buffer: times 12 db 0
