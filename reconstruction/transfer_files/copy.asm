; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_copy
global files_at_85b5
global files_at_85b7
global files_at_85b9
global files_at_85bb
global files_at_85bd
global files_at_85bf
global files_at_85c2
global files_at_85c5
global files_at_85c7
global files_at_85ca
global files_at_85cc
global files_at_85ce
global files_at_85d0
global files_at_85d2
global files_at_85d4
global files_at_85d6
global files_at_85d8
global files_at_85da
global files_at_85dc
global files_at_85de
global files_at_85df
global files_at_85e0
global files_at_85e1
global files_at_85e3
global files_at_85e4
global files_at_85e6
global files_at_85e8
global files_at_85ea
global files_at_85ec
global files_at_85ed
global files_at_85ee
global files_at_85f0
global files_at_85f2
global files_at_85f4
global files_at_85f6
global files_at_85f8
global files_at_85fa
global files_at_85fb
%else
ORG 0x85b4
%endif
%include "encodings.inc"
files_copy: push bp
files_at_85b5: mov_load bp,sp
files_at_85b7: mov_load dx,di
files_at_85b9: mov_load bx,si
files_at_85bb: mov ax,ds
files_at_85bd: mov es,ax
files_at_85bf: mov si,[bp+0x6]
files_at_85c2: mov di,[bp+0x4]
files_at_85c5: mov_load ax,di
files_at_85c7: mov cx,[bp+0x8]
files_at_85ca: jcxz files_at_85f6
files_at_85cc: cmp_load di,si
files_at_85ce: jna short files_at_85e6
files_at_85d0: mov_load ax,si
files_at_85d2: add_load ax,cx
files_at_85d4: cmp_load di,ax
files_at_85d6: jnc short files_at_85e6
files_at_85d8: mov_load ax,di
files_at_85da: add_load si,cx
files_at_85dc: add_load di,cx
files_at_85de: dec si
files_at_85df: dec di
files_at_85e0: std
files_at_85e1: rep movsb
files_at_85e3: cld
files_at_85e4: jmp short files_at_85f6
files_at_85e6: mov_load ax,di
files_at_85e8: test al,0x1
files_at_85ea: jz short files_at_85ee
files_at_85ec: movsb
files_at_85ed: dec cx
files_at_85ee: shr cx,1
files_at_85f0: rep movsw
files_at_85f2: adc_load cx,cx
files_at_85f4: rep movsb
files_at_85f6: mov_load si,bx
files_at_85f8: mov_load di,dx
files_at_85fa: pop bp
files_at_85fb: ret
