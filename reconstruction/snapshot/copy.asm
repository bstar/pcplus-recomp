; Exact original screen snapshot instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef SNAPSHOT_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global snapshot_copy_original
global snapshot_at_64ba
global snapshot_at_64bb
global snapshot_at_64bc
global snapshot_at_64bd
global snapshot_at_64be
global snapshot_at_64c1
global snapshot_at_64c2
global snapshot_at_64c3
global snapshot_at_64c6
global snapshot_at_64c8
global snapshot_at_64ca
global snapshot_at_64cb
global snapshot_at_64ce
global snapshot_at_64d0
global snapshot_at_64d1
global snapshot_at_64d3
global snapshot_at_64d5
global snapshot_at_64d7
global snapshot_at_64d8
global snapshot_at_64da
global snapshot_at_64dc
global snapshot_at_64dd
global snapshot_at_64df
global snapshot_at_64e1
global snapshot_at_64e3
global snapshot_at_64e5
global snapshot_at_64e7
global snapshot_at_64e9
global snapshot_at_64eb
global snapshot_at_64ed
global snapshot_at_64ef
global snapshot_at_64f0
global snapshot_at_64f1
global snapshot_at_64f3
global snapshot_at_64f4
global snapshot_at_64f5
global snapshot_at_64f6
global snapshot_at_64f7
global snapshot_at_64f8
global snapshot_at_64fa
%else
ORG 0x64b8
%endif
%include "encodings.inc"
snapshot_copy_original: mov_load bx,sp
snapshot_at_64ba: push ds
snapshot_at_64bb: push di
snapshot_at_64bc: push si
snapshot_at_64bd: std
snapshot_at_64be: mov cx,[bx+0x2]
snapshot_at_64c1: push ds
snapshot_at_64c2: pop es
snapshot_at_64c3: mov di,[bx+0x8]
snapshot_at_64c6: add_load di,cx
snapshot_at_64c8: sub_load ax,ax
snapshot_at_64ca: stosb
snapshot_at_64cb: lds si,word [bx+0x4]
snapshot_at_64ce: mov_load bx,cx
snapshot_at_64d0: dec bx
snapshot_at_64d1: shl bx,1
snapshot_at_64d3: add_load si,bx
snapshot_at_64d5: mov_load bx,cx
snapshot_at_64d7: inc bx
snapshot_at_64d8: sub_load dx,dx
snapshot_at_64da: jcxz snapshot_at_64f3
snapshot_at_64dc: lodsw
snapshot_at_64dd: or_load al,al
snapshot_at_64df: jnz short snapshot_at_64e3
snapshot_at_64e1: mov al,0x20
snapshot_at_64e3: or_load dx,dx
snapshot_at_64e5: jnz short snapshot_at_64f0
snapshot_at_64e7: cmp al,0x20
snapshot_at_64e9: jnz short snapshot_at_64ef
snapshot_at_64eb: mov_load bx,cx
snapshot_at_64ed: jmp short snapshot_at_64f0
snapshot_at_64ef: inc dx
snapshot_at_64f0: stosb
snapshot_at_64f1: loop snapshot_at_64dc
snapshot_at_64f3: cld
snapshot_at_64f4: pop si
snapshot_at_64f5: pop di
snapshot_at_64f6: pop ds
snapshot_at_64f7: dec bx
snapshot_at_64f8: mov_load ax,bx
snapshot_at_64fa: ret word 0x8
