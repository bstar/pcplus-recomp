; Checked fixed-plane admission around exact native attribute navigation.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern attribute_boundary_native,pcplus_flow_bell,terminal_abort
extern screen_columns,screen_attribute_row_bytes,screen_video_row_bytes,text_video_segment
extern screen_viewport_enabled,screen_viewport_active,screen_viewport_offset
extern screen_visible_column,terminal_viewport_admit_impl
extern csi_last_row,screen_last_column,screen_first_row,screen_last_row
extern erase_cell_count,screen_attributes_base,screen_attribute_cells
extern screen_cursor_row,screen_cursor_column,screen_attribute_offset,screen_video_offset
global attribute_screen_set_cursor_far
global screen_adjust_attribute_boundary,attribute_geometry_admit,attribute_plane_admit,attribute_boundary_notice
extern screen_set_cursor,screen_cursor_left,screen_cursor_right

; Preserve the resident near-call/RET4 interface through the checked far API.
screen_adjust_attribute_boundary:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call far attribute_boundary_checked_far
 pushf
 cmp ax,3
 je .invalid
 popf
 pop bp
 ret 4
.invalid:
 popf
 pop bp
 mov ax,0x2adc
 jmp terminal_abort

attribute_screen_set_cursor_far:
 call screen_set_cursor
 retf
attribute_screen_cursor_left_far:
 call screen_cursor_left
 retf
attribute_screen_cursor_right_far:
 call screen_cursor_right
 retf

attribute_boundary_notice_far:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 call pcplus_flow_bell
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
; Read-only geometry check; near callers live in this far segment.
global attribute_geometry_admit_far
attribute_geometry_admit_far:
 call attribute_geometry_admit
 retf
attribute_geometry_admit:
 call attribute_plane_admit
 jc .bad
 mov ax,[screen_cursor_row]
 cmp ax,[csi_last_row]
 ja .bad
 mov bx,[screen_cursor_column]
 cmp bx,[screen_attribute_row_bytes]
 jae .bad
 mov cx,[screen_attribute_row_bytes]
 mul cx
 add ax,bx
 cmp ax,[screen_attribute_offset]
 jne .bad
 cmp word [screen_viewport_enabled],0
 je .ordinary
 mov ax,bx
 sub ax,[screen_viewport_offset]
 jc .bad
 cmp ax,80
 jae .bad
 cmp ax,[screen_visible_column]
 jne .bad
 shl ax,1
 mov cx,ax
 mov ax,[screen_cursor_row]
 mul word [screen_video_row_bytes]
 add ax,cx
 jmp .video
.ordinary:
 shl ax,1
.video:
 cmp ax,[screen_video_offset]
 jne .bad
 clc
 ret
.bad:
 stc
 ret

; Whole-plane repair during native wrapping ignores temporarily stale cursor
; offsets; it still requires bounded real backing and fixed video geometry.
attribute_plane_admit:
 cmp word [screen_attribute_row_bytes],132
 jne .ordinary
 ; Reuse the owned static-shadow/status/modal admission. Native whole-plane
 ; repair deliberately ignores cursor offsets while its own scan is moving.
 jmp terminal_viewport_admit_impl
.ordinary:
 cmp word [screen_columns],80
 jne .bad
 cmp word [screen_attribute_row_bytes],80
 jne .bad
 cmp word [screen_video_row_bytes],160
 jne .bad
 cmp word [text_video_segment],0xb800
 jne .bad
 cmp word [screen_viewport_enabled],0
 jne .bad
 cmp word [screen_viewport_active],1
 ja .bad
 cmp word [screen_viewport_offset],0
 jne .bad
 cmp word [screen_last_column],79
 jne .bad
 mov ax,[csi_last_row]
 cmp ax,24
 ja .bad
 cmp [screen_last_row],ax
 ja .bad
 mov bx,[screen_first_row]
 cmp bx,[screen_last_row]
 ja .bad
 inc ax
 mov cx,80
 mul cx
 cmp ax,[erase_cell_count]
 jne .bad
 cmp word [screen_attributes_base],screen_attribute_cells
 jne .bad
 clc
 ret
.bad:
 stc
 ret


; Far stack carries offset,direction. Native helper keeps its own RET4 ABI.
attribute_boundary_checked_far:
 push bp
 mov bp,sp
 call attribute_geometry_admit
 jc .invalid
 mov ax,[bp+6]
 cmp ax,[erase_cell_count]
 jae .invalid
 push word [bp+8]
 push word [bp+6]
 call attribute_boundary_native
 pop bp
 retf 4
.invalid:
 mov ax,3
 pop bp
 retf 4

; Imports of relocated native code resolve to these same-segment near proxies.
global attribute_screen_set_cursor,attribute_screen_cursor_left,attribute_screen_cursor_right,attribute_boundary_local
attribute_screen_set_cursor:
 call far attribute_screen_set_cursor_far
 ret
attribute_screen_cursor_left:
 call far attribute_screen_cursor_left_far
 ret
attribute_screen_cursor_right:
 call far attribute_screen_cursor_right_far
 ret
attribute_boundary_local:
 jmp attribute_boundary_native
attribute_boundary_notice:
 call far attribute_boundary_notice_far
 ret
