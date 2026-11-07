; Native 2.01 Alt-P key selector; wrapper/save/hardware owners are separate.
BITS 16
CPU 8086
%ifdef LINE_PORT_OMF
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
global line_port_key
extern line_port_port:wrt DGROUP
extern line_port_baud:wrt DGROUP
extern line_port_parity:wrt DGROUP
extern line_port_stop:wrt DGROUP
extern line_port_bits:wrt DGROUP
extern line_port_bell
extern line_port_quiesce
%else
ORG 0xf05c
%define line_port_port 0x1b84
%define line_port_baud 0x1b86
%define line_port_parity 0x1b88
%define line_port_stop 0x1b8a
%define line_port_bits 0x1b8c
%define line_port_bell 0x376d
%define line_port_quiesce 0xadba
%endif
%include "encodings.inc"
line_port_key:
L_f05c: push bp
L_f05d: mov_load bp,sp
L_f05f: mov dx,[bp+0x4]
L_f062: mov_load ax,dx
L_f064: sub ax,strict word 0x31
L_f067: jnc short L_f06c
L_f069: jmp near L_f129
L_f06c: sub ax,strict word 0x8
L_f06f: ja short L_f074
L_f071: jmp near L_f12f
L_f074: sub ax,strict word 0xc
L_f077: jnz short L_f07c
L_f079: jmp near L_f139
L_f07c: sub ax,strict word 0x8
L_f07f: jnz short L_f084
L_f081: jmp near L_f142
L_f084: dec ax
L_f085: jnz short L_f08a
L_f087: jmp near L_f14b
L_f08a: dec ax
L_f08b: jnz short L_f090
L_f08d: jmp near L_f154
L_f090: sub ax,strict word 0x4
L_f093: jnz short L_f098
L_f095: jmp near L_f15d
L_f098: sub ax,strict word 0x12
L_f09b: jnz short L_f0a0
L_f09d: jmp near L_f139
L_f0a0: sub ax,strict word 0x8
L_f0a3: jnz short L_f0a8
L_f0a5: jmp near L_f142
L_f0a8: dec ax
L_f0a9: jnz short L_f0ae
L_f0ab: jmp near L_f14b
L_f0ae: dec ax
L_f0af: jnz short L_f0b4
L_f0b1: jmp near L_f154
L_f0b4: sub ax,strict word 0x4
L_f0b7: jnz short L_f0bc
L_f0b9: jmp near L_f15d
L_f0bc: sub ax,0x118d
L_f0bf: jnz short L_f0c4
L_f0c1: jmp near L_f166
L_f0c4: sub ax,0x1f00
L_f0c7: jnz short L_f0cc
L_f0c9: jmp near L_f17a
L_f0cc: sub ax,0xa00
L_f0cf: jnz short L_f0d4
L_f0d1: jmp near L_f188
L_f0d4: sub ax,0x100
L_f0d7: jnz short L_f0dc
L_f0d9: jmp near L_f193
L_f0dc: sub ax,0x100
L_f0df: jnz short L_f0e4
L_f0e1: jmp near L_f19e
L_f0e4: sub ax,0x100
L_f0e7: jnz short L_f0ec
L_f0e9: jmp near L_f1a9
L_f0ec: sub ax,0x100
L_f0ef: jnz short L_f0f4
L_f0f1: jmp near L_f1b4
L_f0f4: sub ax,0x100
L_f0f7: jnz short L_f0fc
L_f0f9: jmp near L_f1bf
L_f0fc: sub ax,0x100
L_f0ff: jnz short L_f104
L_f101: jmp near L_f1ca
L_f104: sub ax,0x100
L_f107: jnz short L_f10c
L_f109: jmp near L_f1d5
L_f10c: sub ax,0x3600
L_f10f: jz short L_f172
L_f111: sub ax,0x100
L_f114: jnz short L_f119
L_f116: jmp near L_f1e0
L_f119: sub ax,0x500
L_f11c: jnz short L_f121
L_f11e: jmp near L_f1e8
L_f121: sub ax,0x100
L_f124: jnz short L_f129
L_f126: jmp near L_f1f0
L_f129: call line_port_bell
L_f12c: jmp near L_f1f6
L_f12f: sub dx,0x31
L_f132: mov [line_port_baud],dx
L_f136: jmp near L_f1f6
L_f139: mov word [line_port_parity],0x2
L_f13f: jmp near L_f1f6
L_f142: mov word [line_port_parity],0x3
L_f148: jmp near L_f1f6
L_f14b: mov word [line_port_parity],0x0
L_f151: jmp near L_f1f6
L_f154: mov word [line_port_parity],0x1
L_f15a: jmp near L_f1f6
L_f15d: mov word [line_port_parity],0x4
L_f163: jmp near L_f1f6
L_f166: mov word [line_port_parity],0x2
L_f16c: mov word [line_port_bits],0x7
L_f172: mov word [line_port_stop],0x1
L_f178: jmp short L_f1f6
L_f17a: mov word [line_port_parity],0x0
L_f180: mov word [line_port_bits],0x8
L_f186: jmp short L_f172
L_f188: call line_port_quiesce
L_f18b: mov word [line_port_port],0x0
L_f191: jmp short L_f1f6
L_f193: call line_port_quiesce
L_f196: mov word [line_port_port],0x1
L_f19c: jmp short L_f1f6
L_f19e: call line_port_quiesce
L_f1a1: mov word [line_port_port],0x2
L_f1a7: jmp short L_f1f6
L_f1a9: call line_port_quiesce
L_f1ac: mov word [line_port_port],0x3
L_f1b2: jmp short L_f1f6
L_f1b4: call line_port_quiesce
L_f1b7: mov word [line_port_port],0x4
L_f1bd: jmp short L_f1f6
L_f1bf: call line_port_quiesce
L_f1c2: mov word [line_port_port],0x5
L_f1c8: jmp short L_f1f6
L_f1ca: call line_port_quiesce
L_f1cd: mov word [line_port_port],0x6
L_f1d3: jmp short L_f1f6
L_f1d5: call line_port_quiesce
L_f1d8: mov word [line_port_port],0x7
L_f1de: jmp short L_f1f6
L_f1e0: mov word [line_port_stop],0x2
L_f1e6: jmp short L_f1f6
L_f1e8: mov word [line_port_bits],0x7
L_f1ee: jmp short L_f1f6
L_f1f0: mov word [line_port_bits],0x8
L_f1f6: mov_load sp,bp
L_f1f8: pop bp
L_f1f9: ret

%ifdef LINE_PORT_OMF
SEGMENT _DATA public class=DATA use16
%endif
