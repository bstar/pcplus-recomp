; Checked unsigned decimal conversion for the maintained parameter reader.
; Near string pointer at SS:SP+2, caller removes argument. AX=value, CF=overflow.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global ansi_decimal
ansi_decimal:
 mov bx,sp
 push si
 mov si,[bx+2]
 xor ax,ax
 mov cx,10
.next:
 xor bx,bx
 mov bl,[si]
 inc si
 cmp bl,0
 je .done
 sub bx,'0'
 cmp bx,9
 ja .bad
 mul cx
 or dx,dx
 jnz .bad
 add ax,bx
 jc .bad
 jmp .next
.done:
 pop si
 clc
 ret
.bad:
 pop si
 stc
 ret
