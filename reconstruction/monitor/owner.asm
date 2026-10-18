; Exact original raw monitor instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef MONITOR_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global monitor_run_original
global monitor_at_1aab
global monitor_at_1aad
global monitor_at_1ab0
global monitor_at_1ab1
global monitor_at_1ab2
global monitor_at_1ab8
global monitor_at_1abb
global monitor_at_1abe
global monitor_at_1ac1
global monitor_at_1ac3
global monitor_at_1ac7
global monitor_at_1aca
global monitor_at_1acd
global monitor_at_1ace
global monitor_at_1ad1
global monitor_at_1ad4
global monitor_at_1ad6
global monitor_at_1ad9
global monitor_at_1adc
global monitor_at_1add
global monitor_at_1ae1
global monitor_at_1ae4
global monitor_at_1ae5
global monitor_at_1ae8
global monitor_at_1aeb
global monitor_at_1aec
global monitor_at_1af0
global monitor_at_1af2
global monitor_at_1af3
global monitor_at_1af6
global monitor_at_1af8
global monitor_at_1afa
global monitor_at_1afd
global monitor_at_1b00
global monitor_at_1b01
global monitor_at_1b04
global monitor_at_1b05
global monitor_at_1b08
global monitor_at_1b0b
global monitor_at_1b0c
global monitor_at_1b0f
global monitor_at_1b12
global monitor_at_1b15
global monitor_at_1b18
global monitor_at_1b19
global monitor_at_1b1c
global monitor_at_1b1d
global monitor_at_1b20
global monitor_at_1b23
global monitor_at_1b29
global monitor_at_1b2e
global monitor_at_1b30
global monitor_at_1b33
global monitor_at_1b35
global monitor_at_1b38
global monitor_at_1b3b
global monitor_at_1b3d
global monitor_at_1b3f
global monitor_at_1b41
global monitor_at_1b44
global monitor_at_1b46
global monitor_at_1b49
global monitor_at_1b4b
global monitor_at_1b4e
global monitor_at_1b51
global monitor_at_1b53
global monitor_at_1b55
global monitor_at_1b57
global monitor_at_1b58
global monitor_at_1b5b
global monitor_at_1b5d
global monitor_at_1b5e
global monitor_at_1b61
global monitor_at_1b63
global monitor_at_1b64
global monitor_at_1b67
global monitor_at_1b68
global monitor_at_1b6b
global monitor_at_1b6e
global monitor_at_1b70
global monitor_at_1b72
global monitor_at_1b75
global monitor_at_1b76
global monitor_at_1b79
global monitor_at_1b7c
global monitor_at_1b7f
global monitor_at_1b81
global monitor_at_1b83
global monitor_at_1b86
global monitor_at_1b89
global monitor_at_1b8c
global monitor_at_1b8e
global monitor_at_1b91
global monitor_at_1b93
global monitor_at_1b96
global monitor_at_1b98
global monitor_at_1b9a
global monitor_at_1b9c
global monitor_at_1b9f
global monitor_at_1ba2
global monitor_at_1ba5
global monitor_at_1bab
global monitor_at_1bae
global monitor_at_1bb1
global monitor_at_1bb4
global monitor_at_1bb7
global monitor_at_1bb8
global monitor_at_1bb9
global monitor_at_1bbb
global monitor_at_1bbc
extern monitor_render
extern monitor_dispatch_key
extern monitor_normal_attribute
extern monitor_special_attribute
extern monitor_hook
extern monitor_active_attribute
extern monitor_choice_attribute
extern monitor_prompt_attribute
extern monitor_clear
extern monitor_status
extern monitor_window_descriptor
extern monitor_active
extern monitor_resolve_original
extern monitor_help_context
extern monitor_save_window
extern monitor_restore_window
extern monitor_prompt_text
extern monitor_dump_mode
extern monitor_dump_name
extern monitor_keyboard_read
extern monitor_keyboard_available
extern monitor_draw_text
extern monitor_yesno_original
extern monitor_close
extern monitor_open
extern monitor_putc
extern monitor_rx_count
extern monitor_dequeue
extern monitor_key
%else
ORG 0x1aaa
%define monitor_render 0x730
%define monitor_dispatch_key 0x1604
%define monitor_normal_attribute 0x1d32
%define monitor_special_attribute 0x1d34
%define monitor_hook 0x1d6e
%define monitor_active_attribute 0x1f70
%define monitor_choice_attribute 0x1f7c
%define monitor_prompt_attribute 0x1f7e
%define monitor_clear 0x24e2
%define monitor_status 0x2fb8
%define monitor_window_descriptor 0x329e
%define monitor_active 0x332c
%define monitor_resolve_original 0x353d
%define monitor_help_context 0x397a
%define monitor_save_window 0x3fc7
%define monitor_restore_window 0x4015
%define monitor_prompt_text 0x422a
%define monitor_dump_mode 0x468b
%define monitor_dump_name 0x468e
%define monitor_keyboard_read 0x64fe
%define monitor_keyboard_available 0x651a
%define monitor_draw_text 0x6bf0
%define monitor_yesno_original 0x6dde
%define monitor_close 0x8318
%define monitor_open 0x841a
%define monitor_putc 0x8436
%define monitor_rx_count 0x8e20
%define monitor_dequeue 0xaa65
%define monitor_key 0xcffa
%endif
%include "encodings.inc"
monitor_run_original: push bp
monitor_at_1aab: mov_load bp,sp
monitor_at_1aad: sub sp,0xa
monitor_at_1ab0: push di
monitor_at_1ab1: push si
monitor_at_1ab2: mov word [monitor_active],0x1
monitor_at_1ab8: call monitor_status
monitor_at_1abb: mov ax,[monitor_hook]
monitor_at_1abe: mov [bp-0xa],ax
monitor_at_1ac1: sub_load di,di
monitor_at_1ac3: mov [monitor_hook],di
monitor_at_1ac7: call monitor_clear
monitor_at_1aca: mov ax,monitor_window_descriptor
monitor_at_1acd: push ax
monitor_at_1ace: call monitor_save_window
monitor_at_1ad1: add sp,0x2
monitor_at_1ad4: mov_load si,ax
monitor_at_1ad6: mov [bp-0x6],dx
monitor_at_1ad9: mov ax,0x307
monitor_at_1adc: push ax
monitor_at_1add: push word [monitor_prompt_attribute]
monitor_at_1ae1: mov ax,monitor_prompt_text
monitor_at_1ae4: push ax
monitor_at_1ae5: call monitor_draw_text
monitor_at_1ae8: mov ax,0x31a
monitor_at_1aeb: push ax
monitor_at_1aec: push word [monitor_choice_attribute]
monitor_at_1af0: sub_load ax,ax
monitor_at_1af2: push ax
monitor_at_1af3: call monitor_yesno_original
monitor_at_1af6: or_load ax,ax
monitor_at_1af8: jz short monitor_at_1b15
monitor_at_1afa: mov di,0x1
monitor_at_1afd: mov ax,monitor_dump_mode
monitor_at_1b00: push ax
monitor_at_1b01: mov ax,monitor_dump_name
monitor_at_1b04: push ax
monitor_at_1b05: call monitor_resolve_original
monitor_at_1b08: add sp,0x2
monitor_at_1b0b: push ax
monitor_at_1b0c: call monitor_open
monitor_at_1b0f: add sp,0x4
monitor_at_1b12: mov [bp-0x2],ax
monitor_at_1b15: push word [bp-0x6]
monitor_at_1b18: push si
monitor_at_1b19: mov ax,monitor_window_descriptor
monitor_at_1b1c: push ax
monitor_at_1b1d: call monitor_restore_window
monitor_at_1b20: add sp,0x6
monitor_at_1b23: mov word [monitor_help_context],0x19
monitor_at_1b29: cmp word [monitor_rx_count],0x0
monitor_at_1b2e: jz short monitor_at_1b7c
monitor_at_1b30: call monitor_dequeue
monitor_at_1b33: mov_load si,ax
monitor_at_1b35: mov ax,[monitor_special_attribute]
monitor_at_1b38: mov [monitor_active_attribute],ax
monitor_at_1b3b: mov_load ax,si
monitor_at_1b3d: or_load ax,ax
monitor_at_1b3f: jz short monitor_at_1b58
monitor_at_1b41: sub ax,strict word 0x1b
monitor_at_1b44: jz short monitor_at_1b5e
monitor_at_1b46: sub ax,0xe4
monitor_at_1b49: jz short monitor_at_1b64
monitor_at_1b4b: mov ax,[monitor_normal_attribute]
monitor_at_1b4e: mov [monitor_active_attribute],ax
monitor_at_1b51: mov_load ax,si
monitor_at_1b53: sub_load ah,ah
monitor_at_1b55: jmp short monitor_at_1b67
monitor_at_1b57: nop
monitor_at_1b58: mov ax,0x30
monitor_at_1b5b: jmp short monitor_at_1b67
monitor_at_1b5d: nop
monitor_at_1b5e: mov ax,0x1b
monitor_at_1b61: jmp short monitor_at_1b67
monitor_at_1b63: nop
monitor_at_1b64: mov ax,0x3f
monitor_at_1b67: push ax
monitor_at_1b68: call monitor_render
monitor_at_1b6b: add sp,0x2
monitor_at_1b6e: or_load di,di
monitor_at_1b70: jz short monitor_at_1b7c
monitor_at_1b72: push word [bp-0x2]
monitor_at_1b75: push si
monitor_at_1b76: call monitor_putc
monitor_at_1b79: add sp,0x4
monitor_at_1b7c: call monitor_keyboard_available
monitor_at_1b7f: or_load ax,ax
monitor_at_1b81: jz short monitor_at_1b23
monitor_at_1b83: call monitor_keyboard_read
monitor_at_1b86: mov [monitor_key],ax
monitor_at_1b89: cmp ax,strict word 0x1b
monitor_at_1b8c: jz short monitor_at_1b98
monitor_at_1b8e: cmp ax,strict word 0x1c
monitor_at_1b91: jz short monitor_at_1b23
monitor_at_1b93: call monitor_dispatch_key
monitor_at_1b96: jmp short monitor_at_1b23
monitor_at_1b98: or_load di,di
monitor_at_1b9a: jz short monitor_at_1ba5
monitor_at_1b9c: push word [bp-0x2]
monitor_at_1b9f: call monitor_close
monitor_at_1ba2: add sp,0x2
monitor_at_1ba5: mov word [monitor_active],0x0
monitor_at_1bab: mov ax,[bp-0xa]
monitor_at_1bae: mov [monitor_hook],ax
monitor_at_1bb1: call monitor_clear
monitor_at_1bb4: call monitor_status
monitor_at_1bb7: pop si
monitor_at_1bb8: pop di
monitor_at_1bb9: mov_load sp,bp
monitor_at_1bbb: pop bp
monitor_at_1bbc: ret
