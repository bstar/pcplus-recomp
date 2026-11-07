; Owned emulator fault injector: match only one module and its opening PSP.
; No writes to product memory/code; log every matching explicit close attempt.
BITS 16
CPU 8086
ORG 100h
jmp start
old_dos: dd 0
sample: dw 0x4346,0,0,0,0,0xffff,0,0,0,0,0
%define FIRED (sample+2)
%define CLOSE_CALLS (sample+4)
%define REAL_AX (sample+6)
%define REAL_FLAGS (sample+8)
%define HELD (sample+10)
%define OWNER_PSP (sample+12)
%define OPEN_CALLS (sample+14)
%define RESTORED (sample+16)
%define CLOSE_SITE_CS (sample+18)
%define TOTAL_CLOSES (sample+20)
%ifdef MODULE_LINE
path: db 'C:\PCLINE.OVL',0
%else
path: db 'C:\PCMETA.OVL',0
%endif
handler:
 pushf
 push bp
 mov bp,sp
 cmp ah,3eh
 je .close
 cmp word [cs:FIRED],0
 jne .pass
 cmp ah,3ch
 je .open
 cmp ah,3dh
 je .open
 cmp ah,5bh
 jne .pass
.open:
 call matches
 jnc .pass
 push ax
 push bx
 mov ah,51h
 pushf
 call far [cs:old_dos]
 mov [cs:OWNER_PSP],bx
 pop bx
 pop ax
 inc word [cs:OPEN_CALLS]
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
 push ax
 push bx
 mov ah,51h
 pushf
 call far [cs:old_dos]
 cmp bx,[cs:OWNER_PSP]
 pop bx
 pop ax
 jne .pass
 inc word [cs:TOTAL_CLOSES]
 push ax
 mov ax,[ss:bp+6]
 cmp word [cs:CLOSE_SITE_CS],0
 jne .site_known
 mov [cs:CLOSE_SITE_CS],ax
.site_known:
 cmp ax,[cs:CLOSE_SITE_CS]
 pop ax
 jne .pass
 inc word [cs:CLOSE_CALLS]
 cmp word [cs:FIRED],0
 jne .pass
%ifdef CLOSE_BEFORE
 mov word [cs:REAL_AX],0xffff
 mov word [cs:REAL_FLAGS],0xffff
%else
 pushf
 call far [cs:old_dos]
 mov [cs:REAL_AX],ax
 pushf
 pop word [cs:REAL_FLAGS]
%endif
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
 mov cx,22
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
 mov word [buffer+16],1
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,22
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,22
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
buffer: times 22 db 0
