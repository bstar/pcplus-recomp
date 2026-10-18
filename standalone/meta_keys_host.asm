; Declared diagnostic fixtures for unrecovered ASPECT/program/UI dependencies.
; No executable is spawned and no ASPECT/HOOK program is emulated here.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern meta_keys_invoke,meta_keys_expand,meta_keys_hook,meta_keys_strcpy
extern meta_keys_send_text,meta_keys_alt_digit
extern meta_keys_decimal16,meta_keys_decimal32
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 mov ax,0
 mov es,ax
 mov ax,[es:0x46c]
 mov [start_ticks],ax
 mov ax,3
 push ax
 push ax
 mov ax,macro_fixture
 push ax
 call meta_keys_invoke
 add sp,6
 cmp word [wire_count],3
 jne .fail
 cmp byte [wire_bytes],0
 jne .fail
 cmp byte [wire_bytes+1],'A'
 jne .fail
 cmp byte [wire_bytes+2],'B'
 jne .fail
 xor ax,ax
 mov es,ax
 mov ax,[es:0x46c]
 sub ax,[start_ticks]
 cmp ax,10
 jb .fail
 ; Actual Alt1 consumer indexes record0 and dispatches kind3 text.
 mov word [meta_normalized_scan],0x78
 mov word [meta_actions],3
 mov byte [meta_actions+2],'Z'
 mov byte [meta_actions+3],0
 call meta_keys_alt_digit
 cmp word [wire_count],4
 jne .fail
 cmp byte [wire_bytes+3],'Z'
 jne .fail
 mov ax,0x4c00
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21
; Cdecl bridge for original callee-cleanup hook(4 words) and near test driver.
global meta_hook_call
meta_hook_call:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call meta_keys_hook
 pop bp
 ret

global meta_keys_transmit,meta_keys_echo,meta_keys_message
meta_keys_transmit:
 push bp
 mov bp,sp
 push bx
 mov bx,[wire_count]
 mov ax,[bp+4]
 mov [wire_bytes+bx],al
 inc word [wire_count]
 pop bx
 pop bp
 ret 2
meta_keys_echo:
 inc word [echo_count]
 ret
meta_keys_message:
 mov [last_message],bx
 inc word [message_count]
 ret

global meta_keys_aspect_service,meta_keys_program_service,meta_keys_resolve_program
meta_keys_aspect_service:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [aspect_arg0],ax
 mov ax,[bp+6]
 mov [aspect_arg1],ax
 inc word [aspect_count]
 pop bp
 ret 4
meta_keys_resolve_program:
 ; Explicit identity resolver fixture, not a reconstructed DOS PATH search.
 mov bx,sp
 mov ax,[bx+2]
 inc word [resolve_count]
 ret
meta_keys_program_service:
 push bp
 mov bp,sp
 push si
 push di
 mov si,bp
 add si,4
 mov di,program_arguments
 push ds
 pop es
 mov cx,5
 rep movsw
 inc word [program_count]
 cmp word [program_arguments+2],0
 je .done
 push word [program_arguments+2]
 mov ax,program_command
 push ax
 call meta_keys_strcpy
 add sp,4
.done:
 mov ax,[program_return]
 pop di
 pop si
 pop bp
 ret

SEGMENT _DATA public align=16 class=DATA use16
%macro wordvar 2
 global %1
 %1: dw %2
%endmacro
wordvar meta_script_active,0
wordvar meta_pacing,0
wordvar meta_local_echo,0
wordvar meta_normalized_scan,0x78
wordvar meta_hook_result,0
wordvar meta_pace_counter,0
wordvar meta_pace_calibration,1
wordvar wire_count,0
wordvar echo_count,0
wordvar message_count,0
wordvar aspect_count,0
wordvar program_count,0
wordvar resolve_count,0
wordvar program_return,0x1234
wordvar aspect_arg0,0
wordvar aspect_arg1,0
wordvar last_message,0
wordvar start_ticks,0
wordvar meta_prm_image,0
wordvar meta_hook_exchange_a,0
wordvar meta_hook_exchange_b,0
global meta_actions,meta_actions_text0,meta_pause_byte
global meta_script_busy_message,meta_missing_name_message
global meta_hook_prefix,meta_hook_space_a,meta_hook_space_b,meta_hook_space_c,meta_hook_space_d
global test_input,test_output,wire_bytes,program_arguments,program_command
meta_pause_byte: db '~'
meta_actions: dw 3
meta_actions_text0: times 52 db 0
 times 9*54 db 0
meta_script_busy_message: db 'Already in script file.  Chain not permitted',0
meta_missing_name_message: db 'No program name specified',0
meta_hook_prefix: db ' PCPLUS ',0
meta_hook_space_a: db ' ',0
meta_hook_space_b: db ' ',0
meta_hook_space_c: db ' ',0
meta_hook_space_d: db ' ',0
wire_bytes: times 1024 db 0
program_arguments: times 5 dw 0
program_command: times 256 db 0
test_input: times 256 db 0
test_output: times 256 db 0
macro_fixture: db '^@A~B',0
SEGMENT STACK stack align=16 class=STACK use16
 resb 4096
stack_top:
