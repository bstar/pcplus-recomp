BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _alarm_dos_context,_alarm_dos_ticks
_alarm_dos_context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 and ax,0x200
 ret
.bad:
 xor ax,ax
 ret
_alarm_dos_ticks:
 push es
 mov ax,0x40
 mov es,ax
 pushf
 cli
 mov ax,[es:0x6c]
 mov dx,[es:0x6e]
 popf
 pop es
 ret
