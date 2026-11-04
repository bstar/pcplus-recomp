; Original Ctrl-] status toggle46BA..4734;123 exact bytes.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef STATUS_TOGGLE_OMF
SEGMENT STATUS_TOGGLE_NATIVE_CODE public align=16 class=FARCODE use16
extern csi_last_row,screen_last_row,screen_bottom_margin,screen_cursor_row,screen_cursor_column
extern status_hidden,physical_rows,status_rows,effective_rows
extern status_clear_original,scroll_up,screen_set_cursor,status_refresh_original
global local_status_toggle_46ba
%else
ORG 0x46ba
%define csi_last_row 0x334a
%define screen_last_row 0xce3a
%define screen_bottom_margin 0xcee4
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define status_hidden 0x1d46
%define physical_rows 0x7a74
%define status_rows 0x7a80
%define effective_rows 0x334c
%define status_clear_original 0x4795
%define scroll_up 0x1fc4
%define screen_set_cursor 0x1bbe
%define status_refresh_original 0x2fb8
%endif
local_status_toggle_46ba:
 push di
 push si
 mov ax,[csi_last_row]
 cmp [screen_last_row],ax
 jne .last_custom
 mov di,1
 jmp short .bottom
.last_custom:
 sub_load di,di
.bottom:
 cmp [screen_bottom_margin],ax
 jne .bottom_custom
 mov si,1
 jmp short .toggle
.bottom_custom:
 sub_load si,si
.toggle:
 cmp word [status_hidden],byte 1
 sbb_load ax,ax
 neg ax
 mov [status_hidden],ax
 or_load ax,ax
 jz .show
 mov ax,[physical_rows]
 dec ax
 mov [csi_last_row],ax
 mov ax,[physical_rows]
 mov [effective_rows],ax
 call status_clear_original
 jmp short .margins
.show:
 mov ax,[status_rows]
 dec ax
 mov [csi_last_row],ax
 mov ax,[status_rows]
 mov [effective_rows],ax
 cmp ax,[screen_cursor_row]
 jg .draw
 call scroll_up
 mov ax,[csi_last_row]
 mov dx,[screen_cursor_column]
 call screen_set_cursor
.draw:
 call status_refresh_original
.margins:
 or_load di,di
 jz .last_done
 mov ax,[csi_last_row]
 mov [screen_last_row],ax
.last_done:
 or_load si,si
 jz .done
 mov ax,[csi_last_row]
 mov [screen_bottom_margin],ax
.done:
 pop si
 pop di
 ret
