; Recovered 4E6B wrapper and 6DDE yes/no body, not original source.
; Flat output preserves exact instruction bytes; OMF leaves UI services explicit.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ABORT_CONFIRM_OMF
%ifdef ABORT_CONFIRM_FAR
SEGMENT ASPECT_CODE public class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global aspect_abort_yesno
%ifndef ABORT_CONFIRM_YESNO_ONLY
global aspect_abort_confirm
%endif
extern abort_confirm_descriptor,abort_confirm_prompt,abort_confirm_attribute
extern abort_choice_attribute,abort_choice_no,abort_choice_yes
extern abort_choice_cursor_mode,abort_choice_last_key
extern abort_window_save,abort_window_restore,abort_choice_write
extern abort_cursor_push,abort_cursor_pop,abort_cursor_set
extern abort_cursor_enable,abort_cursor_disable,abort_choice_key_read,abort_choice_bell
%else
%ifndef ABORT_CONFIRM_UNIT
%define ABORT_CONFIRM_UNIT 0
%endif
%if ABORT_CONFIRM_UNIT=0
ORG 0x4e6b
%define aspect_abort_yesno 0x6dde
%else
ORG 0x6dde
%endif
%define abort_confirm_descriptor 0x329e
%define abort_confirm_prompt 0x4948
%define abort_confirm_attribute 0x1f7e
%define abort_choice_attribute 0x1f7c
%define abort_choice_no 0x7a96
%define abort_choice_yes 0x7a9a
%define abort_choice_cursor_mode 0x7a6c
%define abort_choice_last_key 0x7a9e
%define abort_window_save 0x3fc7
%define abort_window_restore 0x4015
%define abort_choice_write 0x6bf0
%define abort_cursor_push 0x6b5a
%define abort_cursor_pop 0x6b42
%define abort_cursor_set 0x6e78
%define abort_cursor_enable 0x6dca
%define abort_cursor_disable 0x6e5a
%define abort_choice_key_read 0x64fe
%define abort_choice_bell 0x376d
%endif
%ifdef ABORT_CONFIRM_OMF
%ifndef ABORT_CONFIRM_YESNO_ONLY
%define ABORT_CONFIRM_BODY
%endif
%define ABORT_YESNO_BODY
%else
%if ABORT_CONFIRM_UNIT=0
%define ABORT_CONFIRM_BODY
%else
%define ABORT_YESNO_BODY
%endif
%endif
%ifdef ABORT_CONFIRM_BODY
aspect_abort_confirm:
 push bp
 mov_load bp,sp
 sub sp,4
 push di
 push si
 mov ax,abort_confirm_descriptor
 push ax
 call abort_window_save
 pop bx
 mov_load di,ax
 mov [bp-2],dx
 mov ax,0x0307
 push ax
 push word [abort_confirm_attribute]
 mov ax,abort_confirm_prompt
 push ax
 call abort_choice_write
 mov ax,0x031a
 push ax
 push word [abort_choice_attribute]
 sub_load ax,ax
 push ax
 call aspect_abort_yesno
 mov_load si,ax
 push word [bp-2]
 push di
 mov ax,abort_confirm_descriptor
 push ax
 call abort_window_restore
 add sp,6
 mov_load ax,si
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%ifdef ABORT_YESNO_BODY
aspect_abort_yesno:
 push bp
 mov_load bp,sp
 push di
 push si
 call abort_cursor_push
 mov ax,[bp+8]
 mov bx,[bp+6]
 push ax
 push bx
 push ax
 push ax
 push bx
 mov ax,abort_choice_yes
 mov di,[bp+4]
 cmp di,0
 jnz short .initial
 mov ax,abort_choice_no
.initial:
 push ax
 call abort_choice_write
 call abort_cursor_set
 mov si,[abort_choice_cursor_mode]
 cmp si,0
 jnz short .read
 call abort_cursor_enable
.read:
 call abort_choice_key_read
 mov [abort_choice_last_key],ax
 cmp al,13
 jz short .enter
 cmp al,27
 jz short .no
 and al,0xdf
 cmp al,'Y'
 jz short .yes
 cmp al,'N'
 jz short .no
 call abort_choice_bell
 jmp short .read
.no:
 mov di,0
 mov ax,abort_choice_no
 jmp short .answer
.yes:
 mov di,1
 mov ax,abort_choice_yes
.answer:
 push ax
 call abort_choice_write
.finish:
 cmp si,0
 jnz short .restore
 call abort_cursor_disable
.restore:
 call abort_cursor_pop
 mov_load ax,di
 pop si
 pop di
 pop bp
 ret 6
.enter:
 add sp,4
 jmp short .finish
%endif
