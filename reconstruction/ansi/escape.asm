; Recovered PCPlus 2.01 overlay-14 escape entry, not original source.
; Exact flat mode; OMF mode supplies named integration interfaces.
; See docs/ESCAPE.md for service boundaries and legacy loop behavior.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ANSI_OMF
SEGMENT _TEXT public class=CODE use16
global ansi_escape_entry
extern ansi_next_byte, ansi_unread_byte, ansi_read_parameter, ansi_parameter_transition, ansi_dispatch_command, ansi_escape_service_e0f8, ansi_escape_service_dd74, ansi_escape_service_ddbc, ansi_escape_service_da46, ansi_escape_service_12c8, ansi_escape_service_dac6, ansi_escape_service_da84, ansi_escape_service_ec94, ansi_escape_service_dd58, ansi_escape_service_20a4
extern ansi_parameter_count, ansi_parameters, ansi_private, ansi_secondary, ansi_charset_g0_flag_a, ansi_charset_g0_flag_graphics, ansi_charset_g1_flag_a, ansi_charset_g1_flag_graphics
%else
ORG 0xecd2
%define ansi_next_byte 0x5ca0
%define ansi_unread_byte 0xabde
%define ansi_read_parameter 0xe3f2
%define ansi_parameter_transition 0xe4a2
%define ansi_dispatch_command 0xe4b2
%define ansi_escape_service_e0f8 0xe0f8
%define ansi_escape_service_dd74 0xdd74
%define ansi_escape_service_ddbc 0xddbc
%define ansi_escape_service_da46 0xda46
%define ansi_escape_service_12c8 0x12c8
%define ansi_escape_service_dac6 0xdac6
%define ansi_escape_service_da84 0xda84
%define ansi_escape_service_ec94 0xec94
%define ansi_escape_service_dd58 0xdd58
%define ansi_escape_service_20a4 0x20a4
%define ansi_parameter_count 0xcb5c
%define ansi_parameters 0xcb3c
%define ansi_private 0xceac
%define ansi_secondary 0xcee2
%define ansi_charset_g0_flag_a 0xcde0
%define ansi_charset_g0_flag_graphics 0xcdec
%define ansi_charset_g1_flag_a 0xcde8
%define ansi_charset_g1_flag_graphics 0xcdf0
%endif
ansi_escape_entry:
L_ecd2: push bp
L_ecd3: mov_load bp, sp
L_ecd5: push si
L_ecd6: call ansi_next_byte
L_ecd9: cmp ax, strict word 0x48
L_ecdc: jnz L_ece1
L_ecde: jmp near L_ee04
L_ece1: jg L_ed46
L_ece3: cmp ax, strict word 0x45
L_ece6: jnz L_eceb
L_ece8: jmp near L_edfe
L_eceb: jbe L_ecf0
L_eced: jmp near L_eeaa
L_ecf0: cmp al, 0x28
L_ecf2: jnz L_ecf7
L_ecf4: jmp near L_ee3c
L_ecf7: jg L_ed12
L_ecf9: or_load al, al
L_ecfb: jz L_ecd6
L_ecfd: sub al, 0x1b
L_ecff: jz L_ecd6
L_ed01: sub al, 0x5
L_ed03: jnz L_ed08
L_ed05: jmp near L_ed9c
L_ed08: sub al, 0x3
L_ed0a: jnz L_ed0f
L_ed0c: jmp near L_edb0
L_ed0f: jmp near L_eeaa
L_ed12: cmp al, 0x37
L_ed14: jnz L_ed19
L_ed16: jmp near L_ede4
L_ed19: jg L_ed34
L_ed1b: sub al, 0x29
L_ed1d: jnz L_ed22
L_ed1f: jmp near L_ee76
L_ed22: dec al
L_ed24: jge L_ed29
L_ed26: jmp near L_eeaa
L_ed29: dec al
L_ed2b: jg L_ed30
L_ed2d: jmp near L_edb6
L_ed30: jmp near L_eeaa
nop ; original alignment instruction
L_ed34: sub al, 0x38
L_ed36: jnz L_ed3b
L_ed38: jmp near L_edf0
L_ed3b: sub al, 0xc
L_ed3d: jnz L_ed42
L_ed3f: jmp near L_edf8
L_ed42: jmp near L_eeaa
nop ; original alignment instruction
L_ed46: cmp ax, strict word 0x7f
L_ed49: jz L_ecd6
L_ed4b: jg L_ed76
L_ed4d: cmp ax, strict word 0x63
L_ed50: jnz L_ed55
L_ed52: jmp near L_ee1e
L_ed55: jbe L_ed5a
L_ed57: jmp near L_eeaa
L_ed5a: sub al, 0x4d
L_ed5c: jnz L_ed61
L_ed5e: jmp near L_ee0a
L_ed61: sub al, 0x3
L_ed63: jnz L_ed68
L_ed65: jmp near L_ee10
L_ed68: sub al, 0xa
L_ed6a: jnz L_ed6f
L_ed6c: jmp near L_ee16
L_ed6f: dec al
L_ed71: jz L_edb9
L_ed73: jmp near L_eeaa
L_ed76: cmp ax, strict word 0x88
L_ed79: jnz L_ed7e
L_ed7b: jmp near L_ee04
L_ed7e: jg L_ed8c
L_ed80: sub ax, strict word 0x84
L_ed83: jz L_edf8
L_ed85: dec ax
L_ed86: jz L_edfe
L_ed88: jmp near L_eeaa
nop ; original alignment instruction
L_ed8c: sub ax, strict word 0x8d
L_ed8f: jz L_ee0a
L_ed91: sub ax, strict word 0x3
L_ed94: jz L_ee10
L_ed96: sub ax, strict word 0xb
L_ed99: jmp short L_ed71
nop ; original alignment instruction
L_ed9c: call ansi_next_byte
L_ed9f: sub ax, strict word 0x46
L_eda2: jl L_edaa
L_eda4: dec ax
L_eda5: jg L_edaa
L_eda7: jmp near L_eeaa
L_edaa: call ansi_unread_byte
L_edad: jmp near L_eeaa
L_edb0: call ansi_escape_service_e0f8
L_edb3: jmp near L_eeaa
L_edb6: call ansi_next_byte
L_edb9: sub_load ax, ax
L_edbb: mov [ansi_parameter_count], ax
L_edbe: mov [ansi_parameters], ax
L_edc1: mov [ansi_private], ax
L_edc4: mov [ansi_secondary], ax
L_edc7: mov si, 0x44
L_edca: mov_load ax, si
L_edcc: cmp ax, strict word 0x53
L_edcf: jz L_ee36
L_edd1: jbe L_edd6
L_edd3: jmp near L_eeaa
L_edd6: sub al, 0x44
L_edd8: jz L_ee28
L_edda: sub al, 0x8
L_eddc: jz L_ee30
L_edde: pop si
L_eddf: mov_load sp, bp
L_ede1: pop bp
L_ede2: ret
nop ; original alignment instruction
L_ede4: sub_load ax, ax
L_ede6: push ax
L_ede7: call ansi_escape_service_dd74
L_edea: add sp, 0x2
L_eded: jmp near L_eeaa
L_edf0: sub_load ax, ax
L_edf2: push ax
L_edf3: call ansi_escape_service_ddbc
L_edf6: jmp short L_edea
L_edf8: call ansi_escape_service_da46
L_edfb: jmp near L_eeaa
L_edfe: call ansi_escape_service_12c8
L_ee01: jmp near L_eeaa
L_ee04: call ansi_escape_service_dac6
L_ee07: jmp near L_eeaa
L_ee0a: call ansi_escape_service_da84
L_ee0d: jmp near L_eeaa
L_ee10: call ansi_escape_service_ec94
L_ee13: jmp near L_eeaa
L_ee16: call ansi_escape_service_dd58
L_ee19: pop si
L_ee1a: mov_load sp, bp
L_ee1c: pop bp
L_ee1d: ret
L_ee1e: mov ax, 0x1
L_ee21: push ax
L_ee22: call ansi_escape_service_20a4
L_ee25: jmp short L_edea
nop ; original alignment instruction
L_ee28: call ansi_read_parameter
L_ee2b: mov_load si, ax
L_ee2d: jmp short L_edca
nop ; original alignment instruction
L_ee30: call ansi_dispatch_command
L_ee33: jmp short L_ee2b
nop ; original alignment instruction
L_ee36: call ansi_parameter_transition
L_ee39: jmp short L_ee2b
nop ; original alignment instruction
L_ee3c: call ansi_next_byte
L_ee3f: mov_load si, ax
L_ee41: or_load si, si
L_ee43: jz L_ee3c
L_ee45: sub_load ax, ax
L_ee47: mov [ansi_charset_g0_flag_a], ax
L_ee4a: mov [ansi_charset_g0_flag_graphics], ax
L_ee4d: mov_load ax, si
L_ee4f: cmp ax, strict word 0x41
L_ee52: jz L_ee6a
L_ee54: ja L_eeaa
L_ee56: sub al, 0x30
L_ee58: jz L_ee5e
L_ee5a: sub al, 0x2
L_ee5c: jnz L_eeaa
L_ee5e: mov word [ansi_charset_g0_flag_graphics], 0x1
L_ee64: pop si
L_ee65: mov_load sp, bp
L_ee67: pop bp
L_ee68: ret
nop ; original alignment instruction
L_ee6a: mov word [ansi_charset_g0_flag_a], 0x1
L_ee70: pop si
L_ee71: mov_load sp, bp
L_ee73: pop bp
L_ee74: ret
nop ; original alignment instruction
L_ee76: call ansi_next_byte
L_ee79: mov_load si, ax
L_ee7b: or_load si, si
L_ee7d: jz L_ee76
L_ee7f: sub_load ax, ax
L_ee81: mov [ansi_charset_g1_flag_a], ax
L_ee84: mov [ansi_charset_g1_flag_graphics], ax
L_ee87: mov_load ax, si
L_ee89: cmp ax, strict word 0x41
L_ee8c: jz L_eea4
L_ee8e: ja L_eeaa
L_ee90: sub al, 0x30
L_ee92: jz L_ee98
L_ee94: sub al, 0x2
L_ee96: jnz L_eeaa
L_ee98: mov word [ansi_charset_g1_flag_graphics], 0x1
L_ee9e: pop si
L_ee9f: mov_load sp, bp
L_eea1: pop bp
L_eea2: ret
nop ; original alignment instruction
L_eea4: mov word [ansi_charset_g1_flag_a], 0x1
L_eeaa: pop si
L_eeab: mov_load sp, bp
L_eead: pop bp
L_eeae: ret
