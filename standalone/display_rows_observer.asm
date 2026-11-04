; Diagnostic only: observe BIOS changes and optionally refuse one font request.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _display_rows_observer_start,_display_rows_observer_stop
global _display_rows_observer_count,_display_rows_observer_arm
global _display_rows_observer_pending,_display_rows_observer_dropped
global _display_rows_observer_refuse_modes,_display_rows_observer_modes_pending
global _display_rows_observer_modes_dropped
changes: dw 0
fault: dw 0
dropped: dw 0
modes_pending: dw 0
modes_dropped: dw 0
old_vector: dw 0,0
owned: dw 0
handler:
 cmp ah,0
 je .mode
 cmp ah,0x11
 jne .chain
 cmp al,0x11
 je .change
 cmp al,0x12
 jne .chain
.change:
 inc word [cs:changes]
 cmp ax,0x1112
 jne .chain
 cmp word [cs:fault],0
 je .chain
 mov word [cs:fault],0
 inc word [cs:dropped]
 iret
.mode:
 inc word [cs:changes]
 cmp word [cs:modes_pending],0
 je .chain
 dec word [cs:modes_pending]
 inc word [cs:modes_dropped]
 iret
.chain:
 jmp far [cs:old_vector]
_display_rows_observer_count:
 mov ax,[cs:changes]
 ret
_display_rows_observer_arm:
 mov word [cs:fault],1
 ret
_display_rows_observer_pending:
 mov ax,[cs:fault]
 ret
_display_rows_observer_dropped:
 mov ax,[cs:dropped]
 ret
_display_rows_observer_refuse_modes:
 mov word [cs:modes_pending],2
 ret
_display_rows_observer_modes_pending:
 mov ax,[cs:modes_pending]
 ret
_display_rows_observer_modes_dropped:
 mov ax,[cs:modes_dropped]
 ret
_display_rows_observer_start:
 push es
 mov ax,0x3510
 int 0x21
 mov [cs:old_vector],bx
 mov [cs:old_vector+2],es
 push ds
 push cs
 pop ds
 mov dx,handler
 mov ax,0x2510
 int 0x21
 pop ds
 mov word [cs:owned],1
 pop es
 ret
_display_rows_observer_stop:
 cmp word [cs:owned],0
 je .done
 push ds
 mov dx,[cs:old_vector]
 mov ds,[cs:old_vector+2]
 mov ax,0x2510
 int 0x21
 pop ds
 mov word [cs:owned],0
.done:
 ret
