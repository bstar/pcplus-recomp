; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_receive_character
extern terminal_log_character
extern terminal_history_character
extern render_character
extern ansi_unread_byte
extern ansi_escape_entry
extern csi_terminal_id
extern terminal_escape_dispatch_table
extern terminal_control_dispatch_table
extern attributes_monochrome
extern scroll_suppress_next_linefeed
extern terminal_input_mode_8fe8
extern terminal_c1_enabled
%define short
%else
ORG 0x610
%define terminal_log_character 0x9b6
%define terminal_history_character 0x5832
%define render_character 0x730
%define ansi_unread_byte 0xabde
%define ansi_escape_entry 0xb973
%define csi_terminal_id 0x1d18
%define terminal_escape_dispatch_table 0x445e
%define terminal_control_dispatch_table 0x44a0
%define attributes_monochrome 0x8ff6
%define scroll_suppress_next_linefeed 0x3340
%define terminal_input_mode_8fe8 0x8fe8
%define terminal_c1_enabled 0x1d30
%endif
%include "encodings.inc"
terminal_receive_character:
L_0610: push bp
L_0611: mov_load bp,sp
L_0613: push si
L_0614: mov si,[bp+0x4]
%ifdef INPUT_DISPATCH_OMF
 and si,0xff ; Maintained byte ABI: prevent negative word indices before control tables.
%endif
L_0617: cmp si,0x1b
L_061a: jnz short L_062c
L_061c: mov bx,[csi_terminal_id]
L_0620: shl bx,1
L_0622: call word near [bx+terminal_escape_dispatch_table]
L_0626: pop si
L_0627: mov_load sp,bp
L_0629: pop bp
L_062a: ret
L_062b: nop
L_062c: cmp si,0x20
L_062f: jnl short L_06b0
L_0631: cmp word [attributes_monochrome],0x0
L_0636: jz short L_068c
L_0638: mov_load ax,si
L_063a: cmp ax,strict word 0x1d
L_063d: ja short L_0684
L_063f: shl ax,1
L_0641: xchg ax,bx
L_0642: jmp word near [cs:bx+terminal_low_control_table]
L_0647: nop
terminal_low_control_table:
 dw L_06a3
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_06a3
 dw L_06a3
 dw L_0684
 dw L_06a3
 dw L_06a3
 dw L_06a3
 dw L_06a3
 dw L_0684
 dw L_06a3
 dw L_06a3
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_0684
 dw L_06a3
 dw L_0684
 dw L_0684
 dw L_06a3
 dw L_0684
 dw L_06a3
L_0684: push si
L_0685: call render_character
L_0688: jmp near L_0727
L_068b: nop
L_068c: cmp word [scroll_suppress_next_linefeed],0x0
L_0691: jz short L_06a3
L_0693: cmp si,0xd
L_0696: jz short L_06a3
L_0698: cmp si,0xa
L_069b: jz short L_06a3
L_069d: mov word [scroll_suppress_next_linefeed],0x0
L_06a3: mov_load bx,si
L_06a5: shl bx,1
L_06a7: call word near [bx+terminal_control_dispatch_table]
L_06ab: pop si
L_06ac: mov_load sp,bp
L_06ae: pop bp
L_06af: ret
L_06b0: cmp si,0x7f
L_06b3: jnz short L_06bc
L_06b5: cmp word [attributes_monochrome],0x0
L_06ba: jz short L_072a
L_06bc: cmp word [terminal_input_mode_8fe8],0x0
L_06c1: jz short L_0718
L_06c3: cmp word [terminal_c1_enabled],0x0
L_06c8: jz short L_0718
L_06ca: mov_load ax,si
L_06cc: sub ax,0x84
L_06cf: cmp ax,strict word 0x17
L_06d2: ja short L_0718
L_06d4: shl ax,1
L_06d6: xchg ax,bx
L_06d7: jmp word near [cs:bx+terminal_c1_table]
terminal_c1_table:
 dw L_070c
 dw L_070c
 dw L_0718
 dw L_0718
 dw L_070c
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_070c
 dw L_0718
 dw L_0718
 dw L_070c
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_0718
 dw L_070c
L_070c: call ansi_unread_byte
L_070f: call ansi_escape_entry
L_0712: pop si
L_0713: mov_load sp,bp
L_0715: pop bp
L_0716: ret
L_0717: nop
L_0718: push si
L_0719: call render_character
L_071c: add sp,0x2
L_071f: push si
L_0720: call terminal_history_character
L_0723: push si
L_0724: call terminal_log_character
L_0727: add sp,0x2
L_072a: pop si
L_072b: mov_load sp,bp
L_072d: pop bp
L_072e: ret
L_072f: nop
