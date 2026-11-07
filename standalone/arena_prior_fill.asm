; Owned DOSBox fixture: fill only this process's MCB allocation, then exit.
; No product exists while this runs. Leave the first4KiB (code/stack) intact.
BITS 16
CPU 8086
ORG 100h
start:
 cmp byte [82h],'T'
 jne done
 mov ax,cs
 cli
 mov ss,ax
 mov sp,0ff0h
 sti
 cld
 mov bx,ax
 dec ax
 mov es,ax
 cmp word [es:1],bx
 jne bad
 mov dx,[es:3]
 add dx,bx
 jc bad
 cmp dx,0a000h
 ja bad
 add bx,100h
 jc bad
 cmp bx,dx
 jae bad
.fill:
 mov es,bx
 xor di,di
 mov cx,4
.words:
 mov ax,4d45h ; EM
 stosw
 mov ax,4f50h ; PO
 stosw
 loop .words
 inc bx
 cmp bx,dx
 jb .fill
done:
 mov ax,4c00h
 int 21h
bad:
 mov ax,4c01h
 int 21h
