; Maintained bounded byte-feed adapter around the actual recovered matcher.
; reset(): CF0 AX0; feed(uint16 byte): CF0 AXindex0..10/ffff(no completion).
; Errors CF1 AX1 unterminated slot/2bad cursor/3non-byte input; no state mutation.
; Near C; caller cleans feed2bytes. DS=SS, DF clear. Preserves BP/BX/CX/DX/SI/DI.
; Private one-byte source bounds each feed to one consumed byte. No UART or clock.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global modem_responses_reset_bounded,modem_responses_feed_bounded,modem_response_read_byte
extern modem_response_match_original,modem_response_slots,modem_response_cursors
extern modem_response_available,modem_response_input_byte
%macro save 0
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
%endmacro
%macro restore 0
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
%endmacro
modem_responses_reset_bounded:
 save
 xor dx,dx
 call validate_slots
 jc .done
 xor ax,ax
 inc ax
 push ax
 call modem_response_match_original
 pop bx
 xor ax,ax
 clc
.done:
 restore
modem_responses_feed_bounded:
 save
 mov ax,[bp+4]
 cmp ax,255
 ja .invalid_byte
 mov dx,1
 call validate_slots
 jc .done
 mov ax,[bp+4]
 mov [modem_response_input_byte],al
 mov word [modem_response_available],1
 xor ax,ax
 push ax
 call modem_response_match_original
 pop bx
 clc
 jmp .done
.invalid_byte:
 mov ax,3
 stc
.done:
 restore
; DX0=slot validation only, DX1=also validate all11 cursor pointers.
validate_slots:
 mov bx,modem_response_slots
 mov si,modem_response_cursors
.slot:
 mov di,bx
 mov cx,16
.find_nul:
 cmp byte [di],0
 je .found
 inc di
 loop .find_nul
 mov ax,1
 stc
 ret
.found:
 or dx,dx
 jz .next
 mov ax,[si]
 cmp ax,bx
 jb .bad_cursor
 cmp ax,di
 ja .bad_cursor
.next:
 add bx,16
 add si,2
 cmp si,modem_response_cursors+22
 jb .slot
 xor ax,ax
 clc
 ret
.bad_cursor:
 mov ax,2
 stc
 ret
; Actual one-byte adapter, matching original UART-read near ABI RET2.
; The bounded feed owns this availability/input state; no callback stub or I/O.
modem_response_read_byte:
 xor ax,ax
 mov al,[modem_response_input_byte]
 mov word [modem_response_available],0
 ret 2
