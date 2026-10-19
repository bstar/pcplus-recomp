; Source-only DOS diagnostic adapter; production owns separate guarded services.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _status_format
extern status_ui_printf,status_message,status_character_fill
extern _status_diag_cga_unavailable
GLOBAL status_sprintf,_status_diag_printf,_status_diag_message,_status_diag_fill
status_sprintf:
 push bp
 mov bp,sp
 mov ax,11
 push ax
 lea ax,[bp+8]
 push ax
 push word [bp+6]
 mov ax,136
 push ax
 push word [bp+4]
 call far _status_format
 add sp,10
 mov [_status_diag_error],ax
 pop bp
 ret
_status_diag_printf:
 push bp
 mov bp,sp
 push si
 mov si,[bp+6]
 add si,20
 mov cx,11
.push:
 push word [si]
 sub si,2
 loop .push
 push word [bp+4]
 mov ax,0x1f
 push ax
 mov ax,0x1800
 push ax
 call status_ui_printf
 add sp,28
 pop si
 pop bp
 ret
_status_diag_message:
 push bp
 mov bp,sp
 push word [bp+4]
 call status_message
 pop bx
 pop bp
 ret
_status_diag_fill:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call status_character_fill
 pop bp
 ret
; Never silently model CGA. The DOS tests select non-CGA video; the CPU test
; separately executes actual CGA instructions with explicit port observations.
global text_cga_word
text_cga_word:
 call _status_diag_cga_unavailable
 ret
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
GLOBAL ui_flow_region_cells,ui_flow_coordinate_base,reset_data_1f6c
GLOBAL text_video_segment,text_cga_status_port,program_state_7a72
GLOBAL ui_flow_video_base,screen_columns,_status_diag_error
ui_flow_region_cells: dw 80
ui_flow_coordinate_base: dw 0x1800
reset_data_1f6c: dw 0x1f
text_video_segment: dw 0xb800
text_cga_status_port: dw 0
program_state_7a72:
screen_columns: dw 80
ui_flow_video_base: dw 0x0f00
_status_diag_error: dw 0
