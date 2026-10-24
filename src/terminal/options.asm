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
 mov word [options_seen],0
 mov di,options_config_stage
 xor ax,ax
 mov cx,32
 rep stosw
 mov di,options_dial_stage
 mov cx,32
 rep stosw
 mov di,options_directory_stage
 mov cx,32
 rep stosw
 mov di,options_keyboard_stage
 mov cx,32
 rep stosw
 mov di,options_actions_stage
 mov cx,32
 rep stosw
 mov di,options_translation_stage
 mov cx,32
 rep stosw
 mov word [options_entry_stage],0
 mov word [options_codes_stage],0
 mov word [options_keyboard_mode_stage],2
 mov word [options_ansi_m_stage],0
 mov word [options_receive_credit_stage],0
 mov word [options_init_wait_stage],0xffff
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
 je .selector_size
 cmp word [options_token],'/E'
 je .selector_size
 cmp word [options_token],'/K'
 je .selector_size
 cmp word [options_token],'/T'
 je .selector_size
 cmp word [options_token],'/X'
 je .selector_size
 cmp word [options_token],'/N'
 jne .ordinary_size
.selector_size:
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
 ; Setup is an explicit pre-connect child, with the offline editor's leaf path
 ; contract. Validate this dependency before committing ANY live option.
 test word [options_seen],8192
 jz .setup_valid
 test word [options_seen],16
 jz .invalid
 mov si,options_config_stage
 xor bx,bx
 xor dx,dx
 xor cx,cx
.setup_name:
 lodsb
 or al,al
 jz .setup_end
 cmp al,'.'
 je .setup_dot
 cmp al,'A'
 jb .setup_digit
 cmp al,'Z'
 jbe .setup_character
.setup_digit:
 cmp al,'0'
 jb .setup_punctuation
 cmp al,'9'
 jbe .setup_character
.setup_punctuation:
 cmp al,'_'
 je .setup_character
 cmp al,'-'
 jne .invalid
.setup_character:
 or dx,dx
 jnz .setup_extension
 inc bx
 cmp bx,8
 ja .invalid
 jmp .setup_name
.setup_extension:
 inc cx
 cmp cx,3
 ja .invalid
 jmp .setup_name
.setup_dot:
 or bx,bx
 jz .invalid
 or dx,dx
 jnz .invalid
 inc dx
 jmp .setup_name
.setup_end:
 or bx,bx
 jz .invalid
 or dx,dx
 jz .setup_valid
 or cx,cx
 jz .invalid
.setup_valid:
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
 mov si,options_directory_stage
 mov di,terminal_directory_path
 mov cx,32
 rep movsw
 mov si,options_keyboard_stage
 mov di,terminal_keyboard_path
 mov cx,32
 rep movsw
 mov si,options_actions_stage
 mov di,terminal_actions_path
 mov cx,32
 rep movsw
 mov si,options_translation_stage
 mov di,terminal_translation_path
 mov cx,32
 rep movsw
 mov ax,[options_entry_stage]
 mov [terminal_directory_entry],ax
 mov ax,[options_codes_stage]
 mov [terminal_directory_codes],ax
 mov ax,[options_keyboard_mode_stage]
 mov [terminal_keyboard_bios_selection],ax
 mov ax,[options_ansi_m_stage]
 mov [terminal_ansi_m_policy],ax
 mov ax,[options_receive_credit_stage]
 mov [terminal_zmodem_receive_credit],ax
 mov ax,[options_init_wait_stage]
 cmp ax,0xffff
 jne .init_wait_commit
 xor ax,ax
.init_wait_commit:
 mov [terminal_modem_init_wait],ax
 xor ax,ax
 mov ax,[options_seen]
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
 test word [options_seen],16
 jnz .bad
 mov si,options_token+1
 mov di,options_config_stage
 mov dx,16
.path_start:
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
 or word [options_seen],dx
 jmp .good
.help_start:
 cmp word [options_token],'/S'
 jne .meta_option
 cmp byte [options_token+2],0
 jne .meta_option
 test word [options_seen],8192
 jnz .bad
 or word [options_seen],8192
 jmp .good
.meta_option:
 cmp word [options_token],'/X'
 jne .actions_option
 cmp byte [options_token+2],':'
 jne .actions_option
 test word [options_seen],16384
 jnz .bad
 mov si,options_token+3
 mov di,options_translation_stage
 mov dx,16384
 jmp .path_start
.actions_option:
 cmp word [options_token],'/T'
 jne .credit_option
 cmp byte [options_token+2],':'
 jne .credit_option
 test word [options_seen],4096
 jnz .bad
 mov si,options_token+3
 mov di,options_actions_stage
 mov dx,4096
 jmp .path_start
.credit_option:
 cmp word [options_token],'/I'
 jne .zcredit_option
 cmp byte [options_token+2],':'
 jne .zcredit_option
 cmp word [options_init_wait_stage],0xffff
 jne .bad
 mov di,32767
 jmp .number_begin
