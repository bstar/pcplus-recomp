; Owned nested DOS child. No parent callbacks or renderer substitutes.
BITS 16
CPU 8086
ORG 100h
start:
 mov ax,cs
 mov ds,ax
 mov si,0x81
.space:
 lodsb
 cmp al,' '
 je .space
 mov [kind],al
 ; Every nonstandard inherited descriptor must be absent from the child's JFT.
 mov bx,5
.private:
 mov ax,0x4201
 xor cx,cx
 xor dx,dx
 int 0x21
 jnc .bad
 cmp ax,6
 jne .bad
 inc bx
 cmp bx,20
 jb .private
%ifdef REQUIRE_OUTPUT
 mov dx,outname
 mov ax,0x3d00
 int 0x21
 jc .bad
 mov bx,ax
 mov dx,pending
 mov cx,8
 mov ah,0x3f
 int 0x21
 jc .bad
 cmp ax,8
 jne .bad
 mov ah,0x3e
 int 0x21
 jc .bad
 mov si,pending
 mov di,expected
 mov cx,8
 repe cmpsb
 jne .bad
%endif
 mov dx,logname
 mov ax,0x3d01
 int 0x21
 jc .bad
 mov bx,ax
 mov ax,0x4202
 xor cx,cx
 xor dx,dx
 int 0x21
 jc .bad
 mov dx,kind
 mov cx,1
 mov ah,0x40
 int 0x21
 jc .bad
 cmp ax,1
 jne .bad
 mov ah,0x3e
 int 0x21
 jc .bad
 cmp byte [kind],'G'
 jne .text
 mov ax,0x13
 int 0x10
 jmp .mutate
.text:
 mov ax,0xb800
 mov es,ax
 mov word [es:20*160],0x4f43 ; visible C at row21 for NOCLEAR
 cmp byte [kind],'W'
 jne .mutate
 mov ah,5
 mov cx,0x2c5a ; actual BIOS keyboard Z consumed by native WAIT
 int 0x16
 cmp al,0
 jne .bad
.mutate:
%ifdef MUTATE_DOS_VECTORS
 mov dx,isr
 mov ax,0x2523
 int 0x21
 mov ax,0x2524
 int 0x21
 ; Force DOS to return the altered vectors from this child's own PSP too.
 mov word [0x0e],isr
 mov word [0x10],cs
 mov word [0x12],isr
 mov word [0x14],cs
%endif
 ; Leave foreign UART framing/divisor, IER, MCR, IRQ vector and its PIC bit.
 ; Native PROGRAM must reclaim all of them before subsequent serial input.
 mov dx,PORT+1
 xor al,al
 out dx,al
 mov dx,0x21
 in al,dx
 or al,IRQBIT
 out dx,al
 mov dx,isr
 mov ax,0x2500+VECTOR
 int 0x21
 mov dx,PORT+3
 mov al,0x80
 out dx,al
 mov dx,PORT
 mov al,12
 out dx,al
 inc dx
 xor al,al
 out dx,al
 mov dx,PORT+3
 mov al,0x1e
 out dx,al
 inc dx
 in al,dx
 and al,1 ;DTR is the connection owner; changing it is correctly fatal.
 cmp byte [kind],'F'
 jne .keep_dtr
 xor al,al ; Dedicated fatal-line regression, not a successful handoff.
.keep_dtr:
 out dx,al
 mov ax,0x4c25
 cmp byte [kind],'R'
 jne .exit
 mov al,247
.exit:
 int 0x21
.bad:
 mov ax,0x4c63
 int 0x21
isr: iret
kind: db 0
logname: db 'CHILD.LOG',0
%ifdef REQUIRE_OUTPUT
outname: db 'WRITE.BIN',0
pending: times 8 db 0
expected: db 'pending5'
%endif
