; Native reset body for the dual-context integration diagnostic. The only
; allocation is an explicitly owned static6336-byte far shadow, never a root
; data allocation. Unsupported native services remain diagnostic boundaries.
BITS 16
CPU 8086
GROUP RESET_GROUP RESET_DATA
GROUP DGROUP _DATA _BSS STACK
SEGMENT RESET_CODE public align=16 class=FARCODE use16
extern terminal_reset_test_initialize,terminal_reset_width,modes_width_request_native
extern reset_bank_request,reset_bank_abort
extern reset_bank_call_far,reset_bank_busy
extern reset_configured_wide,program_state_7a74,terminal_dec_keys
extern csi_last_row,screen_last_row,screen_bottom_margin,screen_viewport_right
extern screen_attribute_row_bytes,screen_cursor_row,screen_cursor_column
extern uart_rx_count
global reset_bank_body,reset_bank_allocate,reset_bank_free,reset_bank_error
global reset_bank_observation,reset_bank_wait
reset_bank_observation: times 10 dw 0
reset_bank_wait: dw 0
reset_bank_body:
 cmp word [cs:reset_bank_request],2
 jne .normal
 push ax
 push bx
 mov ax,3
 jmp reset_bank_abort
.normal:
 cmp word [cs:reset_bank_request],3
 jne .observe
 mov ax,1
 call far reset_bank_call_far
 cmp ax,1
 jne reset_bank_error
 cmp word [cs:reset_bank_busy],1
 jne reset_bank_error
.observe:
 mov [cs:reset_bank_observation],ds
 mov [cs:reset_bank_observation+2],ss
 mov [cs:reset_bank_observation+4],sp
 pushf
 pop word [cs:reset_bank_observation+6]
 call terminal_reset_test_initialize
 xor ax,ax
 push ax
 call terminal_reset_width
 add sp,2
 mov word [program_state_7a74],24
 mov word [terminal_dec_keys],1
 mov word [csi_last_row],23
 mov word [screen_last_row],23
 mov word [screen_bottom_margin],23
 mov word [screen_viewport_right],79
 mov ax,[cs:reset_bank_request]
 cmp ax,3
 jne .request
 mov ax,1
.request:
 push ax
 call modes_width_request_native
 mov ax,[screen_attribute_row_bytes]
 mov [cs:reset_bank_observation+8],ax
 mov ax,[reset_configured_wide]
 mov [cs:reset_bank_observation+10],ax
 mov ax,[screen_cursor_row]
 mov [cs:reset_bank_observation+12],ax
 mov ax,[screen_cursor_column]
 mov [cs:reset_bank_observation+14],ax
 ; A bounded tick interval lets a real UART IRQ run on the private stack.
 cmp word [cs:reset_bank_wait],0
 je .done
 mov ax,DGROUP
 mov es,ax
 mov ax,[es:uart_rx_count]
 mov [cs:reset_bank_observation+16],ax
 mov dx,0x3fd
.transmit:
 in al,dx
 test al,0x20
 jz .transmit
 mov dx,0x3f8
 mov al,'B'
 out dx,al
 mov ax,0x40
 mov es,ax
 mov bx,[es:0x6c]
.wait:
 mov ax,[es:0x6c]
 sub ax,bx
 cmp ax,[cs:reset_bank_wait]
 jb .wait
 mov ax,DGROUP
 mov es,ax
 mov ax,[es:uart_rx_count]
 mov [cs:reset_bank_observation+18],ax
.done:
 xor ax,ax
 ret
reset_bank_allocate:
 mov bx,sp
 cmp word [bx+2],6336
 jne reset_bank_error
 mov ax,bank_shadow
 mov dx,seg bank_shadow
 ret
reset_bank_free:
 mov bx,sp
 cmp word [bx+2],bank_shadow
 jne reset_bank_error
 mov ax,seg bank_shadow
 cmp [bx+4],ax
 jne reset_bank_error
 ret
reset_bank_error:
 mov ax,3
 jmp reset_bank_abort
SEGMENT BANK_SHADOW public align=16 class=FAR_DATA use16
global bank_shadow,bank_shadow_end
bank_shadow: resb 6336
bank_shadow_end:
SEGMENT _DATA public align=16 class=DATA use16
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
SEGMENT RESET_DATA public align=16 class=DATA use16
