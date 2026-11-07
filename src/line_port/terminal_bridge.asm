BITS 16
CPU 8086
SEGMENT LINE_PORT_CODE public align=16 class=FARCODE use16
extern keyboard_bank_terminal_setup_start,terminal_program_kind
global _line_port_queue
_line_port_queue:
 call far keyboard_bank_terminal_setup_start
 or ax,ax
 jnz .done
 mov word [terminal_program_kind],12
.done:
 retf
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
extern terminal_redisplay_key_impl,_redisplay_active
global _line_port_reopen
_line_port_reopen:
 mov ax,1900h
 call terminal_redisplay_key_impl
 mov ax,[_redisplay_active]
 retf
