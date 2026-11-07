; Recovered 2.01 Meta Keys component; external UI boundaries remain explicit.
BITS 16
CPU 8086
%ifdef META_EDITOR_OMF
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
global meta_editor_row
extern meta_editor_attribute:wrt DGROUP
extern meta_editor_edit_next:wrt DGROUP
extern meta_editor_edit_previous:wrt DGROUP
extern meta_editor_field_next:wrt DGROUP
extern meta_editor_field_previous:wrt DGROUP
extern meta_editor_kind_format:wrt DGROUP
extern meta_editor_kind_labels:wrt DGROUP
extern meta_editor_records:wrt DGROUP
%define meta_editor_text (meta_editor_records+2)
extern meta_editor_wait_active:wrt DGROUP
extern meta_editor_wait_default:wrt DGROUP
extern meta_editor_inverse
extern meta_editor_cursor
extern meta_editor_read_key
extern meta_editor_edit_text
extern meta_editor_draw_kind
extern meta_editor_field_key
%else
ORG 58004
%define meta_editor_attribute 0x1f7c
%define meta_editor_wait_default 0x2068
%define meta_editor_kind_labels 0x2290
%define meta_editor_records 0x3756
%define meta_editor_text 0x3758
%define meta_editor_field_previous 0x5df4
%define meta_editor_field_next 0x5df8
%define meta_editor_edit_previous 0x5e00
%define meta_editor_edit_next 0x5e04
%define meta_editor_kind_format 0x6644
%define meta_editor_wait_active 0x7a50
%define meta_editor_inverse 0x4a04
%define meta_editor_cursor 0x6e66
%define meta_editor_read_key 0x7878
%define meta_editor_edit_text 0x7880
%define meta_editor_draw_kind 0x75e8
%define meta_editor_field_key 0xe261
%endif
%include "encodings.inc"
meta_editor_row:
L_e294: push bp
L_e295: mov_load bp,sp
L_e297: sub sp,0xe
L_e29a: push di
L_e29b: mov ax,[meta_editor_field_previous]
L_e29e: mov [bp-0xe],ax
L_e2a1: mov ax,[meta_editor_field_next]
L_e2a4: mov [bp-0x8],ax
L_e2a7: mov ax,[meta_editor_edit_previous]
L_e2aa: mov [bp-0xa],ax
L_e2ad: mov ax,[meta_editor_edit_next]
L_e2b0: mov [bp-0xc],ax
L_e2b3: mov ax,0xf00
L_e2b6: mov [meta_editor_edit_previous],ax
L_e2b9: mov [meta_editor_field_previous],ax
L_e2bc: mov ax,0x9
L_e2bf: mov [meta_editor_edit_next],ax
L_e2c2: mov [meta_editor_field_next],ax
L_e2c5: mov ax,0x36
L_e2c8: imul word [bp+0x4]
L_e2cb: mov_load bx,ax
L_e2cd: mov ax,[bx+meta_editor_records]
L_e2d1: mov [bp-0x2],ax
L_e2d4: push word [meta_editor_attribute]
L_e2d8: call meta_editor_inverse
L_e2db: pop bx
L_e2dc: mov [bp-0x4],ax
L_e2df: mov ax,[bp+0x4]
L_e2e2: add ax,strict word 0x6
L_e2e5: mov [bp-0x6],ax
L_e2e8: mov ax,[bp+0x4]
L_e2eb: add ax,strict word 0x6
L_e2ee: push ax
L_e2ef: mov ax,0x11
L_e2f2: push ax
L_e2f3: call meta_editor_cursor
L_e2f6: mov word [meta_editor_wait_active],0x2710
L_e2fc: call meta_editor_read_key
L_e2ff: mov_load di,ax
L_e301: mov ax,[meta_editor_wait_default]
L_e304: mov [meta_editor_wait_active],ax
L_e307: mov_load ax,di
L_e309: sub ax,strict word 0x9
L_e30c: jz short L_e32a
L_e30e: sub ax,strict word 0x4
L_e311: jz short L_e32a
L_e313: sub ax,strict word 0xe
L_e316: jz short L_e386
L_e318: sub ax,0xee5
L_e31b: jz short L_e377
L_e31d: cmp word [bp-0x2],0x3
L_e321: jl short L_e355
L_e323: mov word [bp-0x2],0x0
L_e328: jmp short L_e358
L_e32a: mov al,0x19
L_e32c: mov ah,[bp-0x6]
L_e32f: push ax
L_e330: push word [bp-0x4]
L_e333: mov ax,0x36
L_e336: imul word [bp+0x4]
L_e339: add ax,meta_editor_text
L_e33c: push ax
L_e33d: push ax
L_e33e: mov ax,0x32
L_e341: push ax
L_e342: mov ax,meta_editor_field_key
L_e345: push ax
L_e346: call meta_editor_edit_text
L_e349: mov_load di,ax
L_e34b: inc ax
L_e34c: jz short L_e386
L_e34e: sub ax,0xf01
L_e351: jz short L_e2e8
L_e353: jmp short L_e377
L_e355: inc word [bp-0x2]
L_e358: mov bx,[bp-0x2]
L_e35b: shl bx,1
L_e35d: push word [bx+meta_editor_kind_labels]
L_e361: mov ax,meta_editor_kind_format
L_e364: push ax
L_e365: push word [bp-0x4]
L_e368: mov al,0x11
L_e36a: mov ah,[bp-0x6]
L_e36d: push ax
L_e36e: call meta_editor_draw_kind
L_e371: add sp,0x8
L_e374: jmp near L_e2e8
L_e377: mov ax,0x36
L_e37a: imul word [bp+0x4]
L_e37d: mov_load bx,ax
L_e37f: mov ax,[bp-0x2]
L_e382: mov [bx+meta_editor_records],ax
L_e386: mov ax,[bp-0xe]
L_e389: mov [meta_editor_field_previous],ax
L_e38c: mov ax,[bp-0x8]
L_e38f: mov [meta_editor_field_next],ax
L_e392: mov ax,[bp-0xa]
L_e395: mov [meta_editor_edit_previous],ax
L_e398: mov ax,[bp-0xc]
L_e39b: mov [meta_editor_edit_next],ax
L_e39e: mov_load ax,di
L_e3a0: pop di
L_e3a1: mov_load sp,bp
L_e3a3: pop bp
L_e3a4: ret
%ifdef META_EDITOR_OMF
SEGMENT _DATA public class=DATA use16
%endif
