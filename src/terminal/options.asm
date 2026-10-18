; Maintained DOS command-tail parser. No DOS/BIOS/UART I/O is performed.
; AX=PSP segment, DS=SS. Returns AX=0 CF0 success, AX=1 CF1 help,
; AX=2 CF1 invalid. BP/SI/DI/ES preserved; BX/CX/DX/flags volatile.
; Validation stages all values privately before committing shared settings.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global terminal_parse_options
extern terminal_baud_low,terminal_baud_high,terminal_parity,terminal_data_bits,terminal_stop_bits
extern terminal_irq_vector,terminal_port_number
extern uart_port_index,uart_irq_indices,uart_port_rbr,uart_port_thr,uart_port_ier
extern uart_port_lcr,uart_port_mcr,uart_port_lsr,uart_port_msr
extern uart_software_flow,uart_hardware_flow
terminal_parse_options:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov dx,ax
 mov ax,ds
 mov es,ax
 mov si,options_defaults
 mov di,options_stage
 mov cx,8
 cld
 rep movsw
 mov byte [options_seen],0
 mov di,options_config_stage
 xor ax,ax
 mov cx,32
 rep stosw
 mov di,options_dial_stage
 mov cx,32
 rep stosw
 mov es,dx
 xor cx,cx
 mov cl,[es:0x80]
 cmp cx,127
 ja .invalid
 mov si,0x81
.skip:
 or cx,cx
 jnz .nonempty
 jmp .commit
.nonempty:
 mov al,[es:si]
 cmp al,' '
 je .separator
 cmp al,9
 jne .token
.separator:
 inc si
 dec cx
 jmp .skip
.token:
 xor di,di
.copy:
 jcxz .token_done
 mov al,[es:si]
 cmp al,' '
 je .token_done
 cmp al,9
 je .token_done
 cmp al,0x21
 jb .invalid
 cmp al,0x7e
 ja .invalid
 cmp di,66
 jae .invalid
 mov [options_raw_token+di],al
 cmp al,'a'
 jb .store
 cmp al,'z'
 ja .store
 sub al,32
.store:
 mov [options_token+di],al
 inc di
 inc si
 dec cx
 jmp .copy
.token_done:
 mov byte [options_token+di],0
 mov byte [options_raw_token+di],0
 cmp byte [options_token],'@'
 je .config_size
 cmp word [options_token],'/D'
 jne .ordinary_size
 cmp byte [options_token+2],':'
 je .process
.ordinary_size:
 cmp di,15
 ja .invalid
 jmp .process
.config_size:
 cmp di,64
 ja .invalid
.process:
 push cx
 push si
 call options_process_token
 pop si
 pop cx
 jc .return
 jmp .skip
.commit:
 mov ax,[options_port]
 mov [terminal_port_number],ax
 dec ax
 shl ax,1
 mov bx,ax
 mov dx,[options_bases+bx]
 mov ax,[options_irqs+bx]
 mov [uart_irq_indices],ax
 add ax,8
 mov [terminal_irq_vector],ax
 mov word [uart_port_index],0
 mov [uart_port_rbr],dx
 mov [uart_port_thr],dx
 inc dx
 mov [uart_port_ier],dx
 add dx,2
 mov [uart_port_lcr],dx
 inc dx
 mov [uart_port_mcr],dx
 inc dx
 mov [uart_port_lsr],dx
 inc dx
 mov [uart_port_msr],dx
 mov ax,[options_baud_low]
 mov [terminal_baud_low],ax
 mov ax,[options_baud_high]
 mov [terminal_baud_high],ax
 mov ax,[options_parity]
 mov [terminal_parity],ax
 mov ax,[options_data]
 mov [terminal_data_bits],ax
 mov ax,[options_stop]
 mov [terminal_stop_bits],ax
 mov ax,[options_soft]
 mov [uart_software_flow],ax
 mov ax,[options_hard]
 mov [uart_hardware_flow],ax
 ; Commit only after the complete command tail has validated. No file is read.
 push ds
 pop es
 mov si,options_config_stage
 mov di,terminal_config_path
 mov cx,32
 rep movsw
 mov si,options_dial_stage
 mov di,terminal_dial_target
 mov cx,32
 rep movsw
 xor ax,ax
 mov al,[options_seen]
 mov [terminal_option_mask],ax
 xor ax,ax
 clc
 jmp .return
