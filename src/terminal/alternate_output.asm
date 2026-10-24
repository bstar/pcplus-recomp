; Checked native alternate field-cell output. This metadata/color operation
; does not download or select fonts; the old boundary name remains its ABI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_abort,text_write_cell
extern alternate_output_checked_far
global render_font_output,alternate_output_abort_far,alternate_output_text_far
render_font_output:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call far alternate_output_checked_far
 pop bp
 ret 4
alternate_output_abort_far:
 mov ax,0xbb53
 jmp terminal_abort
alternate_output_text_far:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call text_write_cell
 pop bp
 retf 6
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
GROUP ASPECT_GROUP ASPECT_CODE
extern alternate_output_native,attribute_geometry_admit
extern screen_attribute_offset,erase_attribute_values_base,erase_attribute_values
extern screen_cursor_wrap,attributes_color_mode,render_translation_enabled
extern render_translation_base,render_translation_table
global alternate_output_checked_far,alternate_output_text,alternate_output_checked_end
alternate_output_checked_far:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
 cmp word [screen_cursor_wrap],1
 jne .bad
 cmp word [attributes_color_mode],0
 jne .bad
 cmp word [render_translation_enabled],1
 ja .bad
 cmp word [render_translation_base],render_translation_table
 jne .bad
 call attribute_geometry_admit
 jc .bad
 cmp word [erase_attribute_values_base],erase_attribute_values
 jne .bad
 mov ax,[bp+6]
 cmp ax,[screen_attribute_offset]
 jne .bad
 push word [bp+8]
 push ax
 call alternate_output_native
 pop es
 pop di
 pop si
 pop bp
 retf 4
.bad:
 jmp far alternate_output_abort_far
alternate_output_text:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call far alternate_output_text_far
 pop bp
 ret 6
alternate_output_checked_end:
