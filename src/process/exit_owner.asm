BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _program_exit_retain,_program_exit_stop
_program_exit_retain:
 push bp
 mov bp,sp
 mov bx,[bp+4]
 mov ah,0x50
 int 0x21
 mov dx,[bp+6]
 mov ax,[bp+8]
 mov ah,0x31
 int 0x21
 ; DOS31 must not return. Invalid kernel/memory state cannot fall into DOS4C.
_program_exit_stop:
 sti
.held:
 hlt
 jmp short .held
