; Isolated test fixture: callbacks RECORD requests; they do not implement a terminal.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern ansi_escape_entry
%macro service 2
 global %1
 %1:
 mov word [escape_last_service],%2
 inc word [escape_service_calls]
 mov bx,sp
 mov ax,[bx+2]
 mov [escape_service_argument],ax
 ret
%endmacro
service ansi_escape_service_e0f8,0xe0f8
service ansi_escape_service_dd74,0xdd74
service ansi_escape_service_ddbc,0xddbc
service ansi_escape_service_da46,0xda46
service ansi_escape_service_12c8,0x12c8
service ansi_escape_service_dac6,0xdac6
service ansi_escape_service_da84,0xda84
service ansi_escape_service_ec94,0xec94
service ansi_escape_service_dd58,0xdd58
service ansi_escape_service_20a4,0x20a4
global ansi_next_byte,ansi_unread_byte
ansi_next_byte:
 mov bx,[escape_input_position]
 cmp bx,[escape_input_length]
 jae .empty
 inc word [escape_input_position]
 xor ax,ax
 mov al,[escape_input_buffer+bx]
 ret
.empty:
 mov ax,0xffff
 ret
ansi_unread_byte:
 dec word [escape_input_position]
 inc word [escape_unread_calls]
 ret
%macro token 2
 global %1
 %1:
 inc word [%2]
 mov bx,[escape_token_position]
 shl bx,1
 mov ax,[escape_tokens+bx]
 inc word [escape_token_position]
 ret
%endmacro
token ansi_read_parameter,escape_parameter_calls
token ansi_parameter_transition,escape_transition_calls
token ansi_dispatch_command,escape_dispatch_calls
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 call ansi_escape_entry
 cmp word [escape_last_service],0xdac6
 jne .failed
 cmp word [escape_service_calls],1
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
%macro wordvar 2
 global %1
 %1: dw %2
%endmacro
wordvar ansi_parameter_count,0x5555
wordvar ansi_parameters,0x5555
wordvar ansi_private,0x5555
wordvar ansi_secondary,0x5555
wordvar ansi_charset_g0_flag_a,0x5555
wordvar ansi_charset_g0_flag_graphics,0x5555
wordvar ansi_charset_g1_flag_a,0x5555
wordvar ansi_charset_g1_flag_graphics,0x5555
wordvar escape_input_position,0
wordvar escape_input_length,1
wordvar escape_last_service,0
wordvar escape_service_argument,0
wordvar escape_service_calls,0
wordvar escape_unread_calls,0
wordvar escape_parameter_calls,0
wordvar escape_transition_calls,0
wordvar escape_dispatch_calls,0
wordvar escape_token_position,0
global escape_tokens,escape_input_buffer
escape_tokens: times 64 dw 'A'
escape_input_buffer: db 'H'
 times 2047 db 0
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
