; Maintained bounded, nonblocking sender for proved 12-byte keyboard bindings.
; The original emitter translates stored FF to wire NUL. File/slot selection and
; original blocking pacing are separate from this foreground TX-ring adapter.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_keymap,terminal_quit,terminal_exit_code
extern terminal_tx_count,terminal_enqueue_user_al
global terminal_enqueue_key_slot

; AX = zero-based binding slot, 0..78. DS=SS, DF=0.
; Return AX: 0 queued/empty, 2 bad slot, 3 unterminated binding,
; 4 insufficient TX capacity, 5 application already stopping.
; Preserve BX/CX/DX/BP/SI/DI/ES. Validate the entire binding and reserve its
; capacity before enqueueing any byte; no interrupts, UART IO or busy wait.
terminal_enqueue_key_slot:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 cmp word [terminal_quit],0
 jne .stopping
 cmp ax,79
 jae .bad_slot
 mov bx,12
 mul bx
 mov si,terminal_keymap
 add si,ax
 mov di,si
 xor cx,cx
.scan:
 cmp byte [di],0
 je .capacity
 inc di
 inc cx
 cmp cx,12
 jb .scan
 mov ax,3
 jmp .bad_binding
.capacity:
 mov dx,1024
 sub dx,[terminal_tx_count]
 jc .overflow
 cmp dx,cx
 jb .overflow
 jcxz .success
.send:
 lodsb
 cmp al,0xff
 jne .byte
 xor al,al
.byte:
 call terminal_enqueue_user_al
 loop .send
.success:
 xor ax,ax
 jmp .done
.bad_slot:
 mov ax,2
.bad_binding:
 mov word [terminal_exit_code],4
 mov word [terminal_quit],1
 jmp .done
.overflow:
 mov word [terminal_exit_code],3
 mov word [terminal_quit],1
 mov ax,4
 jmp .done
.stopping:
 mov ax,5
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