.zcredit_option:
 cmp word [options_token],'/Z'
 jne .ansi_option
 cmp byte [options_token+2],':'
 jne .ansi_option
 test word [options_seen],32768
 jnz .bad
 mov di,8192
.number_begin:
 mov si,options_token+3
 cmp byte [si],0
 je .bad
 xor bx,bx
.credit_digit:
 lodsb
 or al,al
 jz .credit_done
 sub al,'0'
 cmp al,9
 ja .bad
 xor ah,ah
 mov cx,ax
 mov ax,bx
 mov dx,10
 mul dx
 or dx,dx
 jnz .bad
 add ax,cx
 jc .bad
 cmp ax,di
 ja .bad
 mov bx,ax
 jmp .credit_digit
.credit_done:
 cmp di,32767
 je .init_wait_done
 or bx,bx
 jz .bad
 mov [options_receive_credit_stage],bx
 or word [options_seen],32768
 jmp .good
.init_wait_done:
 mov [options_init_wait_stage],bx
 jmp .good
.ansi_option:
 cmp word [options_token],'/A'
 jne .bios_option
 cmp byte [options_token+2],':'
 jne .bios_option
 test word [options_seen],2048
 jnz .bad
 mov ax,options_ansi_network
 call options_equal
 jnc .ansi_network
 mov ax,options_ansi_original
 call options_equal
 jc .bad
 mov ax,1
 jmp .ansi_done
.ansi_network:
 xor ax,ax
.ansi_done:
 mov [options_ansi_m_stage],ax
 or word [options_seen],2048
 jmp .good
.bios_option:
 cmp word [options_token],'/B'
 jne .keyboard_option
 cmp byte [options_token+2],':'
 jne .keyboard_option
 test word [options_seen],1024
 jnz .bad
 mov ax,options_bios_standard
 call options_equal
 jnc .bios_standard
 mov ax,options_bios_enhanced
 call options_equal
 jnc .bios_enhanced
 mov ax,options_bios_auto
 call options_equal
 jc .bad
 mov ax,2
 jmp .bios_done
.bios_standard:
 xor ax,ax
 jmp .bios_done
.bios_enhanced:
 mov ax,1
.bios_done:
 mov [options_keyboard_mode_stage],ax
 or word [options_seen],1024
 jmp .good
.keyboard_option:
 cmp word [options_token],'/K'
 jne .directory_option
 cmp byte [options_token+2],':'
 jne .directory_option
 test word [options_seen],512
 jnz .bad
 mov si,options_token+3
 mov di,options_keyboard_stage
 mov dx,512
 jmp .path_start
.directory_option:
 cmp word [options_token],'/E'
 jne .entry_option
 cmp byte [options_token+2],':'
 jne .entry_option
 test word [options_seen],64
 jnz .bad
 mov si,options_token+3
 mov di,options_directory_stage
 mov dx,64
 jmp .path_start
.entry_option:
 cmp word [options_token],'/N'
 jne .dial_option
 cmp byte [options_token+2],':'
 jne .dial_option
 test word [options_seen],128
 jnz .bad
 mov si,options_token+3
 cmp byte [si],0
 je .bad
 xor bx,bx
.entry_digit:
 lodsb
 or al,al
 jz .entry_done
 sub al,'0'
 cmp al,9
 ja .bad
 xor ah,ah
 mov cx,ax
 mov ax,bx
 mov dx,10
 mul dx
 add ax,cx
 cmp ax,200
 ja .bad
 mov bx,ax
 jmp .entry_digit
.entry_done:
 or bx,bx
 jz .bad
 mov [options_entry_stage],bx
 or word [options_seen],128
 jmp .good
.dial_option:
 cmp word [options_token],'/C'
 jne .dial_selector
 cmp byte [options_token+2],':'
 jne .dial_selector
 test word [options_seen],256
 jnz .bad
 mov ax,options_codes_literal
 call options_equal
 jnc .codes_literal
 mov ax,options_codes_legacy
 call options_equal
 jc .bad
 mov word [options_codes_stage],1
 jmp .codes_done
.codes_literal:
 mov word [options_codes_stage],0
.codes_done:
 or word [options_seen],256
 jmp .good
