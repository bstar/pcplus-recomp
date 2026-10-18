; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global erase_move_bytes
%define short
%else
ORG 0x85b4
%endif
%include "encodings.inc"
erase_move_bytes:
L_85b4: push bp
L_85b5: mov_load bp,sp
L_85b7: mov_load dx,di
L_85b9: mov_load bx,si
L_85bb: mov ax,ds
L_85bd: mov es,ax
L_85bf: mov si,[bp+0x6]
L_85c2: mov di,[bp+0x4]
L_85c5: mov_load ax,di
L_85c7: mov cx,[bp+0x8]
L_85ca: jcxz L_85f6
L_85cc: cmp_load di,si
L_85ce: jna short L_85e6
L_85d0: mov_load ax,si
L_85d2: add_load ax,cx
L_85d4: cmp_load di,ax
L_85d6: jnc short L_85e6
L_85d8: mov_load ax,di
L_85da: add_load si,cx
L_85dc: add_load di,cx
L_85de: dec si
L_85df: dec di
L_85e0: std
L_85e1: rep movsb
L_85e3: cld
L_85e4: jmp short L_85f6
L_85e6: mov_load ax,di
L_85e8: test al,0x1
L_85ea: jz short L_85ee
L_85ec: movsb
L_85ed: dec cx
L_85ee: shr cx,1
L_85f0: rep movsw
L_85f2: adc_load cx,cx
L_85f4: rep movsb
L_85f6: mov_load si,bx
L_85f8: mov_load di,dx
L_85fa: pop bp
L_85fb: ret
