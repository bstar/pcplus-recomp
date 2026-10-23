; Explicit cdecl and callee-pop boundaries for the exact native notice core.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern program_notice_error,program_notice_message,program_strlen,pcplus_seconds
extern _notice_platform_clock,_notice_platform_sound,_notice_platform_save
extern _notice_platform_poll,_notice_platform_read,_notice_platform_restore
extern display_text
%macro alias 2
 global %1
 %1: jmp %2
%endmacro
alias program_notice_strlen,program_strlen
alias program_notice_clock,_notice_platform_clock
alias _notice_seconds_native,pcplus_seconds
alias program_notice_save,_notice_platform_save
alias program_notice_poll,_notice_platform_poll
alias program_notice_read,_notice_platform_read
alias program_notice_restore,_notice_platform_restore
alias program_notice_write,display_text
%macro sound 2
 global %1
 %1:
 push bp
 mov bp,sp
 mov ax,%2
 push ax
 call _notice_platform_sound
 add sp,2
 pop bp
 ret
%endmacro
sound program_notice_bell,1
sound program_notice_tone,0
%macro enter 0
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 cld
%endmacro
%macro leave 0
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
%endmacro
global _notice_call_native
_notice_call_native:
 enter
 cmp word [bp+6],0
 jne .error
 push word [bp+4]
 call program_notice_message ;Native RET2 consumes its one original argument.
 jmp short .done
.error:
 mov bx,[bp+4]
 call program_notice_error
.done:
 leave
global _notice_ticks_native
_notice_ticks_native:
 pushf
 cli
 push es
 xor ax,ax
 mov es,ax
 mov ax,[es:0x46c]
 mov dx,[es:0x46e]
 pop es
 popf
 ret
global _notice_key_pending_native,_notice_key_read_native
_notice_key_pending_native:
 enter
 mov ah,1
 int 0x16
 pushf
 pop ax
 xor ax,0x40
 and ax,0x40
 leave
_notice_key_read_native:
 enter
 xor ah,ah
 int 0x16
 leave
SEGMENT _DATA public class=DATA use16
global program_notice_descriptor,_notice_descriptor
program_notice_descriptor:
_notice_descriptor:
 dw 9
global program_notice_left,_notice_left
program_notice_left:
_notice_left: dw 0
 dw 11
global program_notice_right,_notice_right
program_notice_right:
_notice_right: dw 0
 dw program_notice_attribute
global program_notice_attribute,_notice_attribute
program_notice_attribute:
_notice_attribute: dw 0x70

global transfer_dos_clock_sample
transfer_dos_clock_sample: times 4 dw 0
