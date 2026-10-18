; Maintained offline setup-before-connect entry. No parent PRM pointer ABI.
; Runs after directory selection, before loading, UART baseline save or IRQ install.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_option_mask,terminal_config_path,_process_run
global terminal_run_startup_setup
terminal_run_startup_setup:
 push bp
 push si
 push di
 push es
 test word [terminal_option_mask],8192
 jz .success
 ; /S requires @8.3 leaf, already validated atomically by options.asm.
 ; Copy the explicit argument into a separate bounded DOS tail. No COMSPEC,
 ; shell, PATH search, legacy marker or packed parent pointer is involved.
 push ds
 pop es
 cld
 mov di,setup_startup_tail
 mov al,' '
 stosb
 mov si,terminal_config_path
 mov cx,13
.copy:
 lodsb
 stosb
 or al,al
 jz .execute
 loop .copy
 jmp .failed
.execute:
 mov ax,setup_startup_result
 push ax
 mov ax,setup_startup_tail
 push ax
 mov ax,setup_startup_program
 push ax
 call _process_run
 add sp,6
 or ax,ax
 jnz .failed
 cmp word [setup_startup_result+4],0
 jne .failed
.success:
 xor ax,ax
 jmp .done
.failed:
 mov ax,11
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
global setup_startup_result,setup_startup_tail
setup_startup_result: times 4 dw 0
setup_startup_tail: times 14 db 0
setup_startup_program: db 'PRMEDIT.EXE',0
