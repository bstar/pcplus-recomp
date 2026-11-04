; Owned observation-only DOS child: record actual BIOS/BDA text geometry.
BITS 16
CPU 8086
ORG 100h
 push cs
 pop ds
 mov ah,0x0f
 int 0x10
 xor cx,cx
 mov cl,al
 mov [sample],cx
 mov cl,ah
 mov [sample+2],cx
 mov cl,bh
 mov [sample+8],cx
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 mov [sample+4],ax
 mov ax,[es:0x85]
 mov [sample+6],ax
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,sample
 mov cx,10
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,10
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c63
 int 0x21
sample: times 5 dw 0
filename: db 'GEOM.BIN',0
