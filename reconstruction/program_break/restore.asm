; PCPlus 2.01 resident758a, exact36 bytes. Native near no-argument ABI.
BITS 16
CPU 8086
%include "abi.inc"
%ifndef PROGRAM_BREAK_OMF
ORG 0x758a
%else
global program_break_restore
%endif
%include "encodings.inc"
program_break_restore:
 push ds
 lds dx,[program_break_original_1b]
 mov ax,0x251b
 int 0x21
 pop ds
 push ds
 lds dx,[program_break_original_23]
 mov al,0x23
 int 0x21
 pop ds
 cmp byte [program_break_original_flag],1
 jne short .done
 mov ax,0x3301
 mov_load dl,al
 int 0x21
.done:
 ret
