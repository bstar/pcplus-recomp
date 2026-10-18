; Exact PCPlus2.01 resident:8d18..8d33.
BITS 16
CPU 8086
%ifdef DIRECTORY_DIAL_OMF
SEGMENT _TEXT public class=CODE use16
global directory_dial_length_original
%else
ORG 0x8d18
%endif
%include "encodings.inc"
directory_dial_length_original:
L_8d18: push bp
L_8d19: mov_load bp,sp
L_8d1b: mov_load dx,di
L_8d1d: mov ax, ds
L_8d1f: mov es, ax
L_8d21: mov di, word [bp + 0x4]
L_8d24: xor_load ax,ax
L_8d26: mov cx, 0xffff
L_8d29: repne scasb
L_8d2b: not cx
L_8d2d: dec cx
L_8d2e: xchg ax, cx
L_8d2f: mov_load di,dx
L_8d31: pop bp
L_8d32: ret
