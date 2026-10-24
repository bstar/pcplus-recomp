; Native far shadow/video copy, CS:644c..64b8.
BITS 16
CPU 8086
%ifdef VIEWPORT_OMF
SEGMENT _TEXT public class=CODE use16
global viewport_copy
extern viewport_physical_columns,viewport_rows,screen_viewport_left
extern text_video_segment,erase_shadow_offset,erase_shadow_segment
extern ui_cga_blank,ui_cga_unblank
%else
ORG 0x644c
%define viewport_physical_columns 0x7a72
%define viewport_rows 0x7a74
%define screen_viewport_left 0xce2e
%define text_video_segment 0x7a78
%define erase_shadow_offset 0x5dea
%define erase_shadow_segment 0x5dec
%define ui_cga_blank 0x77be
%define ui_cga_unblank 0x77ae
%endif
%include "encodings.inc"
viewport_copy:
 mov_load bx,sp
 push bp
 push ds
 push di
 push si
 call ui_cga_blank
 mov bp,[viewport_physical_columns]
 mov ax,[screen_viewport_left]
 shl ax,1
 mov bx,[bx+2]
 mov_load cx,bx
 and cx,1
 jz short .left
 mov_load cx,ax
 jmp short .selected
 nop
.left:
 sub_load cx,cx
.selected:
 mov dx,[viewport_rows]
 and bx,0x8000
 jz short .save
 mov es,[text_video_segment]
 sub_load di,di
 mov si,[erase_shadow_offset]
 add_load si,cx
 mov ds,[erase_shadow_segment]
.restore_row:
 mov_load cx,bp
 rep movsw
 add_load si,ax
 dec dx
 jnz short .restore_row
 jmp short .done
 nop
.save:
 mov es,[erase_shadow_segment]
 mov di,[erase_shadow_offset]
 add_load di,cx
 sub_load si,si
 mov ds,[text_video_segment]
.save_row:
 mov_load cx,bp
 rep movsw
 add_load di,ax
 dec dx
 jnz short .save_row
.done:
%ifndef VIEWPORT_PRESERVE_DS
 call ui_cga_unblank
%endif
 pop si
 pop di
 pop ds
%ifdef VIEWPORT_PRESERVE_DS
 ; Native unblank otherwise reads its configured port through shadow/video DS.
 ; This callback preserves SI/DI/BP, so restore caller DS before entering it.
 call ui_cga_unblank
%endif
 pop bp
 ret 2
