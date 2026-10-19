; Exact PCPlus2.01 overlay16 D0D0..D194 typed value-stack primitives.
; Retained REA listings: analysis/pcplus-overlay-anchored-16/functions/
; 0x1d0d0.asm,0x1d0f2.asm,0x1d110.asm,0x1d134.asm,0x1d157.asm,
; 0x1d17a.asm,0x1d186.asm. Original executable SHA256:
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS and DF=0, near ABI; reserve/push consume arguments (RET2 or RET4); pop RET.
; Preserve BP/SI/DI; ES/AX/BX/CX/DX/flags volatile. Copy backend is native85B4.
; Native reserve adds16-bit length without checking carry or lower bound,
; compares unsigned against arena+3ACA, and invokes error105 if greater.
; If error returns, pushes continue. Pop never checks underflow. Pointer wrap,
; unchecked reads/writes and nonlocal error behavior are deliberately preserved.
; This recovery is not a safe independently usable production value stack.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_STACK_FLAT
ORG 0xd0d0
%define aspect_stack_pointer 0xe13c
%define aspect_stack_arena 0x9062
%define aspect_stack_error 0x4efb
%define aspect_stack_copy 0x85b4
%else
SEGMENT _TEXT public class=CODE use16
global aspect_stack_reserve,aspect_stack_push_word,aspect_stack_push_dword
global aspect_stack_push_eight,aspect_stack_push_string
global aspect_stack_pop_word,aspect_stack_pop_dword
extern aspect_stack_pointer,aspect_stack_arena,aspect_stack_error,erase_move_bytes
%define aspect_stack_copy erase_move_bytes
%endif
aspect_stack_reserve:
 push bp
 mov_load bp,sp
 mov ax,[bp+4]
 add ax,[aspect_stack_pointer]
 mov cx,aspect_stack_arena
 add cx,0x3aca
 cmp_load ax,cx
 jbe .done
 mov ax,105
 push ax
 call aspect_stack_error
.done:
 mov_load sp,bp
 pop bp
 ret 2
aspect_stack_push_word:
 push bp
 mov_load bp,sp
 mov ax,2
 push ax
 call aspect_stack_reserve
 mov ax,[bp+4]
 mov bx,[aspect_stack_pointer]
 mov [bx],ax
 add word [aspect_stack_pointer],byte 2
 mov_load sp,bp
 pop bp
 ret 2
aspect_stack_push_dword:
 push bp
 mov_load bp,sp
 mov ax,4
 push ax
 call aspect_stack_reserve
 mov ax,[bp+4]
 mov dx,[bp+6]
 mov bx,[aspect_stack_pointer]
 mov [bx],ax
 mov [bx+2],dx
 add word [aspect_stack_pointer],byte 4
 mov_load sp,bp
 pop bp
 ret 4
aspect_stack_push_eight:
 push bp
 mov_load bp,sp
 mov ax,8
 push ax
 call aspect_stack_reserve
 mov ax,8
 push ax
 push word [bp+4]
 push word [aspect_stack_pointer]
 call aspect_stack_copy
 add word [aspect_stack_pointer],byte 8
 mov_load sp,bp
 pop bp
 ret 2
aspect_stack_push_string:
 push bp
 mov_load bp,sp
 mov ax,81
 push ax
 call aspect_stack_reserve
 mov ax,81
 push ax
 push word [bp+4]
 push word [aspect_stack_pointer]
 call aspect_stack_copy
 add word [aspect_stack_pointer],byte 81
 mov_load sp,bp
 pop bp
 ret 2
aspect_stack_pop_word:
 sub word [aspect_stack_pointer],byte 2
 mov bx,[aspect_stack_pointer]
 mov ax,[bx]
 ret
aspect_stack_pop_dword:
 sub word [aspect_stack_pointer],byte 4
 mov bx,[aspect_stack_pointer]
 mov ax,[bx]
 mov dx,[bx+2]
 ret
