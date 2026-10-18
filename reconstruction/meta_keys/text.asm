; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_send_text
extern meta_keys_expand
extern meta_keys_tick_delay
extern meta_keys_pace
extern meta_keys_echo
extern meta_keys_transmit
extern meta_pause_byte
extern meta_pacing
extern meta_local_echo
%define short
%else
ORG 0x48cc
%define meta_keys_expand 0x4934
%define meta_keys_tick_delay 0x6b98
%define meta_keys_pace 0x6b72
%define meta_keys_echo 0x610
%define meta_keys_transmit 0xab0b
%define meta_pause_byte 0x1d66
%define meta_pacing 0x1d68
%define meta_local_echo 0x1d1a
%endif
%include "encodings.inc"
meta_keys_send_text:
L_48cc: push bp
L_48cd: mov_load bp,sp
L_48cf: sub sp,0x82
L_48d3: push si
L_48d4: lea ax,[bp-0x82]
L_48d8: push ax
L_48d9: push word [bp+0x4]
L_48dc: call meta_keys_expand
L_48df: pop bx
L_48e0: pop bx
L_48e1: lea si,[bp-0x82]
L_48e5: jmp short L_4927
L_48e7: mov al,[meta_pause_byte]
L_48ea: cmp [bp-0x1],al
L_48ed: jnz short L_48f8
L_48ef: mov ax,0x9
L_48f2: push ax
L_48f3: call meta_keys_tick_delay
L_48f6: jmp short L_4927
L_48f8: cmp byte [bp-0x1],0xff
L_48fc: jnz short L_4906
L_48fe: sub_load ax,ax
L_4900: push ax
L_4901: call meta_keys_transmit
L_4904: jmp short L_4927
L_4906: cmp word [meta_local_echo],0x0
L_490b: jz short L_4917
L_490d: mov al,[bp-0x1]
L_4910: sub_load ah,ah
L_4912: push ax
L_4913: call meta_keys_echo
L_4916: pop bx
L_4917: mov al,[bp-0x1]
L_491a: sub_load ah,ah
L_491c: push ax
L_491d: call meta_keys_transmit
L_4920: push word [meta_pacing]
L_4924: call meta_keys_pace
L_4927: lodsb
L_4928: mov [bp-0x1],al
L_492b: or_load al,al
L_492d: jnz short L_48e7
L_492f: pop si
L_4930: mov_load sp,bp
L_4932: pop bp
L_4933: ret
