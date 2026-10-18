; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_send_ymodem
global metadata_at_e763
global metadata_at_e765
global metadata_at_e769
global metadata_at_e76a
global metadata_at_e76b
global metadata_at_e76d
global metadata_at_e770
global metadata_at_e774
global metadata_at_e775
global metadata_at_e776
global metadata_at_e778
global metadata_at_e77d
global metadata_at_e780
global metadata_at_e782
global metadata_at_e784
global metadata_at_e787
global metadata_at_e788
global metadata_at_e78b
global metadata_at_e78c
global metadata_at_e78f
global metadata_at_e792
global metadata_at_e795
global metadata_at_e797
global metadata_at_e799
global metadata_at_e79c
global metadata_at_e79d
global metadata_at_e7a0
global metadata_at_e7a1
global metadata_at_e7a4
global metadata_at_e7a7
global metadata_at_e7a9
global metadata_at_e7ac
global metadata_at_e7af
global metadata_at_e7b2
global metadata_at_e7b4
global metadata_at_e7b7
global metadata_at_e7b9
global metadata_at_e7bb
global metadata_at_e7bf
global metadata_at_e7c0
global metadata_at_e7c1
global metadata_at_e7c4
global metadata_at_e7c6
global metadata_at_e7cb
global metadata_at_e7cc
global metadata_at_e7cf
global metadata_at_e7d0
global metadata_at_e7d3
global metadata_at_e7d4
global metadata_at_e7d8
global metadata_at_e7dc
global metadata_at_e7df
global metadata_at_e7e2
global metadata_at_e7e4
global metadata_at_e7e7
global metadata_at_e7e9
global metadata_at_e7eb
global metadata_at_e7ef
global metadata_at_e7f0
global metadata_at_e7f1
global metadata_at_e7f4
global metadata_at_e7f6
global metadata_at_e7f9
global metadata_at_e7fc
global metadata_at_e7fd
global metadata_at_e800
global metadata_at_e803
global metadata_at_e806
global metadata_at_e807
global metadata_at_e80a
global metadata_at_e80c
global metadata_at_e810
global metadata_at_e811
global metadata_at_e812
global metadata_at_e815
global metadata_at_e816
global metadata_at_e81a
global metadata_at_e81c
global metadata_at_e81f
global metadata_at_e820
global metadata_at_e824
global metadata_at_e825
global metadata_at_e828
global metadata_at_e82b
global metadata_at_e82d
global metadata_at_e82f
global metadata_at_e831
global metadata_at_e834
global metadata_at_e836
global metadata_at_e83a
global metadata_at_e83b
global metadata_at_e83e
global metadata_at_e842
global metadata_at_e845
global metadata_at_e84a
global metadata_at_e84c
global metadata_at_e84f
global metadata_at_e850
global metadata_at_e853
global metadata_at_e856
global metadata_at_e858
global metadata_at_e85b
global metadata_at_e85f
global metadata_at_e861
global metadata_at_e864
global metadata_at_e866
global metadata_at_e869
global metadata_at_e86a
global metadata_at_e86b
global metadata_at_e86d
global metadata_at_e86e
global metadata_at_e86f
global metadata_at_e870
global metadata_at_e872
global metadata_at_e873
global metadata_at_e874
global metadata_at_e876
global metadata_at_e877
extern metadata_protocol
extern metadata_basename
extern metadata_local_cancel
extern metadata_send_zero
extern metadata_carrier
extern _transfer_crc_buffer_original
extern metadata_size_low
extern metadata_size_high
extern metadata_unwind
extern metadata_signed_format
extern metadata_timed_byte
extern metadata_transmit_byte
extern metadata_crc_high
extern metadata_crc_low
extern metadata_checkpoint
extern receive_drain
%else
ORG 0xe762
%define metadata_protocol 0x3996
%define metadata_basename 0x3ea4
%define metadata_local_cancel 0x3f4b
%define metadata_send_zero 0x40aa
%define metadata_carrier 0x4861
%define _transfer_crc_buffer_original 0x5c77
%define metadata_size_low 0x9006
%define metadata_size_high 0x9008
%define metadata_unwind 0x9065
%define metadata_signed_format 0x9ae8
%define metadata_timed_byte 0xaad9
%define metadata_transmit_byte 0xab0b
%define metadata_crc_high 0xcbae
%define metadata_crc_low 0xcbb2
%define metadata_checkpoint 0xcd94
%define receive_drain 0xf03e
%endif
%include "encodings.inc"
metadata_send_ymodem: push bp
metadata_at_e763: mov_load bp,sp
metadata_at_e765: sub sp,0xa4
metadata_at_e769: push di
metadata_at_e76a: push si
metadata_at_e76b: sub_load ax,ax
metadata_at_e76d: mov cx,0x80
metadata_at_e770: lea di,[bp-0xa4]
metadata_at_e774: push ss
metadata_at_e775: pop es
metadata_at_e776: rep stosb
metadata_at_e778: mov word [bp-0x2],0x0
metadata_at_e77d: call metadata_local_cancel
metadata_at_e780: or_load ax,ax
metadata_at_e782: jz short metadata_at_e792
metadata_at_e784: mov ax,0x7
metadata_at_e787: push ax
metadata_at_e788: mov ax,metadata_checkpoint
metadata_at_e78b: push ax
metadata_at_e78c: call metadata_unwind
metadata_at_e78f: add sp,0x4
metadata_at_e792: call metadata_carrier
metadata_at_e795: or_load ax,ax
metadata_at_e797: jnz short metadata_at_e7a7
metadata_at_e799: mov ax,0xf
metadata_at_e79c: push ax
metadata_at_e79d: mov ax,metadata_checkpoint
metadata_at_e7a0: push ax
metadata_at_e7a1: call metadata_unwind
metadata_at_e7a4: add sp,0x4
metadata_at_e7a7: sub_load di,di
metadata_at_e7a9: push word [bp+0x4]
metadata_at_e7ac: call metadata_basename
metadata_at_e7af: add sp,0x2
metadata_at_e7b2: mov_load si,ax
metadata_at_e7b4: cmp byte [si],0x0
metadata_at_e7b7: jz short metadata_at_e7c6
metadata_at_e7b9: mov al,[si]
metadata_at_e7bb: mov [bp+di-0xa4],al
metadata_at_e7bf: inc di
metadata_at_e7c0: inc si
metadata_at_e7c1: cmp byte [si],0x0
metadata_at_e7c4: jnz short metadata_at_e7b9
metadata_at_e7c6: mov byte [bp+di-0xa4],0x0
metadata_at_e7cb: inc di
metadata_at_e7cc: mov ax,0xa
metadata_at_e7cf: push ax
metadata_at_e7d0: lea ax,[bp-0x24]
metadata_at_e7d3: push ax
metadata_at_e7d4: push word [metadata_size_high]
metadata_at_e7d8: push word [metadata_size_low]
metadata_at_e7dc: call metadata_signed_format
metadata_at_e7df: add sp,0x8
metadata_at_e7e2: mov_load si,ax
metadata_at_e7e4: cmp byte [si],0x0
metadata_at_e7e7: jz short metadata_at_e7f6
metadata_at_e7e9: mov al,[si]
metadata_at_e7eb: mov [bp+di-0xa4],al
metadata_at_e7ef: inc di
metadata_at_e7f0: inc si
metadata_at_e7f1: cmp byte [si],0x0
metadata_at_e7f4: jnz short metadata_at_e7e9
metadata_at_e7f6: call receive_drain
metadata_at_e7f9: mov ax,0x1
metadata_at_e7fc: push ax
metadata_at_e7fd: call metadata_transmit_byte
metadata_at_e800: call metadata_send_zero
metadata_at_e803: mov ax,0xff
metadata_at_e806: push ax
metadata_at_e807: call metadata_transmit_byte
metadata_at_e80a: sub_load si,si
metadata_at_e80c: mov al,[bp+si-0xa4]
metadata_at_e810: cbw
metadata_at_e811: push ax
metadata_at_e812: call metadata_transmit_byte
metadata_at_e815: inc si
metadata_at_e816: cmp si,0x80
metadata_at_e81a: jl short metadata_at_e80c
metadata_at_e81c: mov ax,0x80
metadata_at_e81f: push ax
metadata_at_e820: lea ax,[bp-0xa4]
metadata_at_e824: push ax
metadata_at_e825: call _transfer_crc_buffer_original
metadata_at_e828: add sp,0x4
metadata_at_e82b: mov_load cx,ax
metadata_at_e82d: mov_load al,ah
metadata_at_e82f: sub_load ah,ah
metadata_at_e831: mov [metadata_crc_high],ax
metadata_at_e834: sub_load ch,ch
metadata_at_e836: mov [metadata_crc_low],cx
metadata_at_e83a: push ax
metadata_at_e83b: call metadata_transmit_byte
metadata_at_e83e: push word [metadata_crc_low]
metadata_at_e842: call metadata_transmit_byte
metadata_at_e845: cmp word [metadata_protocol],0xb
metadata_at_e84a: jz short metadata_at_e866
metadata_at_e84c: mov ax,0xa
metadata_at_e84f: push ax
metadata_at_e850: call metadata_timed_byte
metadata_at_e853: cmp ax,strict word 0x6
metadata_at_e856: jz short metadata_at_e866
metadata_at_e858: inc word [bp-0x2]
metadata_at_e85b: cmp word [bp-0x2],0x3
metadata_at_e85f: jnl short metadata_at_e864
metadata_at_e861: jmp near metadata_at_e77d
metadata_at_e864: jmp short metadata_at_e870
metadata_at_e866: mov ax,0x1
metadata_at_e869: pop si
metadata_at_e86a: pop di
metadata_at_e86b: mov_load sp,bp
metadata_at_e86d: pop bp
metadata_at_e86e: ret
metadata_at_e86f: nop
metadata_at_e870: sub_load ax,ax
metadata_at_e872: pop si
metadata_at_e873: pop di
metadata_at_e874: mov_load sp,bp
metadata_at_e876: pop bp
metadata_at_e877: ret