.invalid:
 mov ax,2
 stc
.return:
 pop es
 pop di
 pop si
 pop bp
 ret

; Match token against ASCIIZ AX; CF0 equal, CF1 different.
options_equal:
 push si
 push di
 mov si,options_token
 mov di,ax
.next:
 lodsb
 cmp al,[di]
 jne .different
 inc di
 or al,al
 jnz .next
 clc
 jmp .done
.different:
 stc
.done:
 pop di
 pop si
 ret

options_process_token:
 cmp byte [options_token],'@'
 jne .help_start
 test byte [options_seen],16
 jnz .bad
 mov si,options_token+1
 mov di,options_config_stage
 cmp byte [si],0
 je .bad
.config_copy:
 lodsb
 cmp al,'*'
 je .bad
 cmp al,'?'
 je .bad
 cmp al,34
 je .bad
 cmp al,39
 je .bad
 mov [di],al
 inc di
 or al,al
 jnz .config_copy
 or byte [options_seen],16
 jmp .good
.help_start:
 cmp word [options_token],'/D'
 jne .help_table
 cmp byte [options_token+2],':'
 jne .help_table
 test byte [options_seen],32
 jnz .bad
 mov si,options_raw_token+3
 mov di,options_dial_stage
 cmp byte [si],0
 je .bad
.dial_copy:
 lodsb
 or al,al
 jz .dial_done
 cmp al,'0'
 jb .dial_punctuation
 cmp al,'9'
 jbe .dial_store
 cmp al,'A'
 jb .dial_punctuation
 cmp al,'Z'
 jbe .dial_store
 cmp al,'a'
 jb .dial_punctuation
 cmp al,'z'
 jbe .dial_store
.dial_punctuation:
 mov bx,options_dial_punctuation
.dial_punctuation_loop:
 cmp byte [bx],0
 je .bad
 cmp al,[bx]
 je .dial_store
 inc bx
 jmp .dial_punctuation_loop
.dial_store:
 mov [di],al
 inc di
 jmp .dial_copy
.dial_done:
 mov byte [di],0
 or byte [options_seen],32
 jmp .good
.help_table:
 mov si,options_help_table
.help_loop:
 lodsw
 or ax,ax
 jz .port
 call options_equal
 jnc .help
 jmp .help_loop
.help:
 mov ax,1
 stc
 ret
.port:
 cmp word [options_token],'CO'
 jne .baud
 cmp byte [options_token+2],'M'
 jne .baud
 cmp byte [options_token+4],0
 jne .bad
 mov al,[options_token+3]
 cmp al,'1'
 jb .bad
 cmp al,'4'
 ja .bad
 test byte [options_seen],1
 jnz .bad
 or byte [options_seen],1
 sub al,'0'
 xor ah,ah
 mov [options_port],ax
 jmp .good
.baud:
 mov bx,options_bauds
.baud_loop:
 mov ax,[bx]
 or ax,ax
 jz .flow
 call options_equal
 jnc .baud_found
 add bx,6
 jmp .baud_loop
.baud_found:
 test byte [options_seen],2
 jnz .bad
 or byte [options_seen],2
 mov ax,[bx+2]
 mov [options_baud_low],ax
 mov ax,[bx+4]
 mov [options_baud_high],ax
 jmp .good
.flow:
 mov bx,options_flows
.flow_loop:
 mov ax,[bx]
 or ax,ax
 jz .serial
 call options_equal
 jnc .flow_found
 add bx,6
 jmp .flow_loop
.flow_found:
 test byte [options_seen],8
 jnz .bad
 or byte [options_seen],8
 mov ax,[bx+2]
 mov [options_soft],ax
 mov ax,[bx+4]
 mov [options_hard],ax
 jmp .good
