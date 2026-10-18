; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_path_component
%define short
%else
ORG 0xa8e6
%endif
%include "encodings.inc"
program_path_component:
L_a8e6: push bp
L_a8e7: mov_load bp,sp
L_a8e9: sub sp,0x2
L_a8ec: push di
L_a8ed: push si
L_a8ee: mov si,[bp+0x4]
L_a8f1: mov di,[bp+0x6]
L_a8f4: mov [bp-0x2],si
L_a8f7: dec word [bp+0x8]
L_a8fa: jz short L_a91c
L_a8fc: cmp byte [si],0x0
L_a8ff: jz short L_a917
L_a901: cmp byte [si],0x3b
L_a904: jz short L_a917
L_a906: mov al,[si]
L_a908: mov [di],al
L_a90a: inc si
L_a90b: inc di
L_a90c: dec word [bp+0x8]
L_a90f: jnz short L_a8fc
L_a911: mov [bp-0x2],si
L_a914: jmp short L_a91c
L_a916: inc si
L_a917: cmp byte [si],0x3b
L_a91a: jz short L_a916
L_a91c: mov byte [di],0x0
L_a91f: cmp [bp-0x2],si
L_a922: jz short L_a928
L_a924: mov_load ax,si
L_a926: jmp short L_a92a
L_a928: sub_load ax,ax
L_a92a: pop si
L_a92b: pop di
L_a92c: mov_load sp,bp
L_a92e: pop bp
L_a92f: ret
