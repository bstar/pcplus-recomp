; Raw startup editor substitute: independently observe the exposed caller traps.
BITS 16
CPU 8086
ORG 100h
start:
 push cs
 pop ds
 mov bx,[0x16]
 mov [record+2],bx
 mov ax,bx
 add ax,0x10+PARENT_DGROUP
 mov es,ax
 mov ax,[es:PARENT_PHASE]
 mov [record+4],ax
 xor di,di
 cmp ax,2
 je .owner
 inc di
.owner:
 cmp [es:PARENT_OWNER],bx
 je .vectors
 inc di
.vectors:
 mov si,0
 mov bx,PARENT_ORIGINALS
 mov bp,record+8
.vector:
 push es
 xor ax,ax
 mov es,ax
 mov dx,[cs:indices+si]
 push bx
 mov bx,dx
 mov ax,[es:bx]
 mov dx,[es:bx+2]
 pop bx
 pop es
 mov [ds:bp],ax
 mov [ds:bp+2],dx
 cmp ax,[es:bx]
 jne .different
 cmp dx,[es:bx+2]
 je .next
.different:
 inc di
.next:
 add bp,4
 add bx,4
 add si,2
 cmp si,6
 jb .vector
 mov ax,0x3300
 int 0x21
 xor dh,dh
 mov [record+20],dx
 cmp dx,[es:PARENT_FLAG]
 je .write
 inc di
.write:
 mov [record+6],di
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,record
 mov cx,22
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,22
 jne failed
 mov ah,0x3e
 int 0x21
 ; Leave changed vectors in both the IVT and the child's own PSP so DOS
 ; termination really exposes them to the waiting parent's resume boundary.
 mov dx,child_handler
 mov ax,0x251b
 int 0x21
 mov ax,0x2523
 int 0x21
 mov ax,0x2524
 int 0x21
 mov word [0x0e],child_handler
 mov word [0x10],cs
 mov word [0x12],child_handler
 mov word [0x14],cs
 mov ax,0x3301
 mov dx,[record+20]
 xor dl,1
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c63
 int 0x21
child_handler: iret
indices: dw 0x1b*4,0x23*4,0x24*4
record: dw 0x4354,0,0,0
 times 7 dw 0
filename: db 'CHILTRAP.BIN',0
