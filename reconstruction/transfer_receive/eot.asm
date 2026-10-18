; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_other_control
global receive_at_dd4e
global receive_at_dd50
global receive_at_dd54
global receive_at_dd56
global receive_at_dd5b
global receive_at_dd5d
global receive_at_dd60
global receive_at_dd61
global receive_at_dd64
global receive_at_dd69
global receive_at_dd6b
global receive_at_dd6f
global receive_at_dd71
global receive_at_dd74
global receive_at_dd77
global receive_at_dd7a
global receive_at_dd7d
global receive_at_dd81
global receive_at_dd83
global receive_at_dd86
global receive_at_dd88
global receive_at_dd8b
global receive_at_dd8c
global receive_at_dd8f
global receive_at_dd92
global receive_at_dd95
global receive_at_dd97
global receive_at_dd9a
global receive_at_dd9c
global receive_at_dd9f
global receive_at_dda1
global receive_at_dda4
global receive_at_dda6
global receive_at_dda9
global receive_at_ddab
global receive_at_ddae
global receive_at_ddb0
global receive_at_ddb1
global receive_at_ddb4
global receive_at_ddb7
global receive_at_ddbb
global receive_at_ddbd
global receive_at_ddc0
global receive_at_ddc4
global receive_at_ddc6
global receive_at_ddc9
global receive_at_ddca
global receive_at_ddcd
global receive_at_ddd2
global receive_at_ddd4
global receive_at_ddd9
global receive_at_dddc
global receive_at_dde0
global receive_at_dde3
global receive_at_dde6
global receive_at_dde9
global receive_at_ddea
global receive_at_dded
global receive_at_ddf0
global receive_at_ddf3
extern receive_nak
extern receive_delay
extern receive_queued_count
extern receive_timed_byte
extern receive_flush_input
extern receive_error_count
extern receive_at_dc1f
extern receive_retry_limit
extern receive_progress
extern receive_status
extern receive_control_status
extern receive_disk_commit
%else
ORG 0xdd4a
%define receive_nak 0x40b9
%define receive_delay 0x6b72
%define receive_queued_count 0x8e20
%define receive_timed_byte 0xaad9
%define receive_flush_input 0xabca
%define receive_error_count 0xcd8a
%define receive_at_dc1f 0xdc1f
%define receive_retry_limit 0xdcf1
%define receive_progress 0xe322
%define receive_status 0xe498
%define receive_control_status 0xf050
%endif
%include "encodings.inc"
receive_other_control: cmp word [bp-0x2],0x4
receive_at_dd4e: jnz short receive_at_dd6b
receive_at_dd50: cmp word [bp-0x10],0x4
receive_at_dd54: jnz short receive_at_dd6b
receive_at_dd56: cmp word [receive_queued_count],0x0
receive_at_dd5b: jnz short receive_at_dd6b
receive_at_dd5d: mov ax,0x64
receive_at_dd60: push ax
receive_at_dd61: call receive_delay
receive_at_dd64: cmp word [receive_queued_count],0x0
receive_at_dd69: jz short receive_retry_limit
receive_at_dd6b: cmp word [bp-0x10],0x4
receive_at_dd6f: jnz short receive_at_dd77
receive_at_dd71: call receive_flush_input
receive_at_dd74: call receive_nak
receive_at_dd77: mov ax,[bp-0x10]
receive_at_dd7a: mov [bp-0x2],ax
receive_at_dd7d: cmp word [bp-0x2],0x4
receive_at_dd81: jnz short receive_at_dd88
receive_at_dd83: mov ax,0x5
receive_at_dd86: jmp short receive_at_dd8b
receive_at_dd88: mov ax,0xf
receive_at_dd8b: push ax
receive_at_dd8c: call receive_timed_byte
receive_at_dd8f: mov [bp-0x10],ax
receive_at_dd92: cmp ax,strict word 0x1
receive_at_dd95: jz short receive_at_ddb0
receive_at_dd97: cmp ax,strict word 0x4
receive_at_dd9a: jz short receive_at_ddb0
receive_at_dd9c: cmp ax,strict word 0x18
receive_at_dd9f: jz short receive_at_ddb0
receive_at_dda1: cmp ax,strict word 0x16
receive_at_dda4: jz short receive_at_ddb0
receive_at_dda6: cmp ax,strict word 0x2
receive_at_dda9: jz short receive_at_ddb0
receive_at_ddab: cmp ax,strict word 0xffff
receive_at_ddae: jnz short receive_at_dd7d
receive_at_ddb0: push ax
receive_at_ddb1: call receive_control_status
receive_at_ddb4: add sp,0x2
receive_at_ddb7: cmp word [bp-0x10],0xffffffffffffffff
receive_at_ddbb: jz short receive_at_ddc0
receive_at_ddbd: jmp near receive_at_dc1f
receive_at_ddc0: cmp word [bp-0x2],0x4
receive_at_ddc4: jnz short receive_at_dddc
receive_at_ddc6: mov ax,0x64
receive_at_ddc9: push ax
receive_at_ddca: call receive_delay
receive_at_ddcd: cmp word [receive_queued_count],0x0
receive_at_ddd2: jnz short receive_at_dddc
receive_at_ddd4: mov word [bp-0x10],0x4
receive_at_ddd9: jmp near receive_retry_limit
receive_at_dddc: inc word [receive_error_count]
receive_at_dde0: inc word [bp-0x14]
receive_at_dde3: call receive_nak
receive_at_dde6: mov ax,0x1
receive_at_dde9: push ax
receive_at_ddea: call receive_status
receive_at_dded: add sp,0x2
receive_at_ddf0: call receive_progress
receive_at_ddf3: jmp near receive_at_dc1f
%ifdef TRANSFER_RECEIVE_OMF
jmp receive_disk_commit
%endif
