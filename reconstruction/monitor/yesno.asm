; Exact original raw monitor instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef MONITOR_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global monitor_yesno_original
global monitor_at_6ddf
global monitor_at_6de1
global monitor_at_6de2
global monitor_at_6de3
global monitor_at_6de6
global monitor_at_6de9
global monitor_at_6dec
global monitor_at_6ded
global monitor_at_6dee
global monitor_at_6def
global monitor_at_6df0
global monitor_at_6df1
global monitor_at_6df4
global monitor_at_6df7
global monitor_at_6dfa
global monitor_at_6dfc
global monitor_at_6dff
global monitor_at_6e00
global monitor_at_6e03
global monitor_at_6e06
global monitor_at_6e0a
global monitor_at_6e0d
global monitor_at_6e0f
global monitor_at_6e12
global monitor_at_6e15
global monitor_at_6e18
global monitor_at_6e1a
global monitor_at_6e1c
global monitor_at_6e1e
global monitor_at_6e20
global monitor_at_6e22
global monitor_at_6e24
global monitor_at_6e26
global monitor_at_6e28
global monitor_at_6e2a
global monitor_at_6e2d
global monitor_at_6e2f
global monitor_at_6e32
global monitor_at_6e35
global monitor_at_6e37
global monitor_at_6e3a
global monitor_at_6e3d
global monitor_at_6e3e
global monitor_at_6e41
global monitor_at_6e44
global monitor_at_6e46
global monitor_at_6e49
global monitor_at_6e4c
global monitor_at_6e4e
global monitor_at_6e4f
global monitor_at_6e50
global monitor_at_6e51
global monitor_at_6e54
global monitor_at_6e57
extern monitor_beep
extern monitor_keyboard_read
extern monitor_prompt_unlock
extern monitor_prompt_lock
extern monitor_draw_text
extern monitor_cursor_6dca
extern monitor_cursor_6e5a
extern monitor_cursor_position
extern monitor_cursor_visibility
extern monitor_no_label
extern monitor_yes_label
extern monitor_prompt_key
%else
ORG 0x6dde
%define monitor_beep 0x376d
%define monitor_keyboard_read 0x64fe
%define monitor_prompt_unlock 0x6b42
%define monitor_prompt_lock 0x6b5a
%define monitor_draw_text 0x6bf0
%define monitor_cursor_6dca 0x6dca
%define monitor_cursor_6e5a 0x6e5a
%define monitor_cursor_position 0x6e78
%define monitor_cursor_visibility 0x7a6c
%define monitor_no_label 0x7a96
%define monitor_yes_label 0x7a9a
%define monitor_prompt_key 0x7a9e
%endif
%include "encodings.inc"
monitor_yesno_original: push bp
monitor_at_6ddf: mov_load bp,sp
monitor_at_6de1: push di
monitor_at_6de2: push si
monitor_at_6de3: call monitor_prompt_lock
monitor_at_6de6: mov ax,[bp+0x8]
monitor_at_6de9: mov bx,[bp+0x6]
monitor_at_6dec: push ax
monitor_at_6ded: push bx
monitor_at_6dee: push ax
monitor_at_6def: push ax
monitor_at_6df0: push bx
monitor_at_6df1: mov ax,monitor_yes_label
monitor_at_6df4: mov di,[bp+0x4]
monitor_at_6df7: cmp di,0x0
monitor_at_6dfa: jnz short monitor_at_6dff
monitor_at_6dfc: mov ax,monitor_no_label
monitor_at_6dff: push ax
monitor_at_6e00: call monitor_draw_text
monitor_at_6e03: call monitor_cursor_position
monitor_at_6e06: mov si,[monitor_cursor_visibility]
monitor_at_6e0a: cmp si,0x0
monitor_at_6e0d: jnz short monitor_at_6e12
monitor_at_6e0f: call monitor_cursor_6dca
monitor_at_6e12: call monitor_keyboard_read
monitor_at_6e15: mov [monitor_prompt_key],ax
monitor_at_6e18: cmp al,0xd
monitor_at_6e1a: jz short monitor_at_6e54
monitor_at_6e1c: cmp al,0x1b
monitor_at_6e1e: jz short monitor_at_6e2f
monitor_at_6e20: and al,0xdf
monitor_at_6e22: cmp al,0x59
monitor_at_6e24: jz short monitor_at_6e37
monitor_at_6e26: cmp al,0x4e
monitor_at_6e28: jz short monitor_at_6e2f
monitor_at_6e2a: call monitor_beep
monitor_at_6e2d: jmp short monitor_at_6e12
monitor_at_6e2f: mov di,0x0
monitor_at_6e32: mov ax,monitor_no_label
monitor_at_6e35: jmp short monitor_at_6e3d
monitor_at_6e37: mov di,0x1
monitor_at_6e3a: mov ax,monitor_yes_label
monitor_at_6e3d: push ax
monitor_at_6e3e: call monitor_draw_text
monitor_at_6e41: cmp si,0x0
monitor_at_6e44: jnz short monitor_at_6e49
monitor_at_6e46: call monitor_cursor_6e5a
monitor_at_6e49: call monitor_prompt_unlock
monitor_at_6e4c: mov_load ax,di
monitor_at_6e4e: pop si
monitor_at_6e4f: pop di
monitor_at_6e50: pop bp
monitor_at_6e51: ret word 0x6
monitor_at_6e54: add sp,0x4
monitor_at_6e57: jmp short monitor_at_6e41
