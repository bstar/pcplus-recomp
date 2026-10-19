; Owned linkedDOS fixture: real recovered flow, stack and nonlocal error code,
; C stdio-backed adapter, no bytecode loop or complete ASPECT implementation.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_flow_read_word,aspect_flow_read_dword,aspect_flow_seek,aspect_flow_call
extern aspect_flow_call_operand,aspect_flow_call_framed,aspect_flow_return,aspect_flow_return_framed
extern aspect_flow_reserve_locals,aspect_flow_jump
extern session_setjmp,aspect_abort
extern _aspect_file_refill,_aspect_file_read,_aspect_file_seek,_aspect_file_tell
extern _stream_owner

global _run_file_flow
_run_file_flow:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov [saved_sp],sp
 mov [saved_bp],bp
 mov si,0x1234
 mov di,0x5678
 mov ax,aspect_dispatch_argument
 push ax
 call session_setjmp
 pop bx
 or ax,ax
 jnz .aborted
 mov bx,[bp+4]
 shl bx,1
 call word [cs:operations+bx]
 mov [_value_low],ax
 mov [_value_high],dx
 xor ax,ax
 jmp short .verify
.aborted:
 mov ax,1
.verify:
 cmp sp,[saved_sp]
 jne .bad
 cmp bp,[saved_bp]
 jne .bad
 cmp si,0x1234
 jne .bad
 cmp di,0x5678
 jne .bad
 mov cx,ss
 mov dx,ds
 cmp cx,dx
 je .done
.bad:
 inc word [_abi_bad]
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
operations: dw word_read,dword_read,seek_file,call_file,operand_call,frame_call,return_file,frame_return,reserve_locals,jump_file
word_read: call aspect_flow_read_word
 ret
dword_read: call aspect_flow_read_dword
 ret
seek_file:
 push word [bp+8]
 push word [bp+6]
 call aspect_flow_seek
 ret
call_file:
 push word [bp+8]
 push word [bp+6]
 call aspect_flow_call
 ret
operand_call: call aspect_flow_call_operand
 ret
frame_call: call aspect_flow_call_framed
 ret
return_file: call aspect_flow_return
 ret
frame_return: call aspect_flow_return_framed
 ret
reserve_locals: call aspect_flow_reserve_locals
 ret
jump_file: call aspect_flow_jump
 ret

; Allstdio callbacks preserve native callee-saved registers. A short operand
; read or failed position operation calls actual native abort/longjmp.
global aspect_flow_refill
aspect_flow_refill:
 push bp
 mov bp,sp
 push word [bp+4]
 call _aspect_file_refill
 pop bx
 cmp ax,0xffff
 jne .done
 mov word [_file_fault],1
 call aspect_abort
.done:
 pop bp
 ret

global aspect_flow_fread
aspect_flow_fread:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call _aspect_file_read
 add sp,byte 8
 cmp ax,[bp+8]
 je .done
 mov word [_file_fault],1
 call aspect_abort
.done:
 pop bp
 ret

global aspect_flow_fseek
aspect_flow_fseek:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call _aspect_file_seek
 add sp,byte 8
 or ax,ax
 jz .done
 mov word [_file_fault],2
 call aspect_abort
.done:
 pop bp
 ret

global aspect_flow_ftell
aspect_flow_ftell:
 push bp
 mov bp,sp
 push word [bp+4]
 call _aspect_file_tell
 pop bx
 cmp dx,0xffff
 jne .done
 cmp ax,0xffff
 jne .done
 mov word [_file_fault],3
 call aspect_abort
.done:
 pop bp
 ret

global aspect_flow_exit,aspect_flow_error,aspect_stack_error
aspect_flow_exit:
 inc word [_ended]
 ret
aspect_flow_error:
aspect_stack_error:
 push bp
 mov bp,sp
 cmp word [bp+4],105
 je .ok
 inc word [_abi_bad]
.ok:
 mov word [_file_fault],4
 call aspect_abort
 pop bp
 ret 2
; Position display disabled in this fixture; unexpected calls fail visibly.
global aspect_abort_tell,aspect_abort_format,aspect_abort_print
aspect_abort_tell:
aspect_abort_format:
aspect_abort_print:
 inc word [_abi_bad]
 ret

SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_flow_stream,aspect_flow_wait_gate,aspect_flow_depth,aspect_flow_frame
 global aspect_flow_local_count,aspect_flow_locals,aspect_stack_pointer,aspect_stack_arena
 global aspect_dispatch_stream,aspect_dispatch_argument,aspect_dispatch_exit_state
 global aspect_abort_display_position,aspect_abort_format_string
 global _flow_depth,_flow_frame,_stack_pointer,_stack_arena,_ended,_file_fault
 global _abi_bad,_value_low,_value_high,_context_guard,_exit_state
aspect_flow_stream:
aspect_dispatch_stream: dw _stream_owner
aspect_flow_wait_gate: dw 0
aspect_flow_depth:
_flow_depth: dw 0
aspect_flow_frame:
_flow_frame: dw 0
aspect_flow_local_count: dw 0
aspect_flow_locals: times 36 db 0
_context_guard: dw 0xa55a
aspect_dispatch_argument: times 10 db 0
 dw 0x5aa5
aspect_dispatch_exit_state:
_exit_state: dw 0
aspect_abort_display_position: dw 0
aspect_abort_format_string: db 'owned fixture',0
saved_sp: dw 0
saved_bp: dw 0
_ended: dw 0
_file_fault: dw 0
_abi_bad: dw 0
_value_low: dw 0
_value_high: dw 0
aspect_stack_pointer:
_stack_pointer: dw 0
aspect_stack_arena:
_stack_arena: times 0x3aca db 0xa5
 db 0x5a
