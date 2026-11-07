; Authored diagnostic services. No UART, file, keyboard, video or window IO.
BITS 16
CPU 8086
GROUP DGROUP PADSEG _DATA
SEGMENT _TEXT public class=CODE use16
global meta_editor_inverse,meta_editor_cursor,meta_editor_read_key
global meta_editor_edit_text,meta_editor_draw_kind
extern meta_editor_field_key
meta_editor_inverse:
 inc word [_inverse_calls]
 mov ax,0x7000
 ret
meta_editor_cursor:
 inc word [_cursor_calls]
 ret 4
meta_editor_read_key:
 cmp word [meta_editor_wait_active],10000
 je .wait_ok
 inc word [_service_errors]
.wait_ok:
 mov bx,[_key_position]
 cmp bx,[_key_count]
 jb .key
 inc word [_service_errors]
 mov ax,27
 ret
.key:
 inc word [_key_position]
 shl bx,1
 mov ax,[_keys+bx]
 ret
meta_editor_draw_kind:
 push bp
 mov bp,sp
 inc word [_draw_calls]
 mov ax,[bp+10]
 mov [_last_label],ax
 pop bp
 ret
meta_editor_edit_text:
 push bp
 mov bp,sp
 inc word [_field_calls]
 cmp word [bp+4],meta_editor_field_key
 jne .bad
 cmp word [bp+6],50
 jne .bad
 mov bx,[bp+8]
 cmp bx,[bp+10]
 jne .bad
 cmp word [bp+12],0x7000
 jne .bad
 mov ax,[_selected_row]
 add ax,6
 mov ah,al
 mov al,25
 cmp ax,[bp+14]
 jne .bad
 ; Deliberately expose the boundary's writes even on a canceled return.
 ; This is NOT a reconstruction of the original shared text editor.
 mov word [bx],0x0078
 mov ax,[_field_return]
 pop bp
 ret 12
.bad:
 inc word [_service_errors]
 mov ax,0xffff
 pop bp
 ret 12

SEGMENT PADSEG public align=16 class=DATA use16
 times 128 db 0xa5
SEGMENT _DATA public class=DATA use16
%macro word_state 2
 global %1,%2
 %1:
 %2: dw 0
%endmacro
global meta_editor_records,_records,_records_before,_records_after
_records_before: times 16 db 0
meta_editor_records:
_records: times 540 db 0
_records_after: times 16 db 0
word_state meta_editor_attribute,_attribute
word_state meta_editor_wait_active,_wait_active
word_state meta_editor_wait_default,_wait_default
word_state meta_editor_field_previous,_field_previous
word_state meta_editor_field_next,_field_next
word_state meta_editor_edit_previous,_edit_previous
word_state meta_editor_edit_next,_edit_next
global meta_editor_kind_labels,meta_editor_kind_format
meta_editor_kind_labels: dw 0x1010,0x2020,0x3030,0x4040
meta_editor_kind_format: db 0
global _keys,_key_count,_key_position,_selected_row,_field_return
_keys: times 16 dw 0
_key_count: dw 0
_key_position: dw 0
_selected_row: dw 0
_field_return: dw 0
global _inverse_calls,_cursor_calls,_draw_calls,_last_label,_field_calls,_service_errors
_inverse_calls: dw 0
_cursor_calls: dw 0
_draw_calls: dw 0
_last_label: dw 0
_field_calls: dw 0
_service_errors: dw 0
