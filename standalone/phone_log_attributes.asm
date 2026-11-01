; Owned DOS attribute fixture. PRELOCK sets real read-only before startup;
; otherwise the first absolute-path query changes real attributes before append.
; All application queries return genuine DOS results. No product RAM patches.
BITS 16
CPU 8086
ORG 100h
%ifndef PRELOCK
%define PRELOCK 0
%endif
jmp start
old_dos: dd 0
sample: dw 0x414c,PRELOCK,0,0,0,0,0,0
%define QUERIES (sample+4)
%define FIRED (sample+6)
%define ORIGINAL (sample+8)
%define AFTER_SET (sample+10)
%define SET_ERROR (sample+12)
path: db 'D:\PCPLUS.FON',0
leaf: db 'PCPLUS.FON',0
relative_match: dw 0
handler:
 pushf
 push bp
 mov bp,sp
 cmp ax,4300h
 jne .pass
 call matches
 jnc .pass
 inc word [cs:QUERIES]
%if !PRELOCK
 cmp word [cs:relative_match],0
 jne .pass
 cmp word [cs:FIRED],0
 jne .pass
 push ax
 push cx
 push dx
 mov ax,4301h
 mov cx,[cs:ORIGINAL]
 or cx,1
 pushf
 call far [cs:old_dos]
 jc .set_error
 inc word [cs:FIRED]
 mov ax,4300h
 pushf
 call far [cs:old_dos]
 jc .set_error
 mov [cs:AFTER_SET],cx
 jmp .set_done
.set_error:
 mov [cs:SET_ERROR],ax
.set_done:
 pop dx
 pop cx
 pop ax
%endif
.pass:
 pop bp
 popf
 jmp far [cs:old_dos]
matches:
 push ax
 push bx
 push cx
 push si
 mov word [cs:relative_match],0
 mov si,dx
 add si,14
 jc .relative
 mov si,dx
 mov bx,path
 mov cx,14
.absolute_loop:
 mov al,[si]
 cmp al,[cs:bx]
 jne .relative
 inc si
 inc bx
 loop .absolute_loop
 jmp .found
.relative:
 mov si,dx
 add si,11
 jc .missing
 mov si,dx
 mov bx,leaf
 mov cx,11
.relative_loop:
 mov al,[si]
 cmp al,[cs:bx]
 jne .missing
 inc si
 inc bx
 loop .relative_loop
 mov word [cs:relative_match],1
.found:
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
 cmp byte [82h],'T'
 jne collect
 mov dx,path
 mov ax,4300h
 int 21h
 jc failed
 mov [ORIGINAL],cx
 mov [AFTER_SET],cx
%if PRELOCK
 or cx,1
 mov ax,4301h
 int 21h
 jc failed
 mov ax,4300h
 int 21h
 jc failed
 test cx,1
 jz failed
 mov [AFTER_SET],cx
 mov word [FIRED],1
%endif
 mov ax,3521h
 int 21h
 mov [old_dos],bx
 mov [old_dos+2],es
 mov dx,handler
 mov ax,2521h
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 mov ax,3521h
 int 21h
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x414c
 jne failed
 mov si,sample
 mov di,buffer
 mov cx,16
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
 mov dx,path
 mov ax,4300h
 int 21h
 jc failed
 mov [buffer+14],cx
 mov cx,[buffer+8]
 mov ax,4301h
 int 21h
 jc failed
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,16
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,16
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
filename: db 'D:\ATTR.BIN',0
buffer: times 16 db 0
