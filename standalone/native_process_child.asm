BITS 16
CPU 8086
ORG 0x100
%ifdef CHILD_DIVIDE
 mov ax,0x1234
 mov ds,ax
 xor bx,bx
 div bx
 mov ax,0x4c63
 int 0x21
%elifdef CHILD_VECTORS
 mov dx,handler
 mov ax,0x2500
 int 0x21
 mov ax,0x2523
 int 0x21
 mov ax,0x2524
 int 0x21
 mov ax,0x4c2a
 int 0x21
handler: iret
%elifdef CHILD_TSR
 mov dx,0x20
 mov ax,0x3107
 int 0x21
%elifdef CHILD_FLAGS
 mov ax,0x4c33
 std
 stc
 int 0x21
%elifdef CHILD_EXIT
 mov ax,0x4c00+CHILD_EXIT
 int 0x21
%else
 push ds
 pop es
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc fail
 mov bx,ax
 xor cx,cx
 mov cl,[0x80]
 add cx,2
 mov dx,0x80
 mov ah,0x40
 int 0x21
 jc fail
 mov ah,0x3e
 int 0x21
 ; Verify an explicitly owned environment survives actual DOS4B00.
 mov ax,[0x2c]
 mov es,ax
%ifdef CHILD_EMPTY
 cmp word [es:0],0
 jne fail
%else
 xor di,di
 mov cx,13
 mov si,expected
 repe cmpsb
 jne fail
%endif
 mov ax,0x4c25
 int 0x21
fail:
 mov ax,0x4c63
 int 0x21
name: db 'CHILD.OUT',0
expected: db 'LABVAR=OWNED',0
%endif
