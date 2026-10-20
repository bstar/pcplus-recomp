BITS 16
CPU 8086
GROUP DGROUP _DATA
%ifdef NATIVE_BREAK_FAR
SEGMENT BRKCODE public class=CODE use16
%define ARGBASE 6
%define return retf
%else
SEGMENT _TEXT public class=CODE use16
%define ARGBASE 4
%define return ret
%endif
extern program_break_install,program_break_restore,program_break_ignore
global _native_break_binding_segment,_native_break_install,_native_break_restore
global _native_break_handler
_native_break_handler:
 mov ax,program_break_ignore
 mov dx,seg program_break_ignore
 return
_native_break_binding_segment:
 mov ax,DGROUP
 return
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
 return
%endmacro
_native_break_install:
 enter
 push word [bp+ARGBASE]
 call program_break_install
 leave
_native_break_restore:
 enter
 call program_break_restore
 leave
%ifdef NATIVE_BREAK_FAR
global _native_break_getvect,_native_break_setvect,_native_break_getflag,_native_break_setflag
_native_break_getvect:
 enter
 mov ax,[bp+ARGBASE]
 mov ah,0x35
 int 0x21
 mov ax,bx
 mov dx,es
 leave
_native_break_setvect:
 enter
 push ds
 mov ax,[bp+ARGBASE]
 mov ah,0x25
 mov dx,[bp+ARGBASE+2]
 mov ds,[bp+ARGBASE+4]
 int 0x21
 pop ds
 leave
_native_break_getflag:
 enter
 mov ax,0x3300
 int 0x21
 xor ax,ax
 mov al,dl
 leave
_native_break_setflag:
 enter
 mov dx,[bp+ARGBASE]
 mov ax,0x3301
 int 0x21
 leave
%endif
SEGMENT _DATA public class=DATA use16
global program_break_original_1b,program_break_original_23,program_break_original_flag
global _native_break_original_1b,_native_break_original_23,_native_break_original_flag
program_break_original_1b:
_native_break_original_1b: dd 0
program_break_original_23:
_native_break_original_23: dd 0
program_break_original_flag:
_native_break_original_flag: db 0
