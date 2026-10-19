; Exact native PCPlus2.01 overlay16 ASPECT flow/operand primitives.
; Retained REA: analysis/pcplus-overlay-anchored-16/functions/0x1*.asm,
; selected entries D1F2,D27D,D282,D287,D2D6,D2F9,D307,D310,D317,D339,
; D349,D352,E129,E176. Original SHA256:
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS, DF=0; near ABI. Seek/call consume low/high offset args (RET4);
; other entries RET; read_word returns AX, read_dword returns DX:AX.
; BP/SI/DI preserved; AX/BX/CX/DX/ES/flags volatile. CRT hooks are cdecl.
; No checked file/seek abstraction: failed seeks still leave pushed return
; positions/depth; short DWORD reads expose old stack bytes; EOF word reads
; combine complete16-bit refill returns. Local reservation changes the pointer
; before checking105 and ignores carry. Cleanup scans all3 records regardless
; of occupancy; it does not clear stored depths, and can decrement count again.
; Gate/depth/frame arithmetic and typed pops remain unchecked native behavior.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_FLOW_FLAT
%if ASPECT_FLOW_UNIT=1
ORG 0xd1f2
%elif ASPECT_FLOW_UNIT=2
ORG 0xd27d
%elif ASPECT_FLOW_UNIT=3
ORG 0xd2d6
%elif ASPECT_FLOW_UNIT=4
ORG 0xe129
%else
%error Select ASPECT_FLOW_UNIT1..4
%endif
%define aspect_flow_stream 0x4b02
%define aspect_flow_refill 0x9094
%define aspect_flow_fread 0x845a
%define aspect_flow_fseek 0x853a
%define aspect_flow_ftell 0x8ed8
%define aspect_flow_exit 0x4eb5
%define aspect_flow_error 0x4efb
%define aspect_flow_wait_gate 0xe382
%define aspect_flow_depth 0xe37a
%define aspect_flow_frame 0xe13a
%define aspect_flow_local_count 0xe320
%define aspect_flow_locals 0xe2fc
%define aspect_stack_pointer 0xe13c
%define aspect_stack_arena 0x9062
%define aspect_stack_push_word 0xd0f2
%define aspect_stack_push_dword 0xd110
%define aspect_stack_pop_word 0xd17a
%define aspect_stack_pop_dword 0xd186
%define native_read_word 0xe129
%define native_read_dword 0xe176
%define native_seek 0xd287
%define native_call 0xd2d6
%define native_push_frame 0xd2f9
%define native_call_operand 0xd307
%define native_return 0xd317
%define native_cleanup_locals 0xd352
%else
%define ASPECT_FLOW_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_flow_gate_decrement,aspect_flow_gate_increment,aspect_flow_seek
global aspect_flow_call,aspect_flow_push_frame,aspect_flow_call_operand
global aspect_flow_call_framed,aspect_flow_return,aspect_flow_return_framed
global aspect_flow_jump,aspect_flow_reserve_locals,aspect_flow_cleanup_locals
global aspect_flow_read_word,aspect_flow_read_dword
extern aspect_flow_stream,aspect_flow_refill,aspect_flow_fread,aspect_flow_fseek,aspect_flow_ftell
extern aspect_flow_exit,aspect_flow_error,aspect_flow_wait_gate,aspect_flow_depth
extern aspect_flow_frame,aspect_flow_local_count,aspect_flow_locals
extern aspect_stack_pointer,aspect_stack_arena,aspect_stack_push_word,aspect_stack_push_dword
extern aspect_stack_pop_word,aspect_stack_pop_dword
%define native_read_word aspect_flow_read_word
%define native_read_dword aspect_flow_read_dword
%define native_seek aspect_flow_seek
%define native_call aspect_flow_call
%define native_push_frame aspect_flow_push_frame
%define native_call_operand aspect_flow_call_operand
%define native_return aspect_flow_return
%define native_cleanup_locals aspect_flow_cleanup_locals
%endif
%if ASPECT_FLOW_UNIT=0 || ASPECT_FLOW_UNIT=1
aspect_flow_reserve_locals:
 call native_read_word
 add [aspect_stack_pointer],ax
 mov ax,aspect_stack_arena
 add ax,0x3aca
 cmp ax,[aspect_stack_pointer]
 jae .done
 mov ax,105
 push ax
 call aspect_flow_error
