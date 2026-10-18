; Exact original PCPlus2.01 CRC instructions.
BITS 16
CPU 8086
%ifdef TRANSFER_BLOCKS_OMF
SEGMENT _TEXT public class=CODE use16
global transfer_crc_update_original
extern transfer_crc_table
%else
ORG 0x5c42
%define transfer_crc_table 0x39fc
%endif
%include "encodings.inc"
transfer_crc_update_original:
L_5c42: push bp
L_5c43: mov_load bp,sp
L_5c45: mov ah, byte [bp + 0x4]
L_5c48: sub_load al,al
L_5c4a: mov bl, byte [bp + 0x5]
L_5c4d: sub_load bh,bh
L_5c4f: shl bx, 0x1
L_5c51: xor ax, word [bx + transfer_crc_table]
L_5c55: xor ax, word [bp + 0x6]
L_5c58: pop bp
L_5c59: ret 0x4
