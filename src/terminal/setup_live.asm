; Foreground setup scheduling over the same drained UART/EXEC/video owner as
; PROGRAM. Direct local executable and bounded leaf argument; no shell parsing.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_option_mask,terminal_config_path,terminal_macro_active
extern terminal_program_start,terminal_program_kind
global terminal_setup_start
; AX0 queued,1 no explicit supported leaf,2 busy. Preserve BP/SI/DI/ES.
terminal_setup_start:
 push bp
 push si
 push di
 push es
 test word [terminal_option_mask],16
 jz .unavailable
 cmp word [terminal_macro_active],0
 jne .busy
 mov si,terminal_config_path
 xor bx,bx ;base count
 xor dx,dx ;dot seen
 xor cx,cx ;extension count
.name:
 lodsb
 or al,al
 jz .end
 cmp al,'.'
 je .dot
 cmp al,'a'
 jb .folded
 cmp al,'z'
 ja .folded
 sub al,32
.folded:
 cmp al,'A'
 jb .digit
 cmp al,'Z'
 jbe .character
.digit:
 cmp al,'0'
 jb .punctuation
 cmp al,'9'
 jbe .character
.punctuation:
 cmp al,'_'
 je .character
 cmp al,'-'
 jne .unavailable
.character:
 or dx,dx
 jnz .extension
 inc bx
 cmp bx,8
 ja .unavailable
 jmp .name
.extension:
 inc cx
 cmp cx,3
 ja .unavailable
 jmp .name
.dot:
 or bx,bx
 jz .unavailable
 or dx,dx
 jnz .unavailable
 inc dx
 jmp .name
.end:
 or bx,bx
 jz .unavailable
 or dx,dx
 jz .queue
 or cx,cx
 jz .unavailable
.queue:
 mov ax,setup_schedule_command
 call terminal_program_start
 or ax,ax
 jnz .busy
 push ds
 pop es
 cld
 mov di,terminal_setup_tail
 mov al,' '
 stosb
 mov si,terminal_config_path
 mov cx,13
.copy:
 lodsb
 stosb
 or al,al
 jz .queued
 loop .copy ;syntax validation above guarantees a bounded terminator.
.queued:
 mov word [terminal_program_kind],1
 xor ax,ax
 jmp .done
.unavailable:
 mov ax,1
 jmp .done
.busy:
 mov ax,2
.done:
 mov [terminal_setup_status],ax
 pop es
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
global terminal_setup_tail,terminal_setup_status
terminal_setup_tail: times 14 db 0
terminal_setup_status: dw 0
setup_schedule_command: db 'PRMEDIT.EXE',0
