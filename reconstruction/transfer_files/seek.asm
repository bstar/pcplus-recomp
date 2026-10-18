; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_seek
global files_at_a22f
global files_at_a231
global files_at_a234
global files_at_a237
global files_at_a23b
global files_at_a23d
global files_at_a240
global files_at_a242
global files_at_a247
global files_at_a249
global files_at_a24d
global files_at_a24f
global files_at_a251
global files_at_a253
global files_at_a256
global files_at_a258
global files_at_a25a
global files_at_a25f
global files_at_a261
global files_at_a264
global files_at_a267
global files_at_a269
global files_at_a26c
global files_at_a26d
global files_at_a26f
global files_at_a272
global files_at_a275
global files_at_a277
global files_at_a27a
global files_at_a27c
global files_at_a27f
global files_at_a282
global files_at_a284
global files_at_a287
global files_at_a28a
global files_at_a28d
global files_at_a28f
global files_at_a291
global files_at_a294
global files_at_a297
global files_at_a29a
global files_at_a29c
global files_at_a29e
global files_at_a2a0
global files_at_a2a5
extern files_handle_limit
extern files_handle_flags
extern files_error_value
%else
ORG 0xa22e
%define files_handle_limit 0x7b29
%define files_handle_flags 0x7b2b
%define files_error_value 0x9435
%endif
%include "encodings.inc"
files_seek: push bp
files_at_a22f: mov_load bp,sp
files_at_a231: sub sp,0x4
files_at_a234: mov bx,[bp+0x4]
files_at_a237: cmp bx,[files_handle_limit]
files_at_a23b: jc short files_at_a242
files_at_a23d: mov ax,0x900
files_at_a240: jmp short files_at_a26c
files_at_a242: test word [bp+0x8],0x8000
files_at_a247: jz short files_at_a291
files_at_a249: cmp word [bp+0xa],0x0
files_at_a24d: jz short files_at_a269
files_at_a24f: xor_load cx,cx
files_at_a251: mov_load dx,cx
files_at_a253: mov ax,0x4201
files_at_a256: int byte 0x21
files_at_a258: jc short files_at_a2a5
files_at_a25a: test word [bp+0xa],0x2
files_at_a25f: jnz short files_at_a26f
files_at_a261: add ax,[bp+0x6]
files_at_a264: adc dx,[bp+0x8]
files_at_a267: jns short files_at_a291
files_at_a269: mov ax,0x1600
files_at_a26c: stc
files_at_a26d: jmp short files_at_a2a5
files_at_a26f: mov [bp-0x2],dx
files_at_a272: mov [bp-0x4],ax
files_at_a275: mov_load dx,cx
files_at_a277: mov ax,0x4202
files_at_a27a: int byte 0x21
files_at_a27c: add ax,[bp+0x6]
files_at_a27f: adc dx,[bp+0x8]
files_at_a282: jns short files_at_a291
files_at_a284: mov cx,[bp-0x2]
files_at_a287: mov dx,[bp-0x4]
files_at_a28a: mov ax,0x4200
files_at_a28d: int byte 0x21
files_at_a28f: jmp short files_at_a269
files_at_a291: mov dx,[bp+0x6]
files_at_a294: mov cx,[bp+0x8]
files_at_a297: mov al,[bp+0xa]
files_at_a29a: mov ah,0x42
files_at_a29c: int byte 0x21
files_at_a29e: jc short files_at_a2a5
files_at_a2a0: and byte [bx+files_handle_flags],0xfd
files_at_a2a5: jmp near files_error_value
