; Owned DOS observer: read actual BIOS text geometry after terminal shutdown.
; No mode/font/port changes, product memory access or input injection.
BITS 16
CPU 8086
ORG 100h
 mov ah,0x0f
 int 0x10
 mov [sample+4],ax
 mov [sample+6],bx
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 mov [sample],ax
 mov ax,[es:0x85]
 mov [sample+2],ax
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,sample
 mov cx,8
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,8
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
sample: times 8 db 0
filename: db 'D:\GEOM.BIN',0
