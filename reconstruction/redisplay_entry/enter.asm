; Exact PCPlus2.01 Redisplay entry, also called by Chat Alt-F6.
; Source coordinates and original-file mapping are in provenance.json.
BITS 16
CPU 8086
%ifdef REDISPLAY_ENTRY_OMF
SEGMENT _TEXT public class=CODE use16
global redisplay_native_enter
extern window_cursor_push,window_cursor_pop,display_snapshot,redisplay_restore_or_alert
extern redisplay_cursor_hide,redisplay_cursor_show,redisplay_native_view,redisplay_empty_notice
extern redisplay_help_context,display_viewport,display_last_column,native_display_cursor_policy
extern redisplay_bounds,redisplay_origin,mouse_scale_x,redisplay_configured_scale_x
extern redisplay_history_head,redisplay_history_start,redisplay_history_end,redisplay_history_wrapped
extern redisplay_position,redisplay_empty_text
%define short
%else
ORG 0xd830
%define window_cursor_push 0x6b5a
%define window_cursor_pop 0x6b42
%define display_snapshot 0x6bbe
%define redisplay_restore_or_alert 0x4870
%define redisplay_cursor_hide 0x6e5a
%define redisplay_cursor_show 0x6dca
%define redisplay_native_view 0xd95c
%define redisplay_empty_notice 0x427f
%define redisplay_help_context 0x397a
%define display_viewport 0x7a84
%define display_last_column 0x7a7e
%define native_display_cursor_policy 0x7a6c
%define redisplay_bounds 0xe8a2
%define redisplay_origin 0xe8a0
%define mouse_scale_x 0x7a50
%define redisplay_configured_scale_x 0x2068
%define redisplay_history_head 0x4ebe
%define redisplay_history_start 0x4eba
%define redisplay_history_end 0x4ec6
%define redisplay_history_wrapped 0x4ec8
%define redisplay_position 0xe888
%define redisplay_empty_text 0x7692
%endif
%include "encodings.inc"
redisplay_native_enter:
L_d830: push bp
L_d831: mov_load bp,sp
L_d833: sub sp,0x4
L_d836: push di
L_d837: push si
L_d838: mov word [redisplay_help_context],0x25
L_d83e: mov ax,[display_viewport]
L_d841: add ax,[display_last_column]
L_d845: sub ax,0x100
L_d848: mov [redisplay_bounds],ax
L_d84b: mov word [redisplay_origin],0
L_d851: mov si,[native_display_cursor_policy]
L_d855: or_load si,si
L_d857: jz short L_d85c
L_d859: call redisplay_cursor_hide
L_d85c: call window_cursor_push
L_d85f: call display_snapshot
L_d862: mov_load di,ax
L_d864: mov [bp-0x2],dx
L_d867: mov word [mouse_scale_x],10000
L_d86d: mov ax,[redisplay_history_head]
L_d870: dec ax
L_d871: mov [redisplay_position],ax
L_d874: cmp word [redisplay_history_wrapped],0
L_d879: jz short L_d890
L_d87b: mov ax,[redisplay_history_start]
L_d87e: cmp [redisplay_history_head],ax
L_d882: jnz short L_d88b
L_d884: mov ax,[redisplay_history_end]
L_d887: dec ax
L_d888: mov [redisplay_position],ax
L_d88b: call redisplay_native_view
L_d88e: jmp short L_d8a0
L_d890: mov ax,[redisplay_history_start]
L_d893: cmp [redisplay_history_head],ax
L_d897: jnz short L_d88b
L_d899: lea bx,[redisplay_empty_text]
L_d89d: call redisplay_empty_notice
L_d8a0: mov ax,[redisplay_configured_scale_x]
L_d8a3: mov [mouse_scale_x],ax
L_d8a6: push word [bp-0x2]
L_d8a9: push di
L_d8aa: call redisplay_restore_or_alert
L_d8ad: call window_cursor_pop
L_d8b0: or_load si,si
L_d8b2: jz short L_d8b7
L_d8b4: call redisplay_cursor_show
L_d8b7: pop si
L_d8b8: pop di
L_d8b9: mov_load sp,bp
L_d8bb: pop bp
L_d8bc: ret
