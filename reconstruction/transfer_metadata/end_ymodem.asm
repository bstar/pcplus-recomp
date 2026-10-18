; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_end_ymodem
global metadata_at_efcd
global metadata_at_efcf
global metadata_at_efd2
global metadata_at_efd3
global metadata_at_efd4
global metadata_at_efd7
global metadata_at_efd8
global metadata_at_efdb
global metadata_at_efde
global metadata_at_efe1
global metadata_at_efe2
global metadata_at_efe5
global metadata_at_efe8
global metadata_at_efeb
global metadata_at_efec
global metadata_at_efef
global metadata_at_eff2
global metadata_at_eff4
global metadata_at_eff7
global metadata_at_eff8
global metadata_at_effa
global metadata_at_efff
global metadata_at_f001
global metadata_at_f004
global metadata_at_f005
global metadata_at_f008
global metadata_at_f00b
global metadata_at_f00d
global metadata_at_f010
global metadata_at_f013
global metadata_at_f015
global metadata_at_f016
global metadata_at_f017
global metadata_at_f019
global metadata_at_f01a
extern metadata_protocol
extern metadata_send_zero
extern metadata_timed_byte
extern metadata_transmit_byte
extern receive_drain
%else
ORG 0xefcc
%define metadata_protocol 0x3996
%define metadata_send_zero 0x40aa
%define metadata_timed_byte 0xaad9
%define metadata_transmit_byte 0xab0b
%define receive_drain 0xf03e
%endif
%include "encodings.inc"
metadata_end_ymodem: push bp
metadata_at_efcd: mov_load bp,sp
metadata_at_efcf: sub sp,0x2
metadata_at_efd2: push di
metadata_at_efd3: push si
metadata_at_efd4: mov ax,0xf
metadata_at_efd7: push ax
metadata_at_efd8: call metadata_timed_byte
metadata_at_efdb: call receive_drain
metadata_at_efde: mov ax,0x1
metadata_at_efe1: push ax
metadata_at_efe2: call metadata_transmit_byte
metadata_at_efe5: call metadata_send_zero
metadata_at_efe8: mov ax,0xff
metadata_at_efeb: push ax
metadata_at_efec: call metadata_transmit_byte
metadata_at_efef: mov si,0x82
metadata_at_eff2: mov_load di,si
metadata_at_eff4: call metadata_send_zero
metadata_at_eff7: dec si
metadata_at_eff8: jnz short metadata_at_eff4
metadata_at_effa: cmp word [metadata_protocol],0xb
metadata_at_efff: jz short metadata_at_f015
metadata_at_f001: mov ax,0xf
metadata_at_f004: push ax
metadata_at_f005: call metadata_timed_byte
metadata_at_f008: cmp ax,strict word 0x6
metadata_at_f00b: jz short metadata_at_f015
metadata_at_f00d: lea ax,[di+0x1]
metadata_at_f010: cmp ax,strict word 0x3
metadata_at_f013: jl short metadata_at_efdb
metadata_at_f015: pop si
metadata_at_f016: pop di
metadata_at_f017: mov_load sp,bp
metadata_at_f019: pop bp
metadata_at_f01a: ret