.serial:
 cmp byte [options_token+3],0
 jne .bad
 mov al,[options_token]
 cmp al,'7'
 je .bits_ok
 cmp al,'8'
 jne .bad
.bits_ok:
 sub al,'0'
 xor ah,ah
 mov [options_data],ax
 mov al,[options_token+2]
 cmp al,'1'
 je .stop_ok
 cmp al,'2'
 jne .bad
.stop_ok:
 sub al,'0'
 xor ah,ah
 mov [options_stop],ax
 mov al,[options_token+1]
 xor bx,bx
.parity_loop:
 cmp al,[options_parities+bx]
 je .parity_ok
 inc bx
 cmp bx,5
 jb .parity_loop
 jmp .bad
.parity_ok:
 test byte [options_seen],4
 jnz .bad
 or byte [options_seen],4
 mov [options_parity],bx
.good:
 xor ax,ax
 clc
 ret
.bad:
 mov ax,2
 stc
 ret

SEGMENT _DATA public class=DATA use16
global terminal_usage,terminal_config_path,terminal_option_mask,terminal_dial_target
terminal_config_path: times 64 db 0
terminal_dial_target: times 64 db 0
terminal_option_mask: dw 0
terminal_usage:
 db 'PCPLUS terminal lab',13,10
 db 'Usage: TERMINAL [@FILE.PRM] [/D:target] [COM1..COM4] [baud] [serial] [flow]',13,10
 db 'Dial target: explicit, max 63 bytes; case preserved. Flow: NONE|SOFT|HARD.',13,10
 db 'PRM path: explicit only, max 63 bytes; no spaces, quotes or wildcards.',13,10
 db 'Serial: 7/8 data, N/O/E/M/S parity, 1/2 stop; e.g. 8N1. Any option order.',13,10
 db 'Baud: 300 1200 2400 4800 9600 19200 38400 57600 115200',13,10
 db 'Defaults: COM1 38400 8N1 NONE. Alt-X exits. /? shows this help.',13,10,'$'
options_defaults: dw 1,38400,0,0,8,1,0,0
options_stage:
options_port: dw 0
options_baud_low: dw 0
options_baud_high: dw 0
options_parity: dw 0
options_data: dw 0
options_stop: dw 0
options_soft: dw 0
options_hard: dw 0
options_seen: db 0
options_token: times 67 db 0
options_raw_token: times 67 db 0
options_config_stage: times 64 db 0
options_dial_stage: times 64 db 0
options_dial_punctuation: db '.:/-_@[]%?=&',0
options_parities: db 'NOEMS'
options_bases: dw 0x3f8,0x2f8,0x3e8,0x2e8
options_irqs: dw 4,3,4,3
options_help_table: dw options_help1,options_help2,options_help3,options_help4,options_help5,options_help6,0
options_help1: db '/?',0
options_help2: db '?',0
options_help3: db 'HELP',0
options_help4: db '/H',0
options_help5: db '-H',0
options_help6: db '--HELP',0
options_bauds:
 dw options_b300,300,0
 dw options_b1200,1200,0
 dw options_b2400,2400,0
 dw options_b4800,4800,0
 dw options_b9600,9600,0
 dw options_b19200,19200,0
 dw options_b38400,38400,0
 dw options_b57600,57600,0
 dw options_b115200,49664,1
 dw 0
options_b300: db '300',0
options_b1200: db '1200',0
options_b2400: db '2400',0
options_b4800: db '4800',0
options_b9600: db '9600',0
options_b19200: db '19200',0
options_b38400: db '38400',0
options_b57600: db '57600',0
options_b115200: db '115200',0
options_flows:
 dw options_none,0,0
 dw options_n,0,0
 dw options_soft_name,1,0
 dw options_s,1,0
 dw options_hard_name,0,1
 dw options_h,0,1
 dw 0
options_none: db 'NONE',0
options_n: db 'N',0
options_soft_name: db 'SOFT',0
options_s: db 'S',0
options_hard_name: db 'HARD',0
options_h: db 'H',0
