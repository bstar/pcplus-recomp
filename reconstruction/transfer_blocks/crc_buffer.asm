; Exact original PCPlus2.01 CRC instructions.
BITS 16
CPU 8086
%ifdef TRANSFER_BLOCKS_OMF
SEGMENT _TEXT public class=CODE use16
global _transfer_crc_buffer_original
extern transfer_crc_finish_original
extern transfer_crc_update_original
%else
ORG 0x5c77
%define transfer_crc_update_original 0x5c42
%define transfer_crc_finish_original 0x5c5c
%endif
%include "encodings.inc"
_transfer_crc_buffer_original:
L_5c77: push bp
L_5c78: mov_load bp,sp
L_5c7a: push si
L_5c7b: sub_load si,si
L_5c7d: jmp short L_5c90
L_5c7f: mov bx, word [bp + 0x4]
L_5c82: inc word [bp + 0x4]
L_5c85: mov al, byte [bx]
L_5c87: sub_load ah,ah
L_5c89: push ax
L_5c8a: push si
L_5c8b: call transfer_crc_update_original
L_5c8e: mov_load si,ax
L_5c90: dec word [bp + 0x6]
L_5c93: jns short L_5c7f
L_5c95: push si
L_5c96: call transfer_crc_finish_original
L_5c99: pop bx
L_5c9a: pop si
L_5c9b: mov_load sp,bp
L_5c9d: pop bp
L_5c9e: ret
