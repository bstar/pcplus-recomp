; Controlled compact-DS connection component, never an application loader.
; Generated includes contain symbolic aliases/callbacks, no recovered bytes.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global connection_probe_start,connection_probe_stop
global controlled_parent_gate,controlled_parent_dispatch,controlled_parent_return
global controlled_private_restore_sp
global gate_saved_ss,gate_saved_sp,gate_busy
connection_probe_start:
connection_probe_stop:
 hlt

; The fixture actually changes DS=SS and stacks around a FAR callback. The
; parent dispatch is controlled, with a separate guarded synthetic stack.
; No real parent handle, resident bridge, UART, file or IRQ is accessed.
controlled_parent_gate:
 cmp byte [cs:gate_busy],0
 jne connection_probe_stop
 mov byte [cs:gate_busy],1
 pushf
 mov [cs:gate_saved_ss],ss
 mov [cs:gate_saved_sp],sp
 mov bx,0x7000
 mov ss,bx
 mov sp,0x1000
 mov ds,bx
controlled_parent_dispatch:
 nop
controlled_parent_return:
 mov bx,[cs:gate_saved_ss]
 mov cx,[cs:gate_saved_sp]
 mov ss,bx
controlled_private_restore_sp:
 mov sp,cx
 mov ds,bx
 popf
 mov byte [cs:gate_busy],0
 retf
gate_saved_ss: dw 0
gate_saved_sp: dw 0
gate_busy: db 0
%include "connection_callbacks.inc"

SEGMENT _DATA public class=DATA use16
global private_data_header
private_data_header: db 'CONNOMF',0
 dw 1,0,0,0

SEGMENT _BSS public class=BSS use16
; SPAN logical address/extent records the old alias relationship. The optional
; fourth argument reserves extra capacity without conflating adjacent symbols.
%macro SPAN 3-4 0
 global %1
 %1:
 %if %4
  resb %4
 %else
  resb %3
 %endif
%endmacro
SPAN private_config,0x1b84,24
SPAN private_commands,0x1bcb,75
SPAN private_responses,0x1c48,176
SPAN private_terminal,0x1d18,4
SPAN private_hangup_flags,0x1d68,18
SPAN private_ui_attribute,0x1f7a,2
SPAN private_hangup_resource,0x2076,2
SPAN private_key_name,0x21d8,81
SPAN private_meta_name,0x3262,14,81
SPAN private_baud_table,0x3270,32
SPAN private_other_gate,0x3986,2
SPAN private_protocol,0x3996,2
SPAN private_empty,0x4942,1
SPAN private_stream,0x4b02,2
SPAN private_date,0x5100,9
SPAN private_builtin,0x5150,8
SPAN private_file,0x5200,4
SPAN private_wire,0x5300,512
SPAN private_resource_3f9c,0x3f9c,1
SPAN private_resource_6626,0x6626,1
SPAN private_resource_664c,0x664c,1
SPAN private_resource_6672,0x6672,1
SPAN private_resource_667c,0x667c,1
SPAN private_resource_6686,0x6686,1
SPAN private_resource_68b2,0x68b2,1
SPAN private_manual_name,0x69e4,12
SPAN private_resource_69f0,0x69f0,1
SPAN private_resource_6a00,0x6a00,1
SPAN private_resource_6a08,0x6a08,1
SPAN private_resource_6a10,0x6a10,1
SPAN private_resource_6a18,0x6a18,1
SPAN private_page_size,0x6f4a,2
SPAN private_marked_count,0x6f50,2
SPAN private_resource_6ff2,0x6ff2,1
; Keep these115 bytes contiguous: 15x7 slots, two separator strings, "0".
SPAN private_selections,0x70b4,115
SPAN private_resource_7127,0x7127,1
SPAN private_literal_transform,0x7748,13
SPAN private_physical_rows,0x7a74,2
SPAN private_rx_available,0x8e20,2
SPAN private_response_cursors,0x8f58,22
SPAN private_driver,0x8ff4,2
SPAN private_FAILURE,0xd124,2
SPAN private_string_bank,0xd13a,162
SPAN private_global_table,0xdb82,8
SPAN private_string_pending,0xdd82,6
; 11x81 scratch bytes + native alignment byte + pointer/index words.
SPAN private_string_scratch,0xdd88,896
SPAN private_operand_frame,0xe13a,2
SPAN private_lookahead,0xe38c,2
SPAN private_dial_ui_state,0xe464,32
SPAN private_selection_markers,0xe57e,201
; 114-byte record and eight coordinate words preserve all field aliases.
SPAN private_record,0xe650,130
SPAN private_global0,0xf100,81
SPAN private_global1,0xf151,81
%include "connection_data_bindings.inc"
global private_bss_end
private_bss_end:

SEGMENT STACK stack class=STACK use16
global private_stack_guard_low,private_stack_base,private_stack_end,private_stack_guard_high
private_stack_guard_low: resb 16
private_stack_base: resb 4096
private_stack_end:
private_stack_guard_high: resb 16
GROUP DGROUP _DATA _BSS STACK
