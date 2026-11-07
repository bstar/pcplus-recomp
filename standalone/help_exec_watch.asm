; Test-only bounded observer of real DOS EXEC/child-status calls and results.
; Chains the actual kernel; never changes product data or calls DOS in hook.
BITS 16
CPU 8086
ORG 100h
jmp start
old21 dd 0
depth: dw 0
held_ss: times 16 dw 0
held_sp: times 16 dw 0
held_bp: times 16 dw 0
held_record: times 16 dw 0
returned_ax: dw 0
returned_bx: dw 0
returned_carry: dw 0
state: dw 0x4b48,0,0
records: times 16*24 db 0
handler:
 pushf
 cmp ax,0x4b00
 je .selected
 cmp ah,0x4d
 je .selected
.chain:
 popf
 jmp far [cs:old21]
.selected:
 popf
 push bp
 mov bp,sp
 sub sp,2
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 cmp word [cs:state+2],16
 jae .full
 mov bx,[cs:state+2]
 inc word [cs:state+2]
 mov ax,24
 mul bx
 mov bx,ax
 mov [ss:bp-2],bx
 mov ax,[ss:bp-6]
 mov [cs:records+bx],ax
 cmp ax,0x4b00
 jne .captured
 mov si,[ss:bp-12]
 cmp si,65518
 ja .captured
 push cs
 pop es
 mov di,records+6
 add di,bx
 mov cx,18
 cld
.name:
 lodsb
 stosb
 or al,al
 loopnz .name
.captured:
 mov si,[cs:depth]
 shl si,1
 mov [cs:held_ss+si],ss
 mov [cs:held_bp+si],bp
 mov [cs:held_record+si],bx
 mov ax,bp
 sub ax,2
 mov [cs:held_sp+si],ax
 inc word [cs:depth]
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 pushf
 call far [cs:old21]
 ; EXEC may destroy SS:SP and other registers. The real callers repair their
 ; own stack after INT21; this return observer must repair its stack first.
 ; Only CF/AX are defined here. Preserve caller FLAGS with the returned CF.
 mov word [cs:returned_carry],0
 jnc .carry_saved
 mov word [cs:returned_carry],1
.carry_saved:
 mov [cs:returned_ax],ax
 mov [cs:returned_bx],bx
 mov bx,[cs:depth]
 dec bx
 shl bx,1
 cli
 mov ss,[cs:held_ss+bx]
 mov sp,[cs:held_sp+bx]
 mov bp,[cs:held_bp+bx]
 mov bx,[cs:held_record+bx]
 mov [cs:records+bx+2],ax
 mov ax,[cs:returned_carry]
 mov [cs:records+bx+4],ax
 and word [ss:bp+6],0xfffe
 or [ss:bp+6],ax
 dec word [cs:depth]
 mov ax,[cs:returned_ax]
 mov bx,[cs:returned_bx]
 mov sp,bp
 pop bp
 iret
.full:
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 mov sp,bp
 pop bp
 jmp far [cs:old21]
resident_end:
start:
 mov ax,0x3521
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old21],bx
 mov [old21+2],es
 mov dx,handler
 mov ax,0x2521
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,0x3100
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:state],0x4b48
 jne failed
 mov si,state
 mov di,buffer
 mov cx,390
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,[es:old21]
 mov [expected],dx
 mov ax,[es:old21+2]
 mov [expected+2],ax
 push ds
 mov ds,ax
 mov ax,0x2521
 int 21h
 pop ds
 mov ax,0x3521
 int 21h
 cmp bx,[expected]
 jne failed
 mov ax,es
 cmp ax,[expected+2]
 jne failed
 mov word [buffer+4],1
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,390
 mov ah,0x40
 int 21h
 jc .close_failed
 cmp ax,390
 jne .close_failed
 mov ah,0x3e
 int 21h
 jc failed
 mov ax,0x4c00
 int 21h
.close_failed:
 mov ah,0x3e
 int 21h
failed:
 mov ax,0x4c01
 int 21h
expected: dd 0
filename: db 'D:\EXECTRAC.BIN',0
buffer: times 390 db 0
