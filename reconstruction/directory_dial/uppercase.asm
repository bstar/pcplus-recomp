; Exact PCPlus2.01 resident:9128..9146.
BITS 16
CPU 8086
%ifdef DIRECTORY_DIAL_OMF
SEGMENT _TEXT public class=CODE use16
global directory_dial_upper_original
%else
ORG 0x9128
%endif
%include "encodings.inc"
directory_dial_upper_original:
L_9128: push bp
L_9129: mov_load bp,sp
L_912b: mov bx, word [bp + 0x4]
L_912e: mov_load dx,bx
L_9130: jmp short L_913d
L_9132: sub al, 0x61
L_9134: cmp al, 0x1a
L_9136: jnc L_913c
L_9138: add al, 0x41
L_913a: mov byte [bx], al
L_913c: inc bx
L_913d: mov al, byte [bx]
L_913f: or_load al,al
L_9141: jnz L_9132
L_9143: xchg ax, dx
L_9144: pop bp
L_9145: ret
