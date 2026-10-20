; Recovered PCPlus 2.01 keyboard routines, not original source.
; Flat mode preserves four original ranges; OMF mode links explicit state and callback.
; See docs/KEYBOARD.md for ABI, mouse peek/read tables and integration boundaries.
BITS 16
CPU 8086
%include "encodings.inc"
; Select just normalizers or BIOS read/peek plus normalizers, without queue
; ownership. Keep the default flat and complete OMF regions unchanged.
%ifdef KEYBOARD_BIOS_ONLY
%define KEYBOARD_NORMALIZERS_ONLY
%endif
%ifdef KEYBOARD_NORMALIZERS_ONLY
%define KEYBOARD_OMF
%endif
%ifdef KEYBOARD_OMF
SEGMENT _TEXT public class=CODE use16
global keyboard_normalize_bios
global keyboard_normalize_extended
%ifdef KEYBOARD_BIOS_ONLY
global keyboard_bios_read,keyboard_bios_peek
extern keyboard_bios_mode
%endif
%ifndef KEYBOARD_NORMALIZERS_ONLY
global keyboard_read
global keyboard_peek
global keyboard_poll
global keyboard_bios_read
global keyboard_bios_peek
global keyboard_queue_read
global keyboard_read_extended
extern keyboard_queue_count, keyboard_queue_index, keyboard_queue_active, keyboard_queue_peek, keyboard_queue_values, keyboard_bios_mode, keyboard_debug_gate, keyboard_debug_callback
%endif
%else
%ifndef KEYBOARD_REGION
%define KEYBOARD_REGION 0
%endif
%define keyboard_read 0x64fe
%define keyboard_peek 0x651a
%define keyboard_poll 0x6530
%define keyboard_normalize_bios 0x77d2
%define keyboard_bios_read 0x7836
%define keyboard_bios_peek 0x7842
%define keyboard_queue_read 0x7858
%define keyboard_read_extended 0x7878
%define keyboard_normalize_extended 0x7fe2
%define keyboard_debug_callback 0x57ae
%define keyboard_queue_count 0x7a62
%define keyboard_queue_index 0x7a64
%define keyboard_queue_active 0x7a60
%define keyboard_queue_peek 0x5df4
%define keyboard_queue_values 0x5e00
%define keyboard_bios_mode 0x7ac0
%define keyboard_debug_gate 0x397a
%endif
%ifdef KEYBOARD_OMF
%else
%if KEYBOARD_REGION = 0
ORG 0x64fe
%endif
%endif
%ifidn __OUTPUT_FORMAT__,obj
%ifdef KEYBOARD_NORMALIZERS_ONLY
%define KEYBOARD_EMIT 0
%else
%define KEYBOARD_EMIT 1
%endif
%else
%assign KEYBOARD_EMIT (KEYBOARD_REGION = 0)
%endif
%if KEYBOARD_EMIT
%ifdef KEYBOARD_OMF
keyboard_read:
%endif
L_64fe: push bp
L_64ff: mov_load bp, sp
L_6501: push si
L_6502: call keyboard_poll
L_6505: or_load ax, ax
L_6507: jz L_6502
L_6509: call keyboard_queue_read
L_650c: mov_load si, ax
L_650e: or_load si, si
L_6510: jnz L_6515
L_6512: call keyboard_bios_read
L_6515: pop si
L_6516: mov_load sp, bp
L_6518: pop bp
L_6519: ret
%ifdef KEYBOARD_OMF
keyboard_peek:
%endif
L_651a: cmp word [keyboard_queue_count], 0x0
L_651f: jz L_652c
L_6521: mov bx, word [keyboard_queue_index]
L_6525: shl bx, 0x1
L_6527: mov ax, word [bx + keyboard_queue_peek]
L_652b: ret
L_652c: call keyboard_bios_peek
L_652f: ret
%ifdef KEYBOARD_OMF
keyboard_poll:
%endif
L_6530: push si
L_6531: call keyboard_peek
L_6534: mov_load si, ax
L_6536: or_load si, si
L_6538: jz L_654f
L_653a: cmp si, 0x2c00
L_653e: jnz L_654f
L_6540: cmp word [keyboard_debug_gate], 0x0
L_6545: jl L_654f
L_6547: call keyboard_bios_read
L_654a: call keyboard_debug_callback
L_654d: sub_load si, si
L_654f: mov_load ax, si
L_6551: pop si
L_6552: ret
%endif
%ifdef KEYBOARD_OMF
%else
%if KEYBOARD_REGION = 1
ORG 0x77d2
%endif
%endif
%ifidn __OUTPUT_FORMAT__,obj
%define KEYBOARD_EMIT 1
%else
%assign KEYBOARD_EMIT (KEYBOARD_REGION = 1)
%endif
%if KEYBOARD_EMIT
%ifdef KEYBOARD_OMF
keyboard_normalize_bios:
%endif
L_77d2: mov_load bx, sp
L_77d4: mov ax, word [bx + 0x2]
L_77d7: cmp al, 0x0
L_77d9: jz L_77fa
L_77db: cmp al, 0xe0
L_77dd: jz L_77fa
L_77df: cmp ah, 0xe0
L_77e2: jz L_77fa
L_77e4: cmp ax, 0x3920
L_77e7: jz L_77f8
L_77e9: cmp ax, 0xe08
L_77ec: jz L_77fa
L_77ee: cmp ax, 0xe7f
L_77f1: jz L_77fa
L_77f3: cmp ax, 0x372a
L_77f6: jge L_77fa
L_77f8: xor_load ah, ah
L_77fa: ret 0x2
%endif
%ifdef KEYBOARD_OMF
%else
%if KEYBOARD_REGION = 2
ORG 0x7836
%endif
%endif
%ifidn __OUTPUT_FORMAT__,obj
%ifdef KEYBOARD_BIOS_ONLY
%define KEYBOARD_EMIT 1
%elifdef KEYBOARD_NORMALIZERS_ONLY
%define KEYBOARD_EMIT 0
%else
%define KEYBOARD_EMIT 1
%endif
%else
%assign KEYBOARD_EMIT (KEYBOARD_REGION = 2)
%endif
%if KEYBOARD_EMIT
%ifdef KEYBOARD_OMF
keyboard_bios_read:
%endif
L_7836: mov ah, byte [keyboard_bios_mode]
L_783a: int 0x16
L_783c: push ax
L_783d: call keyboard_normalize_bios
L_7840: ret
db 0 ; original alignment byte
%ifdef KEYBOARD_OMF
keyboard_bios_peek:
%endif
L_7842: mov ah, 0x1
L_7844: add ah, byte [keyboard_bios_mode]
L_7848: int 0x16
L_784a: jnz L_784f
L_784c: xor_load ax, ax
L_784e: ret
L_784f: cmp ax, strict word 0x0
L_7852: jnz L_784e
L_7854: mov ah, 0x1
L_7856: ret
db 0 ; original alignment byte
%ifndef KEYBOARD_NORMALIZERS_ONLY
%ifdef KEYBOARD_OMF
keyboard_queue_read:
%endif
L_7858: sub_load ax, ax
L_785a: cli
L_785b: cmp word [keyboard_queue_count], 0x0
L_7860: jz L_7876
L_7862: dec word [keyboard_queue_count]
L_7866: mov word [keyboard_queue_active], 0x0
L_786c: mov bx, word [keyboard_queue_index]
L_7870: shl bx, 0x1
L_7872: mov ax, word [bx + keyboard_queue_values]
L_7876: sti
L_7877: ret
%ifdef KEYBOARD_OMF
keyboard_read_extended:
%endif
L_7878: call keyboard_read
L_787b: push ax
L_787c: call keyboard_normalize_extended
L_787f: ret
%endif
%endif
%ifdef KEYBOARD_OMF
%else
%if KEYBOARD_REGION = 3
ORG 0x7fe2
%endif
%endif
%ifidn __OUTPUT_FORMAT__,obj
%define KEYBOARD_EMIT 1
%else
%assign KEYBOARD_EMIT (KEYBOARD_REGION = 3)
%endif
%if KEYBOARD_EMIT
%ifdef KEYBOARD_OMF
keyboard_normalize_extended:
%endif
L_7fe2: mov_load bx, sp
L_7fe4: mov ax, word [bx + 0x2]
L_7fe7: test ah, 0xf0
L_7fea: jz L_7ff4
L_7fec: cmp al, 0xe0
L_7fee: jz L_7ff7
L_7ff0: cmp al, 0x0
L_7ff2: jnz L_7ffb
L_7ff4: ret 0x2
L_7ff7: xor_load al, al
L_7ff9: jmp L_7ff4
L_7ffb: xor_load ah, ah
L_7ffd: jmp L_7ff4
%endif
