; Real DOS driver/init plus native far callback tests. No physical input injected.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern mouse_probe,mouse_init,mouse_callback,mouse_depth
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov ax,1
 push ax
 call mouse_probe
 or ax,ax
 jz failed
 mov ax,1
 push ax
 mov ax,8
 push ax
 mov ax,4
 push ax
 call mouse_init
 cmp word [mouse_present],0xffff
 jne failed
 cmp word [mouse_scale_x],8
 jne failed
 cmp word [mouse_scale_y],4
 jne failed
 cmp word [mouse_count],0
 jne failed
 ; Native mickey division and horizontal tie selection: dx2,dy2.
 mov ax,1
 mov si,16
 mov di,8
 call emit
 cmp word [mouse_count],2
 jne failed
 cmp word [mouse_code],1
 jne failed
 cmp word [mouse_base_x],16
 jne failed
 cmp word [mouse_base_y],8
 jne failed
 ; An undrained event blocks motion and preserves the baseline.
 mov ax,1
 mov si,24
 mov di,16
 call emit
 cmp word [mouse_base_x],16
 jne failed
 mov word [mouse_count],0
 mov ax,1
 mov si,24
 mov di,16
 call emit
 cmp word [mouse_code],2
 jne failed
 cmp word [mouse_count],2
 jne failed
 ; Buttons override pending motion; left wins simultaneous button presses.
 mov ax,0x0a
 call emit
 cmp word [mouse_code],4
 jne failed
 cmp word [mouse_button_pending],1
 jne failed
 cmp word [mouse_count],1
 jne failed
 ; Disabled right button must not overwrite the prior event.
 mov byte [mouse_enabled+5],0
 mov ax,8
 call emit
 cmp word [mouse_code],4
 jne failed
 ; Busy callback entry skips event processing and balances its CS depth.
 mov word [cs:mouse_depth],0
 mov ax,2
 call emit
 cmp word [cs:mouse_depth],0
 jne failed
 mov word [cs:mouse_depth],0xffff
 cmp word [mouse_code],4
 jne failed
 call detach
 mov bx,1
 mov dx,success
 mov cx,success_end-success
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,success_end-success
 jne failed
 mov ax,0x4c00
 int 0x21
emit:
 ; The callback installs its own DS while borrowing a genuinely foreign SS.
 push ds
 cli
 mov [cs:emit_ss],ss
 mov [cs:emit_sp],sp
 mov bx,seg foreign_stack_top
 mov ss,bx
 mov sp,foreign_stack_top
 mov bx,0x40
 mov ds,bx
 call far [cs:callback_pointer]
 mov bx,ds
 mov ax,ss
 mov [cs:emit_foreign_ss],ax
 mov ax,[cs:emit_ss]
 mov ss,ax
 mov sp,[cs:emit_sp]
 pop ds
 cmp bx,0x40
 jne failed
 mov dx,seg foreign_stack_top
 cmp [cs:emit_foreign_ss],dx
 jne failed
 pushf
 pop bx
 test bx,0x200
 jnz failed
 sti
 ret
detach:
 ; Retire our callback before its owning DOS allocation can terminate.
 push cs
 pop es
 xor dx,dx
 xor cx,cx
 mov ax,0x0c
 int 0x33
 ret
failed:
 call detach
 mov ax,0x4c01
 int 0x21
callback_pointer: dw mouse_callback,seg mouse_callback
emit_ss: dw 0
emit_sp: dw 0
emit_foreign_ss: dw 0
SEGMENT _DATA public align=16 class=DATA use16
global mouse_enabled,mouse_scale_x,mouse_scale_y,mouse_present,mouse_flags
global mouse_motion_x,mouse_motion_y,mouse_base_x,mouse_base_y
global mouse_button_pending,mouse_count,mouse_code
mouse_enabled: times 6 db 1
mouse_scale_x: dw 0
mouse_scale_y: dw 0
mouse_present: dw 0
mouse_flags: dw 0
mouse_motion_x: dw 0
mouse_motion_y: dw 0
mouse_base_x: dw 0
mouse_base_y: dw 0
mouse_button_pending: dw 0
mouse_count: dw 0
mouse_code: dw 0
success: db 'PASS native mouse',13,10
success_end:
SEGMENT STACK stack align=16 class=STACK use16
resb 4096
stack_top:
SEGMENT MOUSESTACK private align=16 class=DATA use16
resb 512
foreign_stack_top:
