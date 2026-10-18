; Recovered PCPlus 2.01 character editing instructions; see docs/CHARACTER_EDIT.md.
BITS 16
CPU 8086
%ifdef CHARACTER_EDIT_OMF
SEGMENT _TEXT public class=CODE use16
global csi_insert_character
extern character_cga_restore
extern character_cga_disable
extern erase_far_move
extern erase_move_bytes
extern text_write_char
extern screen_viewport_active
extern screen_viewport_right
extern screen_video_offset
extern screen_attribute_offset
extern screen_cursor_column
extern screen_cursor_row
extern screen_attribute_checks
extern screen_attributes_base
extern screen_last_column
extern screen_line_flags
extern screen_cursor_wrap
extern screen_columns
extern erase_attribute_values_base
extern erase_shadow_offset
extern erase_shadow_segment
extern text_video_segment
%define short
%else
ORG 0xd270
%define character_cga_restore 0x77ae
%define character_cga_disable 0x77be
%define erase_far_move 0x6412
%define erase_move_bytes 0x85b4
%define text_write_char 0x6c84
%define screen_viewport_active 0x3256
%define screen_viewport_right 0x7a7e
%define screen_video_offset 0x3344
%define screen_attribute_offset 0x3346
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_attribute_checks 0x3734
%define screen_attributes_base 0x39c4
%define screen_last_column 0x3258
%define screen_line_flags 0xcf86
%define screen_cursor_wrap 0x900c
%define screen_columns 0x7a72
%define erase_attribute_values_base 0x39c2
%define erase_shadow_offset 0x5dea
%define erase_shadow_segment 0x5dec
%define text_video_segment 0x7a78
%endif
%include "encodings.inc"
csi_insert_character:
L_d270: push bp
L_d271: mov_load bp,sp
L_d273: sub sp,0x14
L_d276: push di
L_d277: push si
L_d278: mov ax,[screen_attribute_offset]
L_d27b: mov [bp-0xa],ax
L_d27e: mov bx,[screen_cursor_row]
L_d282: test byte [bx+screen_line_flags],0x40
L_d287: jz short L_d294
L_d289: mov word [bp-0xc],0x2
L_d28e: mov si,0x1
L_d291: jmp short L_d299
L_d293: nop
L_d294: sub_load si,si
L_d296: mov [bp-0xc],si
L_d299: mov ax,[screen_last_column]
L_d29c: cmp [screen_cursor_column],ax
L_d2a0: jc short L_d2a5
L_d2a2: jmp near L_d3f6
L_d2a5: cmp word [screen_attribute_checks],0x0
L_d2aa: jz short L_d2e8
L_d2ac: mov [bp-0xe],si
L_d2af: mov ax,[screen_cursor_column]
L_d2b2: mov_load di,ax
L_d2b4: cmp ax,[screen_last_column]
L_d2b8: jnc short L_d2d8
L_d2ba: mov bx,[bp-0xa]
L_d2bd: mov si,[screen_attributes_base]
L_d2c1: test byte [bx+si],0x81
L_d2c4: jnz short L_d2d4
L_d2c6: inc bx
L_d2c7: inc di
L_d2c8: cmp [screen_last_column],di
L_d2cc: ja short L_d2bd
L_d2ce: mov [bp-0xa],bx
L_d2d1: jmp short L_d2d8
L_d2d3: nop
L_d2d4: mov [bp-0xa],bx
L_d2d7: dec di
L_d2d8: mov ax,[screen_cursor_column]
L_d2db: sub_load ax,di
L_d2dd: dec ax
L_d2de: jnz short L_d2e3
L_d2e0: jmp near L_d43a
L_d2e3: mov si,[bp-0xe]
L_d2e6: jmp short L_d2ea
L_d2e8: mov_load di,ax
L_d2ea: call character_cga_disable
L_d2ed: cmp word [screen_viewport_active],0x0
L_d2f2: jnz short L_d2f7
L_d2f4: jmp near L_d386
L_d2f7: cmp [screen_viewport_right],di
L_d2fb: jnc short L_d379
L_d2fd: mov ax,[screen_columns]
L_d300: sub ax,[screen_cursor_column]
L_d304: add ax,[screen_attribute_offset]
L_d308: shl ax,1
L_d30a: add ax,[erase_shadow_offset]
L_d30e: mov dx,[erase_shadow_segment]
L_d312: mov [bp-0x8],ax
L_d315: mov [bp-0x6],dx
L_d318: mov_load cx,si
L_d31a: shl cx,1
L_d31c: add_load ax,cx
L_d31e: inc ax
L_d31f: inc ax
L_d320: push dx
L_d321: push ax
L_d322: push dx
L_d323: push word [bp-0x8]
L_d326: mov_load ax,di
L_d328: sub ax,[screen_columns]
L_d32c: sub_load ax,si
L_d32e: push ax
L_d32f: mov [bp-0x10],cx
L_d332: call erase_far_move
L_d335: mov ax,[screen_viewport_right]
L_d338: sub ax,[screen_cursor_column]
L_d33c: shl ax,1
L_d33e: add ax,[screen_video_offset]
L_d342: mov_load bx,ax
L_d344: mov cx,[text_video_segment]
L_d348: mov es,cx
L_d34a: mov ax,[es:bx]
L_d34d: les bx,word [bp-0x8]
L_d350: add bx,[bp-0x10]
L_d353: mov [es:bx],ax
L_d356: or_load si,si
L_d358: jz short L_d379
L_d35a: mov ax,[screen_viewport_right]
L_d35d: sub ax,[screen_cursor_column]
L_d361: dec ax
L_d362: shl ax,1
L_d364: add ax,[screen_video_offset]
L_d368: mov_load bx,ax
L_d36a: mov cx,[text_video_segment]
L_d36e: mov es,cx
L_d370: mov ax,[es:bx]
L_d373: les bx,word [bp-0x8]
L_d376: mov [es:bx],ax
L_d379: mov ax,[screen_viewport_right]
L_d37c: sub_load ax,di
L_d37e: sbb_load cx,cx
L_d380: and_load ax,cx
L_d382: add_load ax,di
L_d384: jmp short L_d388
L_d386: mov_load ax,di
L_d388: sub ax,[screen_cursor_column]
L_d38c: mov [bp-0x2],ax
L_d38f: mov ax,[screen_video_offset]
L_d392: add ax,[bp-0xc]
L_d395: inc ax
L_d396: inc ax
L_d397: mov cx,[text_video_segment]
L_d39b: sub_load bx,bx
L_d39d: mov [bp-0x14],bx
L_d3a0: mov_load bx,ax
L_d3a2: push cx
L_d3a3: push bx
L_d3a4: mov ax,[screen_video_offset]
L_d3a7: or ax,[bp-0x14]
L_d3aa: mov_load dx,cx
L_d3ac: push dx
L_d3ad: push ax
L_d3ae: mov ax,[bp-0x2]
L_d3b1: sub_load ax,si
L_d3b3: push ax
L_d3b4: call erase_far_move
L_d3b7: call character_cga_restore
L_d3ba: cmp word [screen_cursor_wrap],0x0
L_d3bf: jz short L_d3f6
L_d3c1: cmp word [screen_attribute_checks],0x0
L_d3c6: jnz short L_d3f6
L_d3c8: mov_load ax,di
L_d3ca: sub di,[screen_cursor_column]
L_d3ce: push di
L_d3cf: mov cx,[screen_attributes_base]
L_d3d3: add cx,[bp-0xa]
L_d3d6: push cx
L_d3d7: inc cx
L_d3d8: push cx
L_d3d9: mov_load di,ax
L_d3db: call erase_move_bytes
L_d3de: add sp,0x6
L_d3e1: sub di,[screen_cursor_column]
L_d3e5: push di
L_d3e6: mov ax,[bp-0xa]
L_d3e9: add ax,[erase_attribute_values_base]
L_d3ed: push ax
L_d3ee: inc ax
L_d3ef: push ax
L_d3f0: call erase_move_bytes
L_d3f3: add sp,0x6
L_d3f6: cmp word [screen_cursor_wrap],0x0
L_d3fb: jz short L_d41e
L_d3fd: cmp word [screen_attribute_checks],0x0
L_d402: jnz short L_d41e
L_d404: mov bx,[screen_attributes_base]
L_d408: mov di,[bp-0xa]
L_d40b: and byte [bx+di],0xfe
L_d40e: mov bx,[erase_attribute_values_base]
L_d412: mov al,[bx+di]
L_d414: cbw
L_d415: push ax
L_d416: mov ax,[screen_video_offset]
L_d419: inc ax
L_d41a: push ax
L_d41b: call text_write_char
L_d41e: mov ax,0x20
L_d421: push ax
L_d422: push word [screen_video_offset]
L_d426: call text_write_char
L_d429: or_load si,si
L_d42b: jz short L_d43a
L_d42d: mov ax,0x20
L_d430: push ax
L_d431: mov ax,[screen_video_offset]
L_d434: inc ax
L_d435: inc ax
L_d436: push ax
L_d437: call text_write_char
L_d43a: pop si
L_d43b: pop di
L_d43c: mov_load sp,bp
L_d43e: pop bp
L_d43f: ret
