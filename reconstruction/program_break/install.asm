; PCPlus 2.01 resident7508, exact80 bytes. Native callee-popped word ABI.
BITS 16
CPU 8086
%include "abi.inc"
%ifdef PROGRAM_BREAK_OMF
global program_break_install
extern program_break_ignore
%else
ORG 0x7508
%define program_break_ignore 0x7f90
%endif
%include "encodings.inc"
program_break_install:
 mov_load bx,sp
 mov ax,[bx+2]
 mov byte [program_break_original_flag],0xff
 cmp al,0
 jz short .vectors
 mov ax,0x3300
 int 0x21
 mov [program_break_original_flag],dl
 cmp dl,0
 jz short .vectors
 inc al
 xor_load dl,dl
 int 0x21
.vectors:
 mov ax,0x351b
 int 0x21
 mov [program_break_original_1b],bx
 mov [program_break_original_1b+2],es
 mov al,0x23
 int 0x21
 mov [program_break_original_23],bx
 mov [program_break_original_23+2],es
 mov dx,program_break_ignore
 push ds
 mov ax,cs
 mov ds,ax
 mov ax,0x251b
 int 0x21
 mov al,0x23
 int 0x21
 pop ds
 ret 2
