BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern _directory_accounting_patch
%macro arg 1
 mov ax,%1
 push ax
%endmacro
%macro patch 4
 arg %4
 arg %3
 arg %2
 arg %1
 arg directory_accounting_output
 arg directory_accounting_input
 call _directory_accounting_patch
 add sp,12
%endmacro
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov word [directory_accounting_input+70],65535
 patch 2026,10,17,2
 or ax,ax
 jnz .fail
 cmp word [directory_accounting_output+70],1
 jne .fail
 cmp word [directory_accounting_output+61],0x3031
 jne .fail
 cmp word [directory_accounting_output+67],0x3632
 jne .fail
 cmp byte [directory_accounting_output+69],0
 jne .fail
 patch 2000,2,29,0
 or ax,ax
 jnz .fail
 cmp word [directory_accounting_output+67],0x3030
 jne .fail
 patch 2001,2,29,1
 cmp ax,2
 jne .fail
 cmp word [directory_accounting_output+67],0x3030
 jne .fail
 mov ax,0x4c00
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public class=DATA use16
global directory_accounting_input,directory_accounting_output
 dw 0xa55a
directory_accounting_input: times 114 db 0x39
 dw 0x5aa5
 dw 0xa55a
directory_accounting_output: times 114 db 0x58
 dw 0x5aa5
SEGMENT STACK stack class=STACK use16
 resb 2048
stack_top:
