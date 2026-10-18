; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_fwrite
global files_at_86ad
global files_at_86af
global files_at_86b2
global files_at_86b3
global files_at_86b4
global files_at_86b7
global files_at_86ba
global files_at_86bc
global files_at_86be
global files_at_86c1
global files_at_86c4
global files_at_86c7
global files_at_86ca
global files_at_86cc
global files_at_86cf
global files_at_86d1
global files_at_86d5
global files_at_86d7
global files_at_86da
global files_at_86dc
global files_at_86df
global files_at_86e1
global files_at_86e4
global files_at_86e7
global files_at_86eb
global files_at_86ed
global files_at_86f0
global files_at_86f2
global files_at_86f5
global files_at_86f7
global files_at_86f9
global files_at_86fb
global files_at_86fd
global files_at_86ff
global files_at_8700
global files_at_8701
global files_at_8702
global files_at_8703
global files_at_8704
global files_at_8706
global files_at_8709
global files_at_870c
global files_at_870d
global files_at_870e
global files_at_870f
global files_at_8711
global files_at_8714
global files_at_8716
global files_at_8718
global files_at_871a
global files_at_871d
global files_at_871f
global files_at_8721
global files_at_8723
global files_at_8726
global files_at_8728
global files_at_872c
global files_at_872e
global files_at_8731
global files_at_8733
global files_at_8734
global files_at_8735
global files_at_8736
global files_at_8739
global files_at_873a
global files_at_873b
global files_at_873c
global files_at_873e
global files_at_8740
global files_at_8742
global files_at_8744
global files_at_8747
global files_at_8749
global files_at_874b
global files_at_874c
global files_at_874d
global files_at_874e
global files_at_874f
global files_at_8750
global files_at_8752
global files_at_8755
global files_at_8756
global files_at_8759
global files_at_875c
global files_at_875d
global files_at_875e
global files_at_875f
global files_at_8762
global files_at_8764
global files_at_8766
global files_at_8768
global files_at_876a
global files_at_876c
global files_at_876e
global files_at_8770
global files_at_8772
global files_at_8773
global files_at_8774
global files_at_8775
global files_at_8776
global files_at_8779
global files_at_877c
global files_at_877d
global files_at_877e
global files_at_8781
global files_at_8783
global files_at_8784
global files_at_8785
global files_at_8788
global files_at_878a
global files_at_878c
global files_at_878d
global files_at_8790
global files_at_8792
global files_at_8796
global files_at_8798
global files_at_879b
global files_at_879d
global files_at_879f
global files_at_87a2
global files_at_87a4
global files_at_87a7
global files_at_87a8
global files_at_87a9
global files_at_87ab
global files_at_87ac
extern files_copy_wrapper
extern files_stream_table
extern files_extra_table
extern files_fflush
extern files_putc
extern files_write
%else
ORG 0x86ac
%define files_copy_wrapper 0x4735
%define files_stream_table 0x7b6a
%define files_extra_table 0x7c0a
%define files_fflush 0x8c54
%define files_putc 0x91a6
%define files_write 0xa368
%endif
%include "encodings.inc"
files_fwrite: push bp
files_at_86ad: mov_load bp,sp
files_at_86af: sub sp,0x4
files_at_86b2: push si
files_at_86b3: push di
files_at_86b4: mov ax,[bp+0x6]
files_at_86b7: mul word [bp+0x8]
files_at_86ba: mov_load cx,ax
files_at_86bc: jcxz files_at_871a
files_at_86be: mov [bp-0x2],ax
files_at_86c1: mov bx,[bp+0x4]
files_at_86c4: mov si,[bp+0xa]
files_at_86c7: mov di,files_extra_table
files_at_86ca: mov_load ax,si
files_at_86cc: sub ax,files_stream_table
files_at_86cf: add_load di,ax
files_at_86d1: test byte [si+0x6],0xc
files_at_86d5: jnz short files_at_86dc
files_at_86d7: test byte [di],0x1
files_at_86da: jz short files_at_86e1
files_at_86dc: mov ax,[di+0x2]
files_at_86df: jmp short files_at_86e4
files_at_86e1: mov ax,0x200
files_at_86e4: mov [bp-0x4],ax
files_at_86e7: test byte [si+0x6],0x8
files_at_86eb: jnz short files_at_86f2
files_at_86ed: test byte [di],0x1
files_at_86f0: jz short files_at_8723
files_at_86f2: mov ax,[si+0x2]
files_at_86f5: or_load ax,ax
files_at_86f7: jz short files_at_8723
files_at_86f9: cmp_load ax,cx
files_at_86fb: jna short files_at_86ff
files_at_86fd: mov_load ax,cx
files_at_86ff: push ax
files_at_8700: push bx
files_at_8701: push cx
files_at_8702: push ax
files_at_8703: push bx
files_at_8704: push word [si]
files_at_8706: call files_copy_wrapper
files_at_8709: add sp,0x6
files_at_870c: pop cx
files_at_870d: pop bx
files_at_870e: pop ax
files_at_870f: sub_load cx,ax
files_at_8711: sub [si+0x2],ax
files_at_8714: add_load bx,ax
files_at_8716: add [si],ax
files_at_8718: jmp short files_at_871d
files_at_871a: jmp near files_at_87a7
files_at_871d: or_load cx,cx
files_at_871f: jnz short files_at_86e7
files_at_8721: jmp short files_at_8796
files_at_8723: cmp cx,[bp-0x4]
files_at_8726: jc short files_at_876e
files_at_8728: test byte [si+0x6],0x8
files_at_872c: jnz short files_at_8733
files_at_872e: test byte [di],0x1
files_at_8731: jz short files_at_8740
files_at_8733: push bx
files_at_8734: push cx
files_at_8735: push si
files_at_8736: call files_fflush
files_at_8739: pop dx
files_at_873a: pop cx
files_at_873b: pop bx
files_at_873c: or_load ax,ax
files_at_873e: jnz short files_at_8796
files_at_8740: xor_load dx,dx
files_at_8742: mov_load ax,cx
files_at_8744: div word [bp-0x4]
files_at_8747: mov_load ax,cx
files_at_8749: sub_load ax,dx
files_at_874b: push ax
files_at_874c: push bx
files_at_874d: push cx
files_at_874e: push ax
files_at_874f: push bx
files_at_8750: xor_load ax,ax
files_at_8752: mov al,[si+0x7]
files_at_8755: push ax
files_at_8756: call files_write
files_at_8759: add sp,0x6
files_at_875c: pop cx
files_at_875d: pop bx
files_at_875e: pop dx
files_at_875f: cmp ax,strict word 0xffff
files_at_8762: jz short files_at_8792
files_at_8764: sub_load cx,ax
files_at_8766: cmp_load ax,dx
files_at_8768: jnz short files_at_8792
files_at_876a: add_load bx,ax
files_at_876c: jmp short files_at_871d
files_at_876e: xor_load ax,ax
files_at_8770: mov al,[bx]
files_at_8772: push bx
files_at_8773: push cx
files_at_8774: push si
files_at_8775: push ax
files_at_8776: call files_putc
files_at_8779: add sp,0x4
files_at_877c: pop cx
files_at_877d: pop bx
files_at_877e: cmp ax,strict word 0xffff
files_at_8781: jz short files_at_8796
files_at_8783: inc bx
files_at_8784: dec cx
files_at_8785: mov ax,[di+0x2]
files_at_8788: or_load ax,ax
files_at_878a: jnz short files_at_878d
files_at_878c: inc ax
files_at_878d: mov [bp-0x4],ax
files_at_8790: jmp short files_at_871d
files_at_8792: or byte [si+0x6],0x20
files_at_8796: jcxz files_at_87a4
files_at_8798: mov ax,[bp-0x2]
files_at_879b: sub_load ax,cx
files_at_879d: xor_load dx,dx
files_at_879f: div word [bp+0x6]
files_at_87a2: jmp short files_at_87a7
files_at_87a4: mov ax,[bp+0x8]
files_at_87a7: pop di
files_at_87a8: pop si
files_at_87a9: mov_load sp,bp
files_at_87ab: pop bp
files_at_87ac: ret
