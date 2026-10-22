; Source-owned DS=SS/cdecl and data adapters for exact native window code.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern window_save,window_restore
extern display_snapshot,display_restore,display_cursor,display_fill,display_scroll
extern display_cell_offset,display_snow_cell,ui_read_byte
extern _window_platform_allocate,_window_platform_free
%macro alias 2
 global %1
 %1: jmp %2
%endmacro
alias window_snapshot,display_snapshot
alias window_release,display_restore
alias window_cursor,display_cursor
alias window_read_byte,ui_read_byte
alias window_fill,display_fill
alias window_scroll,display_scroll
alias window_offset8,display_cell_offset
alias window_snow_cell,display_snow_cell
alias display_allocate,_window_platform_allocate
alias display_free,_window_platform_free
; Sound is disabled in this component's admitted configuration. A reached
; sound/alert dependency fails visibly; it is never a successful live no-op.
global window_alert,window_sound_open,window_sound_close
window_alert:
window_sound_open:
window_sound_close:
 mov ax,0x4c63
 int 0x21
%macro enter 0
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 cld
%endmacro
%macro leave 0
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
%endmacro
global _window_begin_native,_window_end_native,_window_native_initialize
_window_begin_native:
 enter
 push word [bp+4]
 call window_save
 add sp,2
 leave
_window_end_native:
 enter
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call window_restore
 add sp,6
 leave
_window_native_initialize:
 enter
 mov ax,window_state_7a3a
 mov [window_state_7a36],ax
 mov [window_state_7a38],ax
 mov word [window_state_1d3e],0
 mov word [window_state_7a4e],0
 mov word [window_state_7a66],0
 mov word [window_state_7a6a],8
 mov word [window_state_7a72],80
 mov word [window_state_7a74],25
 mov word [window_state_7a78],0xb800
 mov word [window_state_7a7a],160
 mov word [window_state_7a7c],4000
 mov word [window_state_7a8c],2000
 mov word [window_state_7a8e],0
 mov word [window_state_7ac4],100
 mov ax,[bp+4]
 mov [window_state_7a94],ax
 mov ax,frame
 mov [window_state_3352],ax
 mov [window_state_7ab2],ax
 mov [window_state_7ab4],ax
 leave
SEGMENT _DATA public class=DATA use16
window_video_state: times 0x7ac8-0x7a30 db 0
global window_state_1d3e
window_state_1d3e: dw 0
global window_state_3352
window_state_3352: dw 0
global window_state_7a36
window_state_7a36 equ window_video_state+6
global window_state_7a38
window_state_7a38 equ window_video_state+8
global window_state_7a3a
window_state_7a3a equ window_video_state+10
global window_state_7a4c
window_state_7a4c equ window_video_state+28
global window_state_7a4e
window_state_7a4e equ window_video_state+30
global window_state_7a66
window_state_7a66 equ window_video_state+54
global window_state_7a6a
window_state_7a6a equ window_video_state+58
global window_state_7a72
window_state_7a72 equ window_video_state+66
global window_state_7a74
window_state_7a74 equ window_video_state+68
global window_state_7a78
window_state_7a78 equ window_video_state+72
global window_state_7a7a
window_state_7a7a equ window_video_state+74
global window_state_7a7c
window_state_7a7c equ window_video_state+76
global window_state_7a8c
window_state_7a8c equ window_video_state+92
global window_state_7a8e
window_state_7a8e equ window_video_state+94
global window_state_7a94
window_state_7a94 equ window_video_state+100
global window_state_7ab2
window_state_7ab2 equ window_video_state+130
global window_state_7ab4
window_state_7ab4 equ window_video_state+132
global window_state_7ac4
window_state_7ac4 equ window_video_state+148
global window_state_8fda
window_state_8fda: dw 0
global window_state_8fdc
window_state_8fdc: dw 0
global window_state_8fde
window_state_8fde: dw 0
global display_legacy
display_legacy equ window_state_7a66
global display_columns
display_columns equ window_state_7a72
global display_segment
display_segment equ window_state_7a78
global display_bytes
display_bytes equ window_state_7a7c
global display_cells
display_cells equ window_state_7a8c
global display_status_port
display_status_port equ window_state_7a8e
global text_video_segment
text_video_segment equ window_state_7a78
global text_cga_status_port
text_cga_status_port equ window_state_7a8e
frame: db 218,196,191,179,217,196,192,179
