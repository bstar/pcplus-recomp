; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_write
global files_at_a369
global files_at_a36b
global files_at_a36e
global files_at_a371
global files_at_a375
global files_at_a377
global files_at_a37a
global files_at_a37b
global files_at_a37e
global files_at_a384
global files_at_a386
global files_at_a38a
global files_at_a38f
global files_at_a391
global files_at_a394
global files_at_a396
global files_at_a398
global files_at_a39a
global files_at_a39c
global files_at_a3a1
global files_at_a3a3
global files_at_a3a6
global files_at_a3a7
global files_at_a3a8
global files_at_a3aa
global files_at_a3ad
global files_at_a3b0
global files_at_a3b1
global files_at_a3b2
global files_at_a3b3
global files_at_a3b5
global files_at_a3b7
global files_at_a3ba
global files_at_a3bd
global files_at_a3bf
global files_at_a3c1
global files_at_a3c3
global files_at_a3c5
global files_at_a3c8
global files_at_a3cb
global files_at_a3cd
global files_at_a3d0
global files_at_a3d2
global files_at_a3d5
global files_at_a3d8
global files_at_a3da
global files_at_a3dd
global files_at_a3df
global files_at_a3e1
global files_at_a3e3
global files_at_a3e4
global files_at_a3e5
global files_at_a3e8
global files_at_a3e9
global files_at_a3eb
global files_at_a3ed
global files_at_a3ef
global files_at_a3f1
global files_at_a3f2
global files_at_a3f4
global files_at_a3f7
global files_at_a3f9
global files_at_a3fb
global files_at_a3fd
global files_at_a3ff
global files_at_a402
global files_at_a403
global files_at_a405
global files_at_a408
global files_at_a40a
global files_at_a40d
global files_at_a40f
global files_at_a410
global files_at_a411
global files_at_a413
global files_at_a416
global files_at_a419
global files_at_a41a
global files_at_a41b
global files_at_a41c
global files_at_a41e
global files_at_a420
global files_at_a422
global files_at_a423
global files_at_a426
global files_at_a428
global files_at_a42a
global files_at_a42b
global files_at_a42d
global files_at_a430
global files_at_a432
global files_at_a434
global files_at_a435
global files_at_a436
global files_at_a437
global files_at_a439
global files_at_a43a
global files_at_a43b
global files_at_a43e
global files_at_a442
global files_at_a444
global files_at_a445
global files_at_a447
global files_at_a449
global files_at_a44b
global files_at_a450
global files_at_a452
global files_at_a455
global files_at_a458
global files_at_a45a
global files_at_a45b
global files_at_a45d
global files_at_a45e
global files_at_a461
global files_at_a463
global files_at_a466
global files_at_a469
global files_at_a46c
global files_at_a46d
global files_at_a46e
global files_at_a471
global files_at_a474
global files_at_a476
global files_at_a478
global files_at_a47a
global files_at_a47d
global files_at_a480
global files_at_a482
global files_at_a484
global files_at_a486
global files_at_a488
global files_at_a48a
global files_at_a48c
global files_at_a48e
global files_at_a493
global files_at_a495
global files_at_a497
global files_at_a49a
global files_at_a49c
global files_at_a49d
global files_at_a49f
global files_at_a4a0
global files_at_a4a3
global files_at_a4a5
extern files_handle_limit
extern files_handle_flags
extern files_overlay_cookie
extern files_overlay_callback
extern files_error_value
extern files_stack_failure
extern files_stack_available
%else
ORG 0xa368
%define files_handle_limit 0x7b29
%define files_handle_flags 0x7b2b
%define files_overlay_cookie 0x8e24
%define files_overlay_callback 0x8e26
%define files_error_value 0x9435
%define files_stack_failure 0xa8bc
%define files_stack_available 0xa8d4
%endif
%include "encodings.inc"
files_write: push bp
files_at_a369: mov_load bp,sp
files_at_a36b: sub sp,0x8
files_at_a36e: mov bx,[bp+0x4]
files_at_a371: cmp bx,[files_handle_limit]
files_at_a375: jc short files_at_a37e
files_at_a377: mov ax,0x900
files_at_a37a: stc
files_at_a37b: jmp near files_error_value
files_at_a37e: cmp word [files_overlay_cookie],0xd6d6
files_at_a384: jnz short files_at_a38a
files_at_a386: call word near [files_overlay_callback]
files_at_a38a: test byte [bx+files_handle_flags],0x20
files_at_a38f: jz short files_at_a39c
files_at_a391: mov ax,0x4202
files_at_a394: xor_load cx,cx
files_at_a396: mov_load dx,cx
files_at_a398: int byte 0x21
files_at_a39a: jc short files_at_a37b
files_at_a39c: test byte [bx+files_handle_flags],0x80
files_at_a3a1: jz short files_at_a411
files_at_a3a3: mov dx,[bp+0x6]
files_at_a3a6: push ds
files_at_a3a7: pop es
files_at_a3a8: xor_load ax,ax
files_at_a3aa: mov [bp-0x2],ax
files_at_a3ad: mov [bp-0x4],ax
files_at_a3b0: cld
files_at_a3b1: push di
files_at_a3b2: push si
files_at_a3b3: mov_load di,dx
files_at_a3b5: mov_load si,dx
files_at_a3b7: mov [bp-0x8],sp
files_at_a3ba: mov cx,[bp+0x8]
files_at_a3bd: jcxz files_at_a3f7
files_at_a3bf: mov al,0xa
files_at_a3c1: repne scasb
files_at_a3c3: jnz short files_at_a40f
files_at_a3c5: call files_stack_available
files_at_a3c8: cmp ax,0xa8
files_at_a3cb: jna short files_at_a413
files_at_a3cd: sub sp,0x2
files_at_a3d0: mov_load bx,sp
files_at_a3d2: mov dx,0x200
files_at_a3d5: cmp ax,0x228
files_at_a3d8: jnc short files_at_a3dd
files_at_a3da: mov dx,0x80
files_at_a3dd: sub_load sp,dx
files_at_a3df: mov_load dx,sp
files_at_a3e1: mov_load di,dx
files_at_a3e3: push ss
files_at_a3e4: pop es
files_at_a3e5: mov cx,[bp+0x8]
files_at_a3e8: lodsb
files_at_a3e9: cmp al,0xa
files_at_a3eb: jz short files_at_a3f9
files_at_a3ed: cmp_load di,bx
files_at_a3ef: jz short files_at_a40a
files_at_a3f1: stosb
files_at_a3f2: loop files_at_a3e8
files_at_a3f4: call files_at_a419
files_at_a3f7: jmp short files_at_a463
files_at_a3f9: mov al,0xd
files_at_a3fb: cmp_load di,bx
files_at_a3fd: jnz short files_at_a402
files_at_a3ff: call files_at_a419
files_at_a402: stosb
files_at_a403: mov al,0xa
files_at_a405: inc word [bp-0x4]
files_at_a408: jmp short files_at_a3ed
files_at_a40a: call files_at_a419
files_at_a40d: jmp short files_at_a3f1
files_at_a40f: pop si
files_at_a410: pop di
files_at_a411: jmp short files_at_a471
files_at_a413: mov ax,0xfffc
files_at_a416: call files_stack_failure
files_at_a419: push ax
files_at_a41a: push bx
files_at_a41b: push cx
files_at_a41c: mov_load cx,di
files_at_a41e: sub_load cx,dx
files_at_a420: jcxz files_at_a434
files_at_a422: push cx
files_at_a423: mov bx,[bp+0x4]
files_at_a426: mov ah,0x40
files_at_a428: int byte 0x21
files_at_a42a: pop cx
files_at_a42b: jc short files_at_a43a
files_at_a42d: add [bp-0x2],ax
files_at_a430: cmp_load cx,ax
files_at_a432: ja short files_at_a43a
files_at_a434: pop cx
files_at_a435: pop bx
files_at_a436: pop ax
files_at_a437: mov_load di,dx
files_at_a439: ret
files_at_a43a: lahf
files_at_a43b: add sp,0x8
files_at_a43e: cmp word [bp-0x2],0x0
files_at_a442: jnz short files_at_a463
files_at_a444: sahf
files_at_a445: jnc short files_at_a44b
files_at_a447: mov ah,0x9
files_at_a449: jmp short files_at_a469
files_at_a44b: test byte [bx+files_handle_flags],0x40
files_at_a450: jz short files_at_a45d
files_at_a452: mov bx,[bp+0x6]
files_at_a455: cmp byte [bx],0x1a
files_at_a458: jnz short files_at_a45d
files_at_a45a: clc
files_at_a45b: jmp short files_at_a469
files_at_a45d: stc
files_at_a45e: mov ax,0x1c00
files_at_a461: jmp short files_at_a469
files_at_a463: mov ax,[bp-0x2]
files_at_a466: sub ax,[bp-0x4]
files_at_a469: mov sp,[bp-0x8]
files_at_a46c: pop si
files_at_a46d: pop di
files_at_a46e: jmp near files_error_value
files_at_a471: mov cx,[bp+0x8]
files_at_a474: or_load cx,cx
files_at_a476: jnz short files_at_a47d
files_at_a478: mov_load ax,cx
files_at_a47a: jmp near files_error_value
files_at_a47d: mov dx,[bp+0x6]
files_at_a480: mov ah,0x40
files_at_a482: int byte 0x21
files_at_a484: jnc short files_at_a48a
files_at_a486: mov ah,0x9
files_at_a488: jmp short files_at_a46e
files_at_a48a: or_load ax,ax
files_at_a48c: jnz short files_at_a46e
files_at_a48e: test byte [bx+files_handle_flags],0x40
files_at_a493: jz short files_at_a49f
files_at_a495: mov_load bx,dx
files_at_a497: cmp byte [bx],0x1a
files_at_a49a: jnz short files_at_a49f
files_at_a49c: clc
files_at_a49d: jmp short files_at_a46e
files_at_a49f: stc
files_at_a4a0: mov ax,0x1c00
files_at_a4a3: jmp short files_at_a46e
files_at_a4a5: db 0x00
