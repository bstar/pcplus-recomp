; Exact original PCPlus2.01 CRC instructions.
BITS 16
CPU 8086
%ifdef TRANSFER_BLOCKS_OMF
SEGMENT _TEXT public class=CODE use16
global transfer_crc_finish_original
extern transfer_crc_update_original
%else
ORG 0x5c5c
%define transfer_crc_update_original 0x5c42
%endif
%include "encodings.inc"
transfer_crc_finish_original:
L_5c5c: push bp
L_5c5d: mov_load bp,sp
L_5c5f: sub_load ax,ax
L_5c61: push ax
L_5c62: push ax
L_5c63: push word [bp + 0x4]
L_5c66: call transfer_crc_update_original
L_5c69: mov word [bp + 0x4], ax
L_5c6c: push ax
L_5c6d: call transfer_crc_update_original
L_5c70: mov word [bp + 0x4], ax
L_5c73: mov_load sp,bp
L_5c75: pop bp
L_5c76: ret
