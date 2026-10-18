; Source-only DOS assertions for recovered PCPlus attribute helpers.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern attributes_normal,attributes_bold,attributes_blink,attributes_reverse
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 call attributes_normal
 cmp word [attributes_current],7
 jne .failed
 call attributes_bold
 call attributes_blink
 cmp word [attributes_current],0x8f
 jne .failed
 call attributes_reverse
 cmp word [attributes_current],0xf8
 jne .failed
 call attributes_reverse
 cmp word [attributes_current],0xf8
 jne .failed
 call attributes_normal
 cmp word [attributes_current],7
 jne .failed
 cmp byte [attributes_reverse_active],0
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
wordvar attributes_normal_value,7
wordvar attributes_bold_value,15
wordvar attributes_preset_value,0x17
wordvar attributes_reverse_value,0x70
wordvar attributes_underline_value,1
wordvar attributes_blink_active,0
wordvar attributes_bold_active,0
wordvar attributes_current,0
wordvar attributes_monochrome,0
wordvar attributes_color_mode,1
global attributes_reverse_active
attributes_reverse_active: db 0
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
