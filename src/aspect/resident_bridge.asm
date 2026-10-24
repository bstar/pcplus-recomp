; Source-owned mechanical resident call bridge, 8086 OMF, DS=SS on each side.
; No application admission, callback pointer/MCB validation or ASIO publication
; is provided here. The owning application must validate those before install.
; All mutable anchors are CS-relative, consuming no parent near DATA/STACK.
;
; initialize NEAR, parent DS=SS: BX=low/CX=top of unused parent stack slice,
; DX=near body in this CS, SI:DI=callback segment:offset. AX=0 or RB_ARGUMENT.
; Low/top exclude 16-byte redzones. Preserve BX/CX/DX/SI/DI/BP/DS/ES/FLAGS.
; disable NEAR must run outside a call; returns AX0 or RB_REENTRY.
; entry FAR: AX=request, BX=value, AX=result; every other register and FLAGS
; preserved. Body AX/BX are inputs; preserve DS/SS, other registers volatile.
; Body starts DS=SS=parent, DF0,
; IF inherited. callback NEAR forwards AX/BX to the installed FAR trampoline;
; that trampoline must restore parent DS=SS and its caller frame itself.
; abort NEAR jumps to the captured body return frame, AX=typed error. Only
; valid synchronously inside this bridge, never from an interrupt or caller.
BITS 16
CPU 8086
%include "resident_bridge.inc"
%ifdef RESIDENT_BRIDGE_FAR
SEGMENT ASPECT_CODE public class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global resident_bridge_initialize,resident_bridge_disable,resident_bridge_entry
global resident_bridge_callback,resident_bridge_abort
global resident_bridge_caller_ds
resident_bridge_caller_ds:
 mov ax,[cs:rb_caller_ss]
 ret
resident_bridge_initialize:
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 mov bp,sp
 cli
 mov ax,RB_REENTRY
 cmp word [cs:rb_busy],0
 jne .done
 mov ax,ss
 push ds
 pop es
 push dx
 mov dx,es
 cmp ax,dx
 pop dx
 jne .bad
 cmp bx,RB_GUARD_BYTES
 jb .bad
 cmp cx,0xfff0
 ja .bad
 cmp cx,bx
 jbe .bad
 mov ax,cx
 sub ax,bx
 cmp ax,RB_MIN_STACK
 jb .bad
 mov ax,bx
 or ax,cx
 test ax,1
 jnz .bad
 mov ax,sp
 cmp ax,RB_SUSPENDED_MARGIN
 jb .bad
 sub ax,RB_SUSPENDED_MARGIN
 cmp cx,ax
 ja .bad
 or dx,dx
 jz .bad
 mov ax,si
 or ax,di
 jz .bad
 mov [cs:rb_low],bx
 mov [cs:rb_top],cx
 mov [cs:rb_body],dx
 mov [cs:rb_callback],di
 mov [cs:rb_callback+2],si
 mov ax,ds
 mov [cs:rb_ds],ax
 ; Existing stack storage belongs to the owner, not a new near allocation.
 mov di,bx
 sub di,RB_GUARD_BYTES
 push cx
 mov cx,RB_GUARD_BYTES
 mov al,0xa6
 cld
 rep stosb
 pop di
 mov cx,RB_GUARD_BYTES
 mov al,0x5a
 rep stosb
 mov word [cs:rb_ready],1
 xor ax,ax
 jmp .done
.bad:
 mov ax,RB_ARGUMENT
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 ret

resident_bridge_disable:
 pushf
 cli
 mov ax,RB_REENTRY
 cmp word [cs:rb_busy],0
 jne .done
 mov word [cs:rb_ready],0
 xor ax,ax
.done:
 popf
 ret

resident_bridge_entry:
 RB_SAVE
 mov bp,sp
 cli
 mov ax,RB_INACTIVE
 cmp word [cs:rb_ready],1
 jne rb_refuse
 mov ax,RB_REENTRY
 cmp word [cs:rb_busy],0
 jne rb_refuse
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 mov ax,RB_ARGUMENT
 jne rb_refuse
 mov word [cs:rb_busy],1
 mov [cs:rb_caller_ss],ss
 mov [cs:rb_caller_sp],sp
 mov ax,[ss:bp+RB_FRAME_FLAGS]
 mov [cs:rb_flags],ax
 mov ax,[ss:bp+RB_FRAME_AX]
 mov bx,[ss:bp+RB_FRAME_BX]
 mov dx,[cs:rb_ds]
 mov ss,dx
 mov sp,[cs:rb_top]
 mov ds,dx
 mov es,dx
 mov [cs:rb_body_sp],sp
 mov dx,[cs:rb_flags]
 and dx,0xfbff
 push dx
 popf
 push ax
 call rb_check_guards
 or ax,ax
 pop ax
 jnz rb_stack_bad
 call word [cs:rb_body]
rb_finish:
 mov [cs:rb_result],ax
 call rb_check_guards
 or ax,ax
 jz .restore
 mov word [cs:rb_result],RB_STACK
.restore:
 cli
 mov word [cs:rb_busy],0
 mov ax,[cs:rb_caller_ss]
 mov dx,[cs:rb_caller_sp]
 mov ss,ax
 mov sp,dx
 mov ds,ax
 mov bp,sp
 mov ax,[cs:rb_result]
 mov [ss:bp+RB_FRAME_AX],ax
 RB_RETURN
rb_stack_bad:
 mov ax,RB_STACK
 jmp rb_finish
rb_refuse:
 mov [ss:bp+RB_FRAME_AX],ax
 RB_RETURN

resident_bridge_abort:
 cli
 mov sp,[cs:rb_body_sp]
 ; Do not restore entry IF until the valid captured parent stack is installed.
 mov dx,[cs:rb_flags]
 and dx,0xfbff
 push dx
 popf
 jmp rb_finish

resident_bridge_callback:
 call far [cs:rb_callback]
 ret

; AX0 good, RB_STACK bad; preserve the body's BX value and all other registers.
rb_check_guards:
 push bx
 push cx
 mov bx,[cs:rb_low]
 sub bx,RB_GUARD_BYTES
 mov cx,RB_GUARD_BYTES
.low:
 cmp byte [bx],0xa6
 jne .bad
 inc bx
 loop .low
 mov bx,[cs:rb_top]
 mov cx,RB_GUARD_BYTES
.high:
 cmp byte [bx],0x5a
 jne .bad
 inc bx
 loop .high
 xor ax,ax
 jmp .done
.bad:
 mov ax,RB_STACK
.done:
 pop cx
 pop bx
 ret

rb_ready: dw 0
global resident_bridge_busy
resident_bridge_busy:
rb_busy: dw 0
rb_ds: dw 0
rb_low: dw 0
rb_top: dw 0
rb_body: dw 0
rb_callback: dd 0
rb_caller_ss: dw 0
rb_caller_sp: dw 0
rb_body_sp: dw 0
rb_flags: dw 0
rb_result: dw 0
