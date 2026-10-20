BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern program_break_install,program_break_restore,program_break_ignore
global _native_break_binding_segment,_native_break_install,_native_break_restore
global _native_break_handler
_native_break_handler:
 mov ax,program_break_ignore
 mov dx,seg program_break_ignore
 ret
_native_break_binding_segment:
 mov ax,DGROUP
 ret
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
 cld
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
%endmacro
_native_break_install:
 enter
 push word [bp+4]
 call program_break_install
 leave
_native_break_restore:
 enter
 call program_break_restore
 leave
SEGMENT _DATA public class=DATA use16
global program_break_original_1b,program_break_original_23,program_break_original_flag
global _native_break_original_1b,_native_break_original_23,_native_break_original_flag
program_break_original_1b:
_native_break_original_1b: dd 0
program_break_original_23:
_native_break_original_23: dd 0
program_break_original_flag:
_native_break_original_flag: db 0
