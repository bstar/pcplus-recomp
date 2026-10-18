; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_strrchr
%define short
%else
ORG 0x83c6
%endif
%include "encodings.inc"
program_strrchr:
L_83c6: push bp
L_83c7: mov_load bp,sp
L_83c9: push di
L_83ca: push ds
L_83cb: pop es
L_83cc: mov di,[bp+0x4]
L_83cf: xor_load ax,ax
L_83d1: mov cx,0xffff
L_83d4: repne scasb
L_83d6: inc cx
L_83d7: neg cx
L_83d9: dec di
L_83da: mov al,[bp+0x6]
L_83dd: std
L_83de: repne scasb
L_83e0: inc di
L_83e1: cmp [di],al
L_83e3: jz short L_83e9
L_83e5: xor_load ax,ax
L_83e7: jmp short L_83eb
L_83e9: mov_load ax,di
L_83eb: cld
L_83ec: pop di
L_83ed: mov_load sp,bp
L_83ef: pop bp
L_83f0: ret
