BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _help_view_close
global _help_view_bad_context
_help_view_bad_context:
 push bp
 mov bp,sp
 pushf
 push ds
 cmp word [bp+4],0
 jne .foreign
 cli
 jmp short .call
.foreign:
 mov ax,0x40
 mov ds,ax
.call:
 call far _help_view_close
 pop ds
 popf
 pop bp
 ret
