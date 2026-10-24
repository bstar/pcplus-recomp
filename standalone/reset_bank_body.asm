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
%ifdef RESET_BANK_OVERLAY
extern redisplay_snapshot
%endif
global reset_bank_body,reset_bank_allocate,reset_bank_free,reset_bank_error
global reset_bank_observation,reset_bank_wait
reset_bank_observation: times 10 dw 0
reset_bank_wait: dw 0
reset_bank_body:
%ifdef RESET_BANK_TRANSACTION
 extern reset_live_prepare,reset_live_finish
 cmp word [cs:reset_bank_request],0x100
 je .live
 cmp word [cs:reset_bank_request],0x101
 je .live
%endif
%ifdef RESET_BANK_APP
 cmp word [cs:reset_bank_request],1
 jbe .observe
 mov ax,1
 ret
%else
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
%endif
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
%ifndef RESET_BANK_APP
 cmp ax,3
 jne .request
 mov ax,1
.request:
%endif
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
%ifndef RESET_BANK_APP
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
%endif
 xor ax,ax
 ret
%ifdef RESET_BANK_TRANSACTION
.live:
 call terminal_reset_test_initialize
 call reset_live_prepare
 mov ax,[cs:reset_bank_request]
 and ax,1
 push ax
 call modes_width_request_native
 call reset_live_finish
 xor ax,ax
 ret
%endif
reset_bank_allocate:
 mov bx,sp
 cmp word [bx+2],6336
 jne reset_bank_error
 mov ax,bank_shadow
%ifdef RESET_BANK_OVERLAY
 mov dx,seg redisplay_snapshot
%else
 mov dx,seg bank_shadow
%endif
 ret
reset_bank_free:
 mov bx,sp
 cmp word [bx+2],bank_shadow
 jne reset_bank_error
%ifdef RESET_BANK_OVERLAY
 mov ax,seg redisplay_snapshot
%else
 mov ax,seg bank_shadow
%endif
 cmp [bx+4],ax
 jne reset_bank_error
 ret
reset_bank_error:
 mov ax,3
 jmp reset_bank_abort
global bank_shadow,bank_shadow_end
%ifdef RESET_BANK_OVERLAY
bank_shadow equ 0xe700
bank_shadow_end equ 0xffc0
%else
SEGMENT BANK_SHADOW public align=16 class=FAR_DATA use16
bank_shadow: resb 6336
bank_shadow_end:
%endif
SEGMENT _DATA public align=16 class=DATA use16
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
%ifdef RESET_BANK_APP
SEGMENT RESET_DATA public align=16 class=NATIVE_DATA use16
%else
SEGMENT RESET_DATA public align=16 class=DATA use16
%endif
