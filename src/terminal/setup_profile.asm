; Maintained4/6 profile transaction. All keyboard file I/O happens before
; confirmation/global mutation; commit runs with IRQ still handed off, after
; mode3/old-screen restoration. Transport and application owners stay intact.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS
%include "terminal_import.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_option_mask,terminal_keyboard_path,capture_fs_canonical_
extern terminal_build_keymap,_keymap_dos_read,terminal_keymap
extern csi_terminal_id,terminal_parser_active,terminal_configuration_values
extern csi_reset_terminal,csi_clear_tabs,terminal_clear_home,terminal_reset_capture
extern terminal_apply_display_configuration,terminal_exit_code,terminal_quit
global terminal_setup_profile_bind,terminal_setup_profile_stage,terminal_setup_profile_finish
%macro save 0
 push bp
 push si
 push di
 push es
 push ds
 pop es
 cld
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop bp
 ret
%endmacro
terminal_setup_profile_bind:
 save
 mov word [terminal_setup_keyboard_bound],0
 mov word [terminal_setup_profile_ready],0
 test word [terminal_option_mask],512
 jz .default
 mov ax,terminal_keyboard_path
 mov dx,setup_keyboard_absolute
 call capture_fs_canonical_
 or ax,ax
 jnz .done
 mov si,setup_keyboard_absolute
 mov cx,64
.length:
 lodsb
 or al,al
 jz .default
 loop .length
 jmp .done ;Reader's supported canonical path must fit its63-byte contract.
.default:
 mov word [terminal_setup_keyboard_bound],1
.done:
 restore

; AX supported target profile. AX0 staged,1 unavailable/invalid keyboard,
;2 unsupported profile/unsafe parser ownership. No live configuration mutation.
terminal_setup_profile_stage:
 save
 mov word [terminal_setup_profile_ready],0
 cmp ax,4
 je .valid
 cmp ax,6
 jne .invalid
.valid:
 cmp word [terminal_parser_active],0
 jne .invalid
 mov [setup_profile_target],ax
 test word [terminal_option_mask],512
 jnz .import
 mov ax,setup_profile_keymap
 call terminal_build_keymap
 jmp .loaded
.import:
 cmp word [terminal_setup_keyboard_bound],1
 jne .failed
 mov ax,setup_profile_keyboard_io
 push ax
 mov ax,setup_profile_keymap
 push ax
 push word [setup_profile_target]
 mov ax,setup_keyboard_absolute
 push ax
 call _keymap_dos_read
 add sp,8
.loaded:
 or ax,ax
 jnz .failed
 mov word [terminal_setup_profile_ready],1
 xor ax,ax
 jmp .done
.failed:
 mov ax,1
 jmp .done
.invalid:
 mov ax,2
.done:
 restore

; A clean old RIS restores the source-owned geometry/modes instead of capturing
; the peer's current state. Then install desired display defaults and staged
; keyboard, reset tabs, clear/home with the NEW palette and capture its RIS.
terminal_setup_profile_finish:
 save
 cmp word [terminal_setup_profile_status],1
 jne .done
 cmp word [terminal_setup_profile_ready],1
 jne .fatal
 mov ax,[setup_profile_target]
 cmp ax,[terminal_configuration_values+TI_PROFILE]
 jne .fatal
 mov ax,1
 push ax
 call csi_reset_terminal
 add sp,2
 call terminal_apply_display_configuration
 push ds
 pop es
 mov si,setup_profile_keymap
 mov di,terminal_keymap
 mov cx,948
 cld
 rep movsb
 mov ax,1
 push ax
 call csi_clear_tabs
 add sp,2
 call terminal_clear_home
 call terminal_reset_capture
 or ax,ax
 jnz .fatal
 mov word [terminal_setup_profile_ready],0
 jmp .done
.fatal:
 mov word [terminal_setup_profile_status],3
 mov word [terminal_exit_code],7
 mov word [terminal_quit],1
.done:
 restore
SEGMENT _DATA public class=DATA use16
global terminal_setup_profile_status,terminal_setup_profile_ready,terminal_setup_keyboard_bound
terminal_setup_profile_status: dw 0 ;0none,1confirmed,2declined,3staging failure.
terminal_setup_profile_ready: dw 0
terminal_setup_keyboard_bound: dw 0
setup_profile_target: dw 0
setup_profile_keyboard_io: times 14 db 0
SEGMENT _BSS public align=2 class=BSS use16
global setup_profile_keymap,setup_keyboard_absolute
setup_profile_keymap: resb 948
setup_keyboard_absolute: resb 128
