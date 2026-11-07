; Original2.01 helper-launch frame. Dependencies and editor remain separate.
; Flat image retains original offsets; OMF names expose each external boundary.
; DS=SS. save_screen returns DX:AX; restore_screen removes four argument bytes
; with RET4. Caller cleanup for formatter/locator/PROGRAM stays native.
BITS 16
CPU 8086
%ifdef KEYMAP_LAUNCH_OMF
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
global keymap_launch
extern keymap_profile:wrt DGROUP,keymap_filename:wrt DGROUP
extern keymap_tail:wrt DGROUP,keymap_format_text:wrt DGROUP,keymap_program_name:wrt DGROUP
extern keymap_format,keymap_save_screen,keymap_locate,keymap_program,keymap_restore_screen,keymap_reload
%else
ORG 0x145a
%define keymap_profile 0x1d18
%define keymap_filename 0x3262
%define keymap_tail 0xce6a
%define keymap_format_text 0x4675
%define keymap_program_name 0x467b
%define keymap_format 0x82b6
%define keymap_save_screen 0x6bbe
%define keymap_locate 0x353d
%define keymap_program 0x433d
%define keymap_restore_screen 0x4870
%define keymap_reload 0x0cd2
%endif
%include "encodings.inc"
keymap_launch:
 push bp
 mov_load bp,sp
 sub sp,byte 4
 push si
 mov ax,keymap_filename
 push ax
 push word [keymap_profile]
 mov ax,keymap_format_text
 push ax
 mov ax,keymap_tail
 push ax
 call keymap_format
 add sp,byte 8
 call keymap_save_screen
 mov_load si,ax
 mov [bp-2],dx
 sub_load ax,ax
 push ax
 push ax
 push ax
 mov ax,keymap_tail
 push ax
 mov ax,keymap_program_name
 push ax
 call keymap_locate
 add sp,byte 2
 push ax
 call keymap_program
 add sp,byte 10
 push word [bp-2]
 push si
 call keymap_restore_screen
 call keymap_reload
 pop si
 mov_load sp,bp
 pop bp
 ret
%ifdef KEYMAP_LAUNCH_OMF
SEGMENT _DATA public class=DATA use16
%endif
