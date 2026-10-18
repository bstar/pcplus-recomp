; Source-only host for the reconstructed parameter reader.
; The byte provider uses caller-owned near memory; end of input models a timeout.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern ansi_read_parameter
global ansi_next_byte, ansi_unread_byte, ansi_control_character, ansi_reset
ansi_next_byte:
 mov bx,[ansi_input_position]
 cmp bx,[ansi_input_length]
 jae .timeout
 inc word [ansi_input_position]
 add bx,[ansi_input_pointer]
 xor ax,ax
 mov al,[bx]
 ret
.timeout:
 mov ax,0xffff
 ret
ansi_unread_byte:
 cmp word [ansi_input_position],0
 je .done
 dec word [ansi_input_position]
.done:
 ret
ansi_control_character:
 mov bx,sp
 mov ax,[bx+2]
 mov [ansi_last_control],ax
 inc word [ansi_control_count]
 ret
ansi_reset:
 push ax
 push cx
 push di
 push es
 mov ax,ds
 mov es,ax
 xor ax,ax
 mov di,ansi_parameters
 mov cx,16
 cld
 rep stosw
 mov [ansi_parameter_count],ax
 mov [ansi_command],ax
 mov [ansi_private],ax
 mov [ansi_secondary],ax
 mov [ansi_parse_error],ax
 mov [ansi_input_position],ax
 mov [ansi_control_count],ax
 mov [ansi_last_control],ax
 pop es
 pop di
 pop cx
 pop ax
 ret
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 call ansi_reset
 call ansi_read_parameter
 cmp ax,'S'
 jne .failed
 cmp word [ansi_command],';'
 jne .failed
 call ansi_read_parameter
 cmp ax,'S'
 jne .failed
 cmp word [ansi_command],'H'
 jne .failed
 cmp word [ansi_parameter_count],2
 jne .failed
 cmp word [ansi_parameters],12
 jne .failed
 cmp word [ansi_parameters+2],34
 jne .failed
 cmp word [ansi_parse_error],0
 jne .failed
 ; Confirm malformed digit runs abort without changing the canary.
 mov word [ansi_input_pointer],overflow_sample
 mov word [ansi_input_length],41
 call ansi_reset
 call ansi_read_parameter
 cmp ax,'A'
 jne .failed
 cmp word [ansi_parse_error],1
 jne .failed
 cmp word [ansi_parameter_canary],0xa55a
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
global ansi_parameters
ansi_parameters: times 16 dw 0
wordvar ansi_parameter_canary,0xa55a
wordvar ansi_parameter_count,0
wordvar ansi_command,0
wordvar ansi_private,0
wordvar ansi_secondary,0
wordvar ansi_parse_error,0
wordvar ansi_input_position,0
wordvar ansi_input_pointer,sample
wordvar ansi_input_length,6
wordvar ansi_control_count,0
wordvar ansi_last_control,0
sample: db '12;34H'
overflow_sample: times 40 db '1'
 db 'H'
SEGMENT _BSS public align=16 class=BSS use16
global ansi_input_buffer
ansi_input_buffer: resb 2048
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
