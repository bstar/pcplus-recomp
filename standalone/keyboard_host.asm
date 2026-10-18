; Source-only keyboard host. Debug callback is an observed integration boundary.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern keyboard_read_extended,keyboard_poll
global keyboard_debug_callback
keyboard_debug_callback:
 inc word [keyboard_debug_count]
 ret
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 ; Test the BIOS path with real emulated keyboard input: letter, arrows, Alt-X.
 call keyboard_read_extended
 cmp ax,'k'
 jne .failed
 call keyboard_read_extended
 cmp ax,0x4800
 jne .failed
 call keyboard_read_extended
 cmp ax,0x4d00
 jne .failed
 call keyboard_read_extended
 cmp ax,0x2d00
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
%macro wordvar 2
 global %1
 %1: dw %2
%endmacro
wordvar keyboard_queue_count,0
wordvar keyboard_queue_index,0
wordvar keyboard_queue_active,0
wordvar keyboard_debug_gate,-1
wordvar keyboard_debug_count,0
global keyboard_queue_peek,keyboard_queue_values,keyboard_bios_mode
; Original peek and dequeue bases are twelve bytes apart; preserve independent
; storage until producer semantics have been recovered.
keyboard_queue_peek: times 6 dw 0
keyboard_queue_values: times 64 dw 0
keyboard_bios_mode: db 0
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