.dial_selector:
 cmp word [options_token],'/D'
 jne .help_table
 cmp byte [options_token+2],':'
 jne .help_table
 test word [options_seen],32
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
 or word [options_seen],32
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
 test word [options_seen],1
 jnz .bad
 or word [options_seen],1
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
 test word [options_seen],2
 jnz .bad
 or word [options_seen],2
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
 test word [options_seen],8
 jnz .bad
 or word [options_seen],8
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
 test word [options_seen],4
 jnz .bad
 or word [options_seen],4
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
global terminal_directory_path,terminal_directory_entry,terminal_directory_codes
global terminal_keyboard_path
global terminal_keyboard_bios_selection
global terminal_ansi_m_policy
global terminal_actions_path
global terminal_translation_path
global terminal_zmodem_receive_credit,_terminal_zmodem_receive_credit
terminal_config_path: times 64 db 0
terminal_dial_target: times 64 db 0
terminal_directory_path: times 64 db 0
terminal_keyboard_path: times 64 db 0
terminal_actions_path: times 64 db 0
terminal_translation_path: times 64 db 0
terminal_keyboard_bios_selection: dw 2
terminal_ansi_m_policy: dw 0
terminal_directory_entry: dw 0
terminal_directory_codes: dw 0
terminal_option_mask: dw 0
terminal_zmodem_receive_credit:
_terminal_zmodem_receive_credit: dw 0
global terminal_modem_init_wait
terminal_modem_init_wait: dw 0
%ifdef TERMINAL_FAR_USAGE
; Read-only startup help need not consume scarce DS=SS data. Its only reader
; supplies the relocated segment explicitly around DOS09 and restores DS.
SEGMENT USAGE_CODE public align=16 class=FARCODE use16
%endif
terminal_usage:
 db 'PCPLUS terminal lab',13,10
 db 'Usage: TERMINAL [@FILE.PRM] [/D:target] [COM1..COM4] [baud] [serial] [flow]',13,10
 db 'Dial target: explicit, max 63 bytes; case preserved. Flow: NONE|SOFT|HARD.',13,10
 db 'Directory: /E:FILE.DIR [/N:1..200]; omit /N to choose an entry.',13,10
 db 'Directory codes: /C:LITERAL (default) or /C:LEGACY (A..J substitutions).',13,10
 db 'Keyboard: /K:FILE.KBD imports the selected profile; explicit path only.',13,10
 db 'Input translation: /X:FILE.XLT loads exactly 256 bytes before connecting.',13,10
 db 'Meta actions: /T:FILE.KEY; Alt-1..Alt-0 run TEXT/PROGRAM; Esc cancels queued action.',13,10
 db 'Capture: Alt-F1 opens/appends or closes; Alt-F2 holds; Alt-F3 toggles CR+LF.',13,10
 db 'Alt-G appends screen to PCPLUS.SCR.',13,10
 db 'Monitor: Ctrl-backslash; Y replaces PCPLUS.DMP; Escape returns.',13,10
 db 'Keyboard BIOS: /B:AUTO (default), /B:STANDARD or /B:ENHANCED.',13,10
 db 'ANSI CSI M: /A:NETWORK (delete lines, default) or /A:ORIGINAL (wait).',13,10
 db 'ZMODEM receive credit: /Z:1..8192 bytes (default 8192).',13,10
 db '/I:0..32767 init reply seconds.',13,10
 db 'Setup: /S @FILE.PRM runs local PRMEDIT.EXE before connecting; 8.3 leaf only.',13,10
 db 'Alt-F10 edits @8.3 PRM; Y confirms serial/profile changes. COM changes need restart.',13,10
 db 'PRM path: explicit only, max 63 bytes; no spaces, quotes or wildcards.',13,10
 db 'Serial: 7/8 data, N/O/E/M/S parity, 1/2 stop; e.g. 8N1. Any option order.',13,10
 db 'Baud: 300 1200 2400 4800 9600 19200 38400 57600 115200',13,10
 db 'Alt-R: XMODEM download (HARD/NONE). Escape cancels. Alt-X exits.',13,10
 db 'Alt-S: XMODEM upload, automatic 1K blocks (HARD/NONE).',13,10
 db 'Defaults: COM1 38400 8N1 NONE. /? shows this help.',13,10,'$'
global terminal_usage_end
terminal_usage_end:
%ifdef TERMINAL_FAR_USAGE
SEGMENT _DATA
%endif
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
options_seen: dw 0
options_token: times 67 db 0
options_raw_token: times 67 db 0
options_config_stage: times 64 db 0
options_dial_stage: times 64 db 0
options_directory_stage: times 64 db 0
options_keyboard_stage: times 64 db 0
options_actions_stage: times 64 db 0
options_translation_stage: times 64 db 0
options_keyboard_mode_stage: dw 2
options_ansi_m_stage: dw 0
options_receive_credit_stage: dw 0
options_init_wait_stage: dw 0xffff
options_ansi_network: db '/A:NETWORK',0
options_ansi_original: db '/A:ORIGINAL',0
options_bios_auto: db '/B:AUTO',0
options_bios_standard: db '/B:STANDARD',0
options_bios_enhanced: db '/B:ENHANCED',0
options_entry_stage: dw 0
options_codes_stage: dw 0
options_codes_literal: db '/C:LITERAL',0
options_codes_legacy: db '/C:LEGACY',0
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
