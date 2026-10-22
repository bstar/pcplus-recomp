; Owned ASPECT BIOS selection over the recovered acquisition component.
; No private application queue, no second foreground reader. DS=SS.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern keyboard_bios_read,keyboard_bios_peek,keyboard_detect_bios_mode
global _runtime_keyboard_read,_runtime_keyboard_peek,_runtime_keyboard_auto
global _runtime_keyboard_cancel_pending
_runtime_keyboard_read: jmp keyboard_bios_read
_runtime_keyboard_peek: jmp keyboard_bios_peek
_runtime_keyboard_cancel_pending:
 call far keyboard_cancel_pending
 ret
_runtime_keyboard_auto:
 mov word [_runtime_keyboard_mode],0
 jmp keyboard_detect_bios_mode
SEGMENT KEYBOARD_CODE public align=16 class=FARCODE use16
; Only the standard IBM-compatible16-word ring is admitted. Preserve raw
; ordinary/extended words and their order; remove the first low-byte Escape.
; All work is bounded under CLI, with caller FLAGS and DS=SS unchanged.
keyboard_cancel_pending:
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov ax,0x40
 mov es,ax
 cli
 mov ax,[es:0x80]
 or ax,[es:0x82]
 jz .bounds
 cmp word [es:0x80],0x1e
 jne .none
 cmp word [es:0x82],0x3e
 jne .none
.bounds:
 mov bx,[es:0x1a]
 mov dx,[es:0x1c]
 mov ax,bx
 or ax,dx
 test al,1
 jnz .none
 cmp bx,0x1e
 jb .none
 cmp bx,0x3e
 jae .none
 cmp dx,0x1e
 jb .none
 cmp dx,0x3e
 jae .none
 mov cx,16
.scan:
 cmp bx,dx
 je .none
 cmp byte [es:bx],27
 je .found
 add bx,2
 cmp bx,0x3e
 jb .next
 mov bx,0x1e
.next:
 loop .scan
.none:
 xor ax,ax
 jmp .done
.found:
 mov di,bx
.shift:
 mov si,di
 add si,2
 cmp si,0x3e
 jb .source
 mov si,0x1e
.source:
 cmp si,dx
 je .retire
 mov ax,[es:si]
 mov [es:di],ax
 mov di,si
 jmp .shift
.retire:
 mov [es:0x1c],di
 mov ax,1
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 retf
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global _runtime_keyboard_mode,keyboard_bios_mode
_runtime_keyboard_mode:
keyboard_bios_mode: dw 0
