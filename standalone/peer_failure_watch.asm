; Test-only extension of the passive width observer. Product MZs are unchanged.
; Only the declared startup refusal fixture writes a product setting.
%define PEER_WIDTH
%define COMPACT_OBSERVER
%macro PEER_WATCH_DATA 0
child_result: dw 0xffff
child_width: dw 0xffff
child_rows: dw 0xffff
child_cells: dw 0xffff
child_scope: dw 0xffff
child_parser: dw 0xffff
child_wait: dw 0xffff
child_native_active: dw 0xffff
child_native_busy: dw 0xffff
child_service: dw 0xffff
final_service: dw 0xffff
final_width: dw 0xffff
final_parser: dw 0xffff
final_scope: dw 0xffff
final_wait: dw 0xffff
final_native_active: dw 0xffff
final_native_busy: dw 0xffff
%endmacro
%macro PEER_WATCH_STAGE 0
%ifdef NATIVE_REFUSE
 ; Rendering supports this cursor backend; the width transaction requires
 ; BIOS ownership. Its real admission must refuse without a native commit.
 mov word [SCREEN_USE_BIOS_CURSOR],0
%endif
%endmacro
%macro PEER_WATCH_CHILD 0
 and ax,255
 mov [cs:child_result],ax
 mov ax,[cs:root_ds]
 mov es,ax
 mov ax,[es:SCREEN_ATTRIBUTE_ROW_BYTES]
 mov [cs:child_width],ax
 mov ax,[es:CSI_ROW_COUNT]
 mov [cs:child_rows],ax
 mov ax,[es:ERASE_CELL_COUNT]
 mov [cs:child_cells],ax
 mov ax,[es:TERMINAL_ASPECT_ACTIVE]
 mov [cs:child_scope],ax
 mov ax,[es:TERMINAL_PARSER_ACTIVE]
 mov [cs:child_parser],ax
 mov ax,[es:TERMINAL_ANSI_WAIT_ACTIVE]
 mov [cs:child_wait],ax
 mov ax,[es:CSI_UNIMPLEMENTED_SERVICE]
 mov [cs:child_service],ax
 mov ax,[cs:live_call+2]
 mov es,ax
 mov ax,[es:RESET_LIVE_ACTIVE]
 mov [cs:child_native_active],ax
 mov ax,[es:RESET_BANK_BUSY]
 mov [cs:child_native_busy],ax
%endmacro
%macro PEER_WATCH_ROOT 0
 mov ax,[CSI_UNIMPLEMENTED_SERVICE]
 mov [cs:final_service],ax
 mov ax,[SCREEN_ATTRIBUTE_ROW_BYTES]
 mov [cs:final_width],ax
 mov ax,[TERMINAL_PARSER_ACTIVE]
 mov [cs:final_parser],ax
 mov ax,[TERMINAL_ASPECT_ACTIVE]
 mov [cs:final_scope],ax
 mov ax,[TERMINAL_ANSI_WAIT_ACTIVE]
 mov [cs:final_wait],ax
 mov ax,[cs:live_call+2]
 mov es,ax
 mov ax,[es:RESET_LIVE_ACTIVE]
 mov [cs:final_native_active],ax
 mov ax,[es:RESET_BANK_BUSY]
 mov [cs:final_native_busy],ax
%endmacro
%include "aspect_wide_watch.asm"
