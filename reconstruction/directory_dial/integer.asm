; Exact PCPlus2.01 resident:a7ce..a822.
BITS 16
CPU 8086
%ifdef DIRECTORY_DIAL_OMF
SEGMENT _TEXT public class=CODE use16
global directory_dial_integer_original
%else
ORG 0xa7ce
%endif
%include "encodings.inc"
directory_dial_integer_original:
L_a7ce: push bp
L_a7cf: mov_load bp,sp
L_a7d1: push di
L_a7d2: push si
L_a7d3: mov si, word [bp + 0x4]
L_a7d6: xor_load ax,ax
L_a7d8: cwd
L_a7d9: xor_load bx,bx
L_a7db: lodsb
L_a7dc: cmp al, 0x20
L_a7de: jz L_a7db
L_a7e0: cmp al, 0x9
L_a7e2: jz L_a7db
L_a7e4: push ax
L_a7e5: cmp al, 0x2d
L_a7e7: jz L_a7ed
L_a7e9: cmp al, 0x2b
L_a7eb: jnz L_a7ee
L_a7ed: lodsb
L_a7ee: cmp al, 0x39
L_a7f0: ja L_a811
L_a7f2: sub al, 0x30
L_a7f4: jc L_a811
L_a7f6: shl bx, 0x1
L_a7f8: rcl dx, 0x1
L_a7fa: mov_load cx,bx
L_a7fc: mov_load di,dx
L_a7fe: shl bx, 0x1
L_a800: rcl dx, 0x1
L_a802: shl bx, 0x1
L_a804: rcl dx, 0x1
L_a806: add_load bx,cx
L_a808: adc_load dx,di
L_a80a: add_load bx,ax
L_a80c: adc dx, 0x0
L_a80f: jmp short L_a7ed
L_a811: pop ax
L_a812: cmp al, 0x2d
L_a814: xchg ax, bx
L_a815: jnz L_a81e
L_a817: neg ax
L_a819: adc dx, 0x0
L_a81c: neg dx
L_a81e: pop si
L_a81f: pop di
L_a820: pop bp
L_a821: ret
