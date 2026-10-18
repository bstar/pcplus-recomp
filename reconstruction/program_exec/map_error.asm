; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_map_error
extern program_errno
extern program_dos_error
extern program_error_map
extern program_dos_major
%define short
%else
ORG 0x9448
%define program_errno 0x7b1c
%define program_dos_error 0x7b27
%define program_error_map 0x7b56
%define program_dos_major 0x7b24
%endif
%include "encodings.inc"
program_map_error:
L_9448: mov [program_dos_error],al
L_944b: or_load ah,ah
L_944d: jnz short L_9471
L_944f: cmp byte [program_dos_major],0x3
L_9454: jc short L_9462
L_9456: cmp al,0x22
L_9458: jnc short L_9466
L_945a: cmp al,0x20
L_945c: jc short L_9462
L_945e: mov al,0x5
L_9460: jmp short L_9468
L_9462: cmp al,0x13
L_9464: jna short L_9468
L_9466: mov al,0x13
L_9468: mov bx,program_error_map
L_946b: xlatb
L_946c: cbw
L_946d: mov [program_errno],ax
L_9470: ret
L_9471: mov_load al,ah
L_9473: jmp short L_946c
