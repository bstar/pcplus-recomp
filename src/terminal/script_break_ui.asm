; Maintained single owned bracket around native BREAK notice31BB. Parent DS=SS.
; Far API BX0 begin,1 end; AX typed result. No UART access or child pointers.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public class=FARCODE use16
extern ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base,screen_columns,ui_flow_suppressed
extern aspect_break_cursor_read_far,aspect_break_cursor_restore_far,aspect_break_notice_far
global terminal_break_ui
terminal_break_ui:
 cmp bx,1
 je .end
 or bx,bx
 jnz .operand
 cmp word [script_break_ui_active],0
 jne .state
 cmp word [ui_flow_region_cells],80
 jne .unsupported
 cmp word [ui_flow_video_base],3840
 jne .unsupported
 cmp word [ui_flow_coordinate_base],0x1800
 jne .unsupported
 cmp word [screen_columns],80
 jne .unsupported
 call far aspect_break_cursor_read_far
 mov [script_break_ui_cursor],ax
 mov word [script_break_ui_underlay_valid],0
 cmp word [ui_flow_suppressed],0
 jne .draw
 call far aspect_break_snapshot_far
 mov word [script_break_ui_underlay_valid],1
.draw:
 mov word [script_break_ui_active],1
 call far aspect_break_notice_far
 xor ax,ax
 retf
.end:
 cmp word [script_break_ui_active],0
 je .ok
 mov word [script_break_ui_active],0
 cmp word [script_break_ui_underlay_valid],0
 je .cursor
 mov word [script_break_ui_underlay_valid],0
 call far aspect_break_restore_far
.cursor:
 mov ax,[script_break_ui_cursor]
 call far aspect_break_cursor_restore_far
.ok:
 xor ax,ax
 retf
.operand: mov ax,7
 retf
.state: mov ax,10
 retf
.unsupported: mov ax,3
 retf

SEGMENT _TEXT public class=CODE use16
extern aspect_break_cursor_read,screen_cursor_output,pcplus_flow_message
extern pcplus_screen_save,pcplus_screen_restore
global aspect_break_cursor_read_far,aspect_break_cursor_restore_far,aspect_break_notice_far
aspect_break_cursor_read_far:
 call aspect_break_cursor_read
 retf
aspect_break_cursor_restore_far:
 push ax
 call screen_cursor_output
 retf
aspect_break_notice_far:
 xor ax,ax
 push ax
 mov ax,script_break_notice
 push ax
 call pcplus_flow_message
 add sp,4
 retf

; Retain only the native15-cell notice region. Revocation can restore it even
; after an abrupt child exit, before UART handback is validated/reacquired.
aspect_break_snapshot_far:
 mov ax,script_break_ui_underlay
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_save
 retf
aspect_break_restore_far:
 mov ax,script_break_ui_underlay
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_restore
 retf

SEGMENT _DATA public class=DATA use16
global script_break_ui_active,script_break_ui_cursor
script_break_ui_active: dw 0
script_break_ui_cursor: dw 0
script_break_ui_underlay_valid: dw 0
script_break_ui_underlay: times 30 db 0
script_break_notice: db '*** BREAK ***',0
