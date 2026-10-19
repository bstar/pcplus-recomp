; Exact PCPlus2.01 EXECUTE/CHAIN handler and per-file/final native owners.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS. EXECUTE nearRET; file_open(owner,filename) RET4; finish nearRET.
; File opener/allocator/error/UI boundaries remain explicit native dependencies.
; E104 is the string scratch pointer, not a separately owned filename allocation.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CHAIN_FLAT
%if ASPECT_CHAIN_UNIT=1
ORG 0xe709
%elif ASPECT_CHAIN_UNIT=2
ORG 0xd770
%elif ASPECT_CHAIN_UNIT=3
ORG 0xd804
%endif
%define aspect_string_next_scratch 0xdfc7
%define aspect_string_read 0xdf04
%define aspect_chain_copy 0x8268
%define aspect_dispatch_exit_state 0xe378
%define aspect_chain_load 0xd4d0
%define aspect_globals_allocate 0xd850
%define aspect_chain_cursor_show 0x6dca
%define aspect_chain_stack_origin 0x9062
%define aspect_stack_pointer 0xe13c
%define aspect_flow_frame 0xe13a
%define aspect_expr_stage_index 0xe390
%define aspect_operand_lookahead 0xe38c
%define aspect_flow_depth 0xe37a
%define aspect_flow_local_count 0xe320
%define aspect_when_disconnect_armed 0xe2fa
%define aspect_when_active_count 0xe2f8
%define aspect_string_pending_near 0xdd86
%define aspect_flow_locals 0xe2fc
%define aspect_when_records 0xe1a0
%define aspect_flow_stream 0x4b02
%define aspect_string_scratch_index 0xe106
%define aspect_string_scratch_pointer 0xe104
%define aspect_string_scratch 0xdd88
%define aspect_flow_wait_gate 0xe382
%define aspect_chain_aux_files 0xe39e
%define aspect_chain_aux_far_blocks 0xe108
%define aspect_chain_script_owner 0x4b00
%define aspect_chain_close 0x8318
%define aspect_chain_far_free 0x85fc
%define aspect_chain_status 0x2fb8
%else
%ifdef ASPECT_CHAIN_RUNTIME
%define ASPECT_CHAIN_UNIT 1
%else
%define ASPECT_CHAIN_UNIT 0
%endif
SEGMENT _TEXT public class=CODE use16
global aspect_chain_command
%ifndef ASPECT_CHAIN_RUNTIME
global aspect_chain_file_open,aspect_chain_finish
%endif
extern aspect_string_next_scratch
extern aspect_string_read
extern aspect_chain_copy
extern aspect_dispatch_exit_state
%ifndef ASPECT_CHAIN_RUNTIME
extern aspect_chain_load
extern aspect_globals_allocate
extern aspect_chain_cursor_show
extern aspect_chain_stack_origin
extern aspect_stack_pointer
extern aspect_flow_frame
extern aspect_expr_stage_index
extern aspect_operand_lookahead
extern aspect_flow_depth
extern aspect_flow_local_count
extern aspect_when_disconnect_armed
extern aspect_when_active_count
extern aspect_string_pending_near
extern aspect_flow_locals
extern aspect_when_records
extern aspect_flow_stream
extern aspect_string_scratch_index
extern aspect_string_scratch_pointer
extern aspect_string_scratch
extern aspect_flow_wait_gate
extern aspect_chain_aux_files
extern aspect_chain_aux_far_blocks
extern aspect_chain_script_owner
extern aspect_chain_close
extern aspect_chain_far_free
extern aspect_chain_status
%endif
%endif
%if ASPECT_CHAIN_UNIT=0 || ASPECT_CHAIN_UNIT=1
aspect_chain_command:
 push si
 call aspect_string_next_scratch
 mov_load si,ax
 call aspect_string_read
 push ax
 push si
 call aspect_chain_copy
 pop bx
 pop bx
 mov word [aspect_dispatch_exit_state],999
 pop si
 ret
%endif
%if ASPECT_CHAIN_UNIT=0 || ASPECT_CHAIN_UNIT=2
aspect_chain_file_open:
 push bp
 mov_load bp,sp
 push di
 mov ax,aspect_chain_stack_origin
 add ax,0x19c8
 add ax,strict word 0x52
 add ah,1
 mov [aspect_stack_pointer],ax
 mov [aspect_flow_frame],ax
 sub_load ax,ax
 mov [aspect_expr_stage_index],ax
 mov [aspect_operand_lookahead],ax
 mov [aspect_flow_depth],ax
 mov [aspect_flow_local_count],ax
 mov [aspect_when_disconnect_armed],ax
 mov [aspect_when_active_count],ax
 mov [aspect_dispatch_exit_state],ax
 mov [aspect_string_pending_near],ax
 mov bx,aspect_flow_locals
 jmp short .locals_test
.locals:
 add bx,byte 12
 mov word [bx-12],0
.locals_test:
 cmp bx,aspect_flow_locals+24
 jbe .locals
 mov bx,aspect_when_records+84
 jmp short .patterns_test
.patterns:
 add bx,byte 86
 mov word [bx-86],0
.patterns_test:
 cmp bx,aspect_when_records+84+172
 jbe .patterns
 mov word [aspect_flow_stream],0
 push word [bp+6]
 push word [bp+4]
 call aspect_chain_load
 mov_load di,ax
 or_load di,di
 jz .loaded
 call aspect_globals_allocate
.loaded:
 mov word [aspect_string_scratch_index],0
 mov word [aspect_string_scratch_pointer],aspect_string_scratch
 call aspect_chain_cursor_show
 inc word [aspect_flow_wait_gate]
 cmp word [bp+4],0
 jz .result
 inc word [aspect_flow_wait_gate]
.result:
 mov_load ax,di
 pop di
 mov_load sp,bp
 pop bp
 ret 4
%endif
%if ASPECT_CHAIN_UNIT=0 || ASPECT_CHAIN_UNIT=3
aspect_chain_finish:
 push si
 mov si,aspect_chain_aux_files
 jmp short .files_test
.files:
 cmp word [si],0
 jz .next_file
 push word [si]
 call aspect_chain_close
 pop bx
.next_file:
 inc si
 inc si
.files_test:
 cmp si,aspect_chain_aux_files+10
 jbe .files
 mov si,aspect_chain_aux_far_blocks
 jmp short .blocks_test
.blocks:
 mov ax,[si+2]
 or ax,[si]
 jz .next_block
 push word [si+2]
 push word [si]
 call aspect_chain_far_free
 pop bx
 pop bx
.next_block:
 add si,byte 4
.blocks_test:
 cmp si,aspect_chain_aux_far_blocks+8
 jbe .blocks
 mov word [aspect_flow_stream],0
 mov word [aspect_chain_script_owner],0
 call aspect_chain_status
 call aspect_chain_cursor_show
 pop si
 ret
%endif
