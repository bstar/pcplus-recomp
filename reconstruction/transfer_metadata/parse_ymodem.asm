; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_parse_ymodem
global metadata_at_e52b
global metadata_at_e52d
global metadata_at_e531
global metadata_at_e532
global metadata_at_e533
global metadata_at_e535
global metadata_at_e538
global metadata_at_e53c
global metadata_at_e53f
global metadata_at_e541
global metadata_at_e544
global metadata_at_e546
global metadata_at_e548
global metadata_at_e54a
global metadata_at_e54b
global metadata_at_e54f
global metadata_at_e550
global metadata_at_e553
global metadata_at_e555
global metadata_at_e559
global metadata_at_e55c
global metadata_at_e55e
global metadata_at_e561
global metadata_at_e563
global metadata_at_e565
global metadata_at_e567
global metadata_at_e568
global metadata_at_e56c
global metadata_at_e56d
global metadata_at_e570
global metadata_at_e572
global metadata_at_e575
global metadata_at_e576
global metadata_at_e57a
global metadata_at_e57d
global metadata_at_e57f
global metadata_at_e585
global metadata_at_e586
global metadata_at_e587
global metadata_at_e589
global metadata_at_e58a
global metadata_at_e58b
global metadata_at_e58c
global metadata_at_e58e
global metadata_at_e58f
global metadata_at_e591
global metadata_at_e593
global metadata_at_e596
global metadata_at_e59a
global metadata_at_e59d
global metadata_at_e59f
global metadata_at_e5a2
global metadata_at_e5a4
global metadata_at_e5a6
global metadata_at_e5a8
global metadata_at_e5a9
global metadata_at_e5aa
global metadata_at_e5ad
global metadata_at_e5af
global metadata_at_e5b0
global metadata_at_e5b1
global metadata_at_e5b3
global metadata_at_e5b4
global metadata_at_e5b5
global metadata_at_e5b6
global metadata_at_e5b9
global metadata_at_e5bc
global metadata_at_e5bd
global metadata_at_e5c0
global metadata_at_e5c3
global metadata_at_e5c6
global metadata_at_e5ca
global metadata_at_e5cc
global metadata_at_e5cd
global metadata_at_e5d0
global metadata_at_e5d3
global metadata_at_e5d4
global metadata_at_e5d5
global metadata_at_e5d7
global metadata_at_e5d8
extern metadata_buffer_pointer
extern metadata_size_low
extern metadata_size_high
extern metadata_decimal_thunk
extern metadata_batch_end
extern metadata_filename
extern metadata_display_start
%else
ORG 0xe52a
%define metadata_buffer_pointer 0x39c0
%define metadata_size_low 0x9006
%define metadata_size_high 0x9008
%define metadata_decimal_thunk 0x9b32
%define metadata_batch_end 0xcb56
%define metadata_filename 0xcb68
%define metadata_display_start 0xee10
%endif
%include "encodings.inc"
metadata_parse_ymodem: push bp
metadata_at_e52b: mov_load bp,sp
metadata_at_e52d: sub sp,0x80
metadata_at_e531: push di
metadata_at_e532: push si
metadata_at_e533: sub_load si,si
metadata_at_e535: mov di,metadata_filename
metadata_at_e538: mov bx,[metadata_buffer_pointer]
metadata_at_e53c: cmp byte [bx],0x0
metadata_at_e53f: jz short metadata_at_e555
metadata_at_e541: cmp si,0x41
metadata_at_e544: jnl short metadata_at_e555
metadata_at_e546: mov al,[bx+si]
metadata_at_e548: mov [di],al
metadata_at_e54a: inc di
metadata_at_e54b: mov bx,[metadata_buffer_pointer]
metadata_at_e54f: inc si
metadata_at_e550: cmp byte [bx+si],0x0
metadata_at_e553: jnz short metadata_at_e541
metadata_at_e555: mov bx,[metadata_buffer_pointer]
metadata_at_e559: cmp byte [bx+si],0x0
metadata_at_e55c: jz short metadata_at_e572
metadata_at_e55e: cmp si,0x41
metadata_at_e561: jnl short metadata_at_e572
metadata_at_e563: mov al,[bx+si]
metadata_at_e565: mov [di],al
metadata_at_e567: inc di
metadata_at_e568: mov bx,[metadata_buffer_pointer]
metadata_at_e56c: inc si
metadata_at_e56d: cmp byte [bx+si],0x0
metadata_at_e570: jnz short metadata_at_e55e
metadata_at_e572: mov byte [di],0x0
metadata_at_e575: inc si
metadata_at_e576: mov bx,[metadata_buffer_pointer]
metadata_at_e57a: cmp byte [bx],0x0
metadata_at_e57d: jnz short metadata_at_e58c
metadata_at_e57f: mov word [metadata_batch_end],0x1
metadata_at_e585: pop si
metadata_at_e586: pop di
metadata_at_e587: mov_load sp,bp
metadata_at_e589: pop bp
metadata_at_e58a: ret
metadata_at_e58b: nop
metadata_at_e58c: mov al,[bx+si]
metadata_at_e58e: cbw
metadata_at_e58f: or_load ax,ax
metadata_at_e591: jz short metadata_at_e5d3
metadata_at_e593: lea di,[bp-0x80]
metadata_at_e596: mov bx,[metadata_buffer_pointer]
metadata_at_e59a: cmp byte [bx+si],0x20
metadata_at_e59d: jz short metadata_at_e5b6
metadata_at_e59f: cmp byte [bx+si],0x0
metadata_at_e5a2: jz short metadata_at_e5b6
metadata_at_e5a4: mov al,[bx+si]
metadata_at_e5a6: mov [di],al
metadata_at_e5a8: inc di
metadata_at_e5a9: inc si
metadata_at_e5aa: cmp si,0x78
metadata_at_e5ad: jng short metadata_at_e596
metadata_at_e5af: pop si
metadata_at_e5b0: pop di
metadata_at_e5b1: mov_load sp,bp
metadata_at_e5b3: pop bp
metadata_at_e5b4: ret
metadata_at_e5b5: nop
metadata_at_e5b6: mov byte [di],0x0
metadata_at_e5b9: lea ax,[bp-0x80]
metadata_at_e5bc: push ax
metadata_at_e5bd: call metadata_decimal_thunk
metadata_at_e5c0: add sp,0x2
metadata_at_e5c3: mov [metadata_size_low],ax
metadata_at_e5c6: mov [metadata_size_high],dx
metadata_at_e5ca: sub_load ax,ax
metadata_at_e5cc: push ax
metadata_at_e5cd: call metadata_display_start
metadata_at_e5d0: add sp,0x2
metadata_at_e5d3: pop si
metadata_at_e5d4: pop di
metadata_at_e5d5: mov_load sp,bp
metadata_at_e5d7: pop bp
metadata_at_e5d8: ret