.done:
 ret
%endif
%if ASPECT_FLOW_UNIT=0 || ASPECT_FLOW_UNIT=2
aspect_flow_gate_decrement:
 dec word [aspect_flow_wait_gate]
 ret
aspect_flow_gate_increment:
 inc word [aspect_flow_wait_gate]
 ret
aspect_flow_seek:
 push bp
 mov_load bp,sp
 sub_load ax,ax
 push ax
 push word [bp+6]
 push word [bp+4]
 push word [aspect_flow_stream]
 call aspect_flow_fseek
 mov_load sp,bp
 pop bp
 ret 4
%endif
%if ASPECT_FLOW_UNIT=0 || ASPECT_FLOW_UNIT=3
aspect_flow_call:
 push bp
 mov_load bp,sp
 inc word [aspect_flow_depth]
 push word [aspect_flow_stream]
 call aspect_flow_ftell
 pop bx
 push dx
 push ax
 call aspect_stack_push_dword
 push word [bp+6]
 push word [bp+4]
 call native_seek
 mov_load sp,bp
 pop bp
 ret 4
aspect_flow_push_frame:
 push word [aspect_flow_frame]
 call aspect_stack_push_word
 mov ax,[aspect_stack_pointer]
 mov [aspect_flow_frame],ax
 ret
aspect_flow_call_operand:
 call native_read_dword
 push dx
 push ax
 call native_call
 ret
aspect_flow_call_framed:
 call native_call_operand
 call native_push_frame
 ret
aspect_flow_return:
 cmp word [aspect_flow_depth],byte 0
 jne .nested
 call aspect_flow_exit
 ret
.nested:
 dec word [aspect_flow_depth]
 cmp word [aspect_flow_local_count],byte 0
 je .pop
 call native_cleanup_locals
.pop:
 call aspect_stack_pop_dword
 push dx
 push ax
 call native_seek
 ret
aspect_flow_return_framed:
 mov ax,[aspect_flow_frame]
 mov [aspect_stack_pointer],ax
 call aspect_stack_pop_word
 mov [aspect_flow_frame],ax
 call native_return
 ret
aspect_flow_jump:
 call native_read_dword
 push dx
 push ax
 call native_seek
 ret
aspect_flow_cleanup_locals:
 mov bx,aspect_flow_locals+4
 jmp short .test
.slot:
 mov ax,[bx]
 cmp [aspect_flow_depth],ax
 jae .next
 mov word [bx-4],0
 dec word [aspect_flow_local_count]
.next:
 add bx,byte 12
.test:
 cmp bx,aspect_flow_locals+28
 jbe .slot
 ret
%endif
%if ASPECT_FLOW_UNIT=0 || ASPECT_FLOW_UNIT=4
aspect_flow_read_word:
 push di
 push si
 mov bx,[aspect_flow_stream]
 dec word [bx+2]
 mov bx,[aspect_flow_stream]
 cmp word [bx+2],byte 0
 jl .refill_low
 mov si,[bx]
 inc word [bx]
 mov al,[si]
 sub_load ah,ah
 jmp short .low
.refill_low:
 push bx
 call aspect_flow_refill
 pop bx
.low:
 mov_load si,ax
 mov bx,[aspect_flow_stream]
 dec word [bx+2]
 mov bx,[aspect_flow_stream]
 cmp word [bx+2],byte 0
 jl .refill_high
 mov di,[bx]
 inc word [bx]
 mov al,[di]
 sub_load ah,ah
 jmp short .high
.refill_high:
 push bx
 call aspect_flow_refill
 pop bx
.high:
 mov_load ah,al
 sub_load al,al
 or_load ax,si
 pop si
 pop di
 ret
aspect_flow_read_dword:
 push bp
 mov_load bp,sp
 sub sp,byte 4
 push word [aspect_flow_stream]
 mov ax,1
 push ax
 mov ax,4
 push ax
 lea ax,[bp-4]
 push ax
 call aspect_flow_fread
 mov ax,[bp-4]
 mov dx,[bp-2]
 mov_load sp,bp
 pop bp
 ret
%endif
