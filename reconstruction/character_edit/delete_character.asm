; Recovered PCPlus 2.01 character editing instructions; see docs/CHARACTER_EDIT.md.
BITS 16
CPU 8086
%ifdef CHARACTER_EDIT_OMF
SEGMENT _TEXT public class=CODE use16
global csi_delete_character
extern character_cga_restore
extern character_cga_disable
extern erase_far_move
extern erase_move_bytes
extern erase_repair_attributes
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
extern csi_wrap_pending
extern attributes_normal_value
extern erase_attribute_values_base
extern erase_shadow_offset
extern erase_shadow_segment
extern text_video_segment
%define short
%else
ORG 0xd440
%define character_cga_restore 0x77ae
%define character_cga_disable 0x77be
%define erase_far_move 0x6412
%define erase_move_bytes 0x85b4
%define erase_repair_attributes 0x2d98
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
%define csi_wrap_pending 0x3342
%define attributes_normal_value 0x1d32
%define erase_attribute_values_base 0x39c2
%define erase_shadow_offset 0x5dea
%define erase_shadow_segment 0x5dec
%define text_video_segment 0x7a78
%endif
%include "encodings.inc"
csi_delete_character:
L_d440: push bp
L_d441: mov_load bp,sp
L_d443: sub sp,0x1a
L_d446: push di
L_d447: push si
L_d448: mov word [csi_wrap_pending],0x0
L_d44e: mov bx,[screen_attribute_offset]
L_d452: mov si,[screen_cursor_row]
L_d456: test byte [si+screen_line_flags],0x40
L_d45b: jz short L_d46a
L_d45d: mov word [bp-0x2],0x2
L_d462: mov word [bp-0xe],0x1
L_d467: jmp short L_d472
L_d469: nop
L_d46a: sub_load ax,ax
L_d46c: mov [bp-0xe],ax
L_d46f: mov [bp-0x2],ax
L_d472: cmp word [screen_attribute_checks],0x0
L_d477: jz short L_d4aa
L_d479: mov di,[screen_cursor_column]
L_d47d: cmp di,[screen_last_column]
L_d481: jnc short L_d497
L_d483: mov si,[screen_attributes_base]
L_d487: test byte [bx+si],0x81
L_d48a: jnz short L_d496
L_d48c: inc bx
L_d48d: inc di
L_d48e: cmp [screen_last_column],di
L_d492: ja short L_d483
L_d494: jmp short L_d497
L_d496: dec di
L_d497: mov [bp-0xc],bx
L_d49a: mov ax,[screen_cursor_column]
L_d49d: sub_load ax,di
L_d49f: dec ax
L_d4a0: jnz short L_d4a5
L_d4a2: jmp near L_d662
L_d4a5: mov_load si,di
L_d4a7: jmp short L_d4b1
L_d4a9: nop
L_d4aa: mov [bp-0xc],bx
L_d4ad: mov si,[screen_last_column]
L_d4b1: cmp word [screen_viewport_active],0x0
L_d4b6: jz short L_d4c6
L_d4b8: mov di,[screen_viewport_right]
L_d4bc: sub_load di,si
L_d4be: sbb_load ax,ax
L_d4c0: and_load di,ax
L_d4c2: add_load di,si
L_d4c4: jmp short L_d4c8
L_d4c6: mov_load di,si
L_d4c8: sub di,[screen_cursor_column]
L_d4cc: call character_cga_disable
L_d4cf: mov ax,[text_video_segment]
L_d4d2: sub_load cx,cx
L_d4d4: mov [bp-0x16],cx
L_d4d7: mov [bp-0x14],ax
L_d4da: mov cx,[screen_video_offset]
L_d4de: push ax
L_d4df: push cx
L_d4e0: mov_load ax,cx
L_d4e2: add ax,[bp-0x2]
L_d4e5: inc ax
L_d4e6: inc ax
L_d4e7: or ax,[bp-0x16]
L_d4ea: mov dx,[bp-0x14]
L_d4ed: push dx
L_d4ee: push ax
L_d4ef: sub di,[bp-0xe]
L_d4f2: push di
L_d4f3: call erase_far_move
L_d4f6: cmp word [screen_viewport_active],0x0
L_d4fb: jnz short L_d500
L_d4fd: jmp near L_d5a6
L_d500: cmp [screen_viewport_right],si
L_d504: jc short L_d509
L_d506: jmp near L_d5a6
L_d509: mov ax,[bp-0xe]
L_d50c: shl ax,1
L_d50e: mov bx,[screen_columns]
L_d512: sub bx,[screen_cursor_column]
L_d516: add bx,[screen_attribute_offset]
L_d51a: shl bx,1
L_d51c: add bx,[erase_shadow_offset]
L_d520: mov es,word [erase_shadow_segment]
L_d524: mov_load di,bx
L_d526: mov word [bp-0x10],es
L_d529: add_load bx,ax
L_d52b: mov ax,[es:bx]
L_d52e: mov cx,[screen_viewport_right]
L_d532: sub cx,[screen_cursor_column]
L_d536: shl cx,1
L_d538: add cx,[screen_video_offset]
L_d53c: mov_load bx,cx
L_d53e: mov cx,[text_video_segment]
L_d542: mov es,cx
L_d544: mov [es:bx],ax
L_d547: cmp word [bp-0xe],0x0
L_d54b: jz short L_d56d
L_d54d: mov es,word [bp-0x10]
L_d550: mov ax,[es:di]
L_d553: mov cx,[screen_viewport_right]
L_d557: sub cx,[screen_cursor_column]
L_d55b: dec cx
L_d55c: shl cx,1
L_d55e: add cx,[screen_video_offset]
L_d562: mov_load bx,cx
L_d564: mov cx,[text_video_segment]
L_d568: mov es,cx
L_d56a: mov [es:bx],ax
L_d56d: mov ax,[bp-0x10]
L_d570: push ax
L_d571: push di
L_d572: mov cx,[bp-0xe]
L_d575: shl cx,1
L_d577: mov [bp-0x1a],di
L_d57a: mov [bp-0x18],ax
L_d57d: add_load di,cx
L_d57f: inc di
L_d580: inc di
L_d581: push ax
L_d582: push di
L_d583: mov_load ax,si
L_d585: sub ax,[bp-0xe]
L_d588: sub ax,[screen_columns]
L_d58c: push ax
L_d58d: call erase_far_move
L_d590: mov_load ax,si
L_d592: sub ax,[screen_columns]
L_d596: shl ax,1
L_d598: add ax,[bp-0x1a]
L_d59b: mov dx,[bp-0x18]
L_d59e: mov [bp-0x6],dx
L_d5a1: mov_load di,ax
L_d5a3: jmp short L_d5bb
L_d5a5: nop
L_d5a6: mov_load ax,si
L_d5a8: sub ax,[screen_cursor_column]
L_d5ac: shl ax,1
L_d5ae: add ax,[screen_video_offset]
L_d5b2: mov dx,[text_video_segment]
L_d5b6: mov_load di,ax
L_d5b8: mov [bp-0x6],dx
L_d5bb: mov es,word [bp-0x6]
L_d5be: mov byte [es:di],0x20
L_d5c2: cmp word [screen_cursor_wrap],0x0
L_d5c7: jz short L_d5da
L_d5c9: mov bx,[screen_attribute_offset]
L_d5cd: sub bx,[screen_cursor_column]
L_d5d1: add bx,[erase_attribute_values_base]
L_d5d5: mov al,[bx+si]
L_d5d7: jmp short L_d5dd
L_d5d9: nop
L_d5da: mov al,[attributes_normal_value]
L_d5dd: mov es,word [bp-0x6]
L_d5e0: mov [es:di+0x1],al
L_d5e4: cmp word [bp-0xe],0x0
L_d5e8: jz short L_d5f9
L_d5ea: mov es,word [bp-0x6]
L_d5ed: mov byte [es:di-0x2],0x20
L_d5f2: mov al,[attributes_normal_value]
L_d5f5: mov [es:di-0x1],al
L_d5f9: call character_cga_restore
L_d5fc: cmp word [screen_cursor_wrap],0x0
L_d601: jz short L_d662
L_d603: cmp word [screen_attribute_checks],0x0
L_d608: jnz short L_d662
L_d60a: mov bx,[bp-0xc]
L_d60d: add bx,[screen_attributes_base]
L_d611: mov al,[bx]
L_d613: and ax,0x80
L_d616: mov_load di,ax
L_d618: mov_load ax,si
L_d61a: sub si,[screen_cursor_column]
L_d61e: push si
L_d61f: lea cx,[bx+0x1]
L_d622: push cx
L_d623: push bx
L_d624: mov_load si,ax
L_d626: call erase_move_bytes
L_d629: add sp,0x6
L_d62c: mov_load ax,si
L_d62e: sub si,[screen_cursor_column]
L_d632: push si
L_d633: mov cx,[bp-0xc]
L_d636: add cx,[erase_attribute_values_base]
L_d63a: mov_load dx,cx
L_d63c: inc cx
L_d63d: push cx
L_d63e: push dx
L_d63f: mov_load si,ax
L_d641: call erase_move_bytes
L_d644: add sp,0x6
L_d647: mov_load bx,si
L_d649: sub bx,[screen_cursor_column]
L_d64d: add bx,[bp-0xc]
L_d650: mov si,[screen_attributes_base]
L_d654: and byte [bx+si],0xfe
L_d657: or_load di,di
L_d659: jz short L_d662
L_d65b: mov ax,0x2
L_d65e: push ax
L_d65f: call erase_repair_attributes
L_d662: pop si
L_d663: pop di
L_d664: mov_load sp,bp
L_d666: pop bp
L_d667: ret
