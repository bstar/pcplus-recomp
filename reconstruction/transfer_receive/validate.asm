; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_at_d8e8
global receive_at_d8ed
global receive_at_d8f0
global receive_at_d8f2
global receive_at_d8f4
global receive_at_d8f8
global receive_at_d8fa
global receive_at_d8fe
global receive_at_d900
global receive_at_d903
global receive_at_d906
global receive_at_d909
global receive_at_d90b
global receive_at_d90e
global receive_at_d911
global receive_at_d912
global receive_at_d915
global receive_at_d918
global receive_at_d91b
global receive_at_d91e
global receive_at_d922
global receive_at_d924
global receive_at_d927
global receive_at_d92a
global receive_at_d92c
global receive_at_d92e
global receive_at_d932
global receive_at_d934
global receive_at_d939
global receive_at_d93b
global receive_at_d93e
global receive_at_d940
global receive_at_d943
global receive_at_d944
global receive_at_d947
global receive_at_d949
global receive_at_d94c
global receive_at_d94f
global receive_at_d951
global receive_at_d955
global receive_at_d957
global receive_at_d95a
global receive_at_d95c
global receive_at_d961
global receive_at_d963
global receive_at_d966
global receive_at_d969
global receive_at_d96d
global receive_at_d970
global receive_at_d973
global receive_at_d976
global receive_at_d977
global receive_at_d97a
global receive_at_d97d
global receive_at_d980
global receive_at_d982
global receive_at_d984
global receive_at_d988
global receive_at_d98a
global receive_at_d98c
global receive_at_d98e
global receive_at_d992
global receive_at_d996
global receive_at_d998
global receive_at_d99d
global receive_at_d99f
global receive_at_d9a3
global receive_at_d9a6
global receive_at_d9a8
global receive_at_d9aa
global receive_at_d9ab
global receive_at_d9ae
global receive_at_d9b1
global receive_at_d9b3
global receive_at_d9b5
global receive_at_d9b7
global receive_at_d9ba
global receive_at_d9bc
global receive_at_d9be
global receive_at_d9c1
global receive_at_d9c4
global receive_at_d9c5
global receive_at_d9c8
global receive_at_d9cb
global receive_at_d9ce
global receive_at_d9cf
global receive_at_d9d2
global receive_at_d9d5
global receive_at_d9d7
global receive_at_d9d9
global receive_at_d9dc
global receive_at_d9e0
global receive_at_d9e2
global receive_at_d9e5
global receive_at_d9e9
global receive_at_d9eb
global receive_at_d9ef
global receive_at_d9f1
global receive_at_d9f3
global receive_at_d9f5
global receive_at_d9f9
global receive_at_d9fb
global receive_at_d9ff
global receive_at_da01
global receive_at_da04
global receive_at_da07
global receive_at_da09
global receive_at_da0e
global receive_at_da10
global receive_at_da14
global receive_at_da16
global receive_at_da19
global receive_at_da1c
global receive_at_da20
global receive_at_da22
global receive_at_da25
global receive_at_da28
global receive_at_da2c
global receive_at_da2e
extern receive_protocol
extern receive_buffer_pointer
extern receive_nak
extern transfer_crc_update_original
extern transfer_crc_finish_original
extern receive_timed_byte
extern receive_flush_input
extern receive_block_size
extern receive_crc_high
extern receive_crc_low
extern receive_wire_high
extern receive_wire_low
extern receive_last_block
extern receive_wire_block
extern receive_buffer_used
extern receive_error_count
extern receive_streaming_mode
extern receive_validated
extern receive_at_dbbc
extern receive_at_dbd8
extern receive_at_dc07
extern receive_status
%else
ORG 0xd8e8
%define receive_protocol 0x3996
%define receive_buffer_pointer 0x39c0
%define receive_nak 0x40b9
%define transfer_crc_update_original 0x5c42
%define transfer_crc_finish_original 0x5c5c
%define receive_timed_byte 0xaad9
%define receive_flush_input 0xabca
%define receive_block_size 0xcb5e
%define receive_crc_high 0xcbae
%define receive_crc_low 0xcbb2
%define receive_wire_high 0xcc46
%define receive_wire_low 0xcc94
%define receive_last_block 0xcc9a
%define receive_wire_block 0xcc9c
%define receive_buffer_used 0xcd34
%define receive_error_count 0xcd8a
%define receive_streaming_mode 0xcdcc
%define receive_validated 0xda31
%define receive_at_dbbc 0xdbbc
%define receive_at_dbd8 0xdbd8
%define receive_at_dc07 0xdc07
%define receive_status 0xe498
%endif
%include "encodings.inc"
receive_at_d8e8: mov word [bp-0xe],0x0
receive_at_d8ed: mov al,[receive_last_block]
receive_at_d8f0: inc al
receive_at_d8f2: sub_load ah,ah
receive_at_d8f4: cmp ax,[receive_wire_block]
receive_at_d8f8: jz short receive_at_d903
receive_at_d8fa: cmp word [bp-0xe],0x0
receive_at_d8fe: jnz short receive_at_d903
receive_at_d900: jmp near receive_at_dbd8
receive_at_d903: mov ax,[receive_buffer_used]
receive_at_d906: mov [bp-0xa],ax
receive_at_d909: sub_load si,si
receive_at_d90b: mov [bp-0xc],si
receive_at_d90e: mov ax,0xf
receive_at_d911: push ax
receive_at_d912: call receive_timed_byte
receive_at_d915: mov [bp-0x8],ax
receive_at_d918: mov al,[bp-0x8]
receive_at_d91b: mov bx,[bp-0xa]
receive_at_d91e: add bx,[receive_buffer_pointer]
receive_at_d922: mov [bx],al
receive_at_d924: inc word [bp-0xa]
receive_at_d927: inc word [bp-0xc]
receive_at_d92a: or_load di,di
receive_at_d92c: jz short receive_at_d93b
receive_at_d92e: cmp word [bp-0xe],0x0
receive_at_d932: jz short receive_at_d940
receive_at_d934: cmp word [receive_protocol],0x3
receive_at_d939: jnz short receive_at_d940
receive_at_d93b: add si,[bp-0x8]
receive_at_d93e: jmp short receive_at_d949
receive_at_d940: push word [bp-0x8]
receive_at_d943: push si
receive_at_d944: call transfer_crc_update_original
receive_at_d947: mov_load si,ax
receive_at_d949: mov ax,[receive_block_size]
receive_at_d94c: cmp [bp-0xc],ax
receive_at_d94f: jnl short receive_at_d957
receive_at_d951: cmp word [bp-0x8],0x0
receive_at_d955: jnl short receive_at_d90e
receive_at_d957: cmp [bp-0xc],ax
receive_at_d95a: jnl short receive_at_d980
receive_at_d95c: cmp word [receive_streaming_mode],0x0
receive_at_d961: jz short receive_at_d966
receive_at_d963: jmp near receive_at_dc07
receive_at_d966: inc word [bp-0x14]
receive_at_d969: inc word [receive_error_count]
receive_at_d96d: call receive_flush_input
receive_at_d970: call receive_nak
receive_at_d973: mov ax,0x2
receive_at_d976: push ax
receive_at_d977: call receive_status
receive_at_d97a: add sp,0x2
receive_at_d97d: jmp near receive_at_dc07
receive_at_d980: or_load di,di
receive_at_d982: jz short receive_at_d98a
receive_at_d984: cmp word [bp-0xe],0x0
receive_at_d988: jz short receive_at_d9a6
receive_at_d98a: or_load di,di
receive_at_d98c: jnz short receive_at_d992
receive_at_d98e: and si,0xff
receive_at_d992: cmp word [bp-0xe],0x0
receive_at_d996: jz short receive_at_d9a6
receive_at_d998: cmp word [receive_protocol],0x3
receive_at_d99d: jnz short receive_at_d9a6
receive_at_d99f: and si,0xff
receive_at_d9a3: mov [bp-0xa],si
receive_at_d9a6: or_load di,di
receive_at_d9a8: jz short receive_at_d9cb
receive_at_d9aa: push si
receive_at_d9ab: call transfer_crc_finish_original
receive_at_d9ae: add sp,0x2
receive_at_d9b1: mov_load si,ax
receive_at_d9b3: mov_load al,ah
receive_at_d9b5: sub_load ah,ah
receive_at_d9b7: mov [receive_crc_high],ax
receive_at_d9ba: mov_load ax,si
receive_at_d9bc: sub_load ah,ah
receive_at_d9be: mov [receive_crc_low],ax
receive_at_d9c1: mov ax,0x3
receive_at_d9c4: push ax
receive_at_d9c5: call receive_timed_byte
receive_at_d9c8: mov [receive_wire_high],ax
receive_at_d9cb: mov ax,0x3
receive_at_d9ce: push ax
receive_at_d9cf: call receive_timed_byte
receive_at_d9d2: mov [receive_wire_low],ax
receive_at_d9d5: or_load di,di
receive_at_d9d7: jz short receive_at_d9f1
receive_at_d9d9: mov ax,[receive_crc_high]
receive_at_d9dc: cmp [receive_wire_high],ax
receive_at_d9e0: jnz short receive_at_d9f1
receive_at_d9e2: mov ax,[receive_crc_low]
receive_at_d9e5: cmp [receive_wire_low],ax
receive_at_d9e9: jnz short receive_at_d9f1
receive_at_d9eb: cmp word [bp-0xe],0x0
receive_at_d9ef: jz short receive_validated
receive_at_d9f1: or_load di,di
receive_at_d9f3: jnz short receive_at_d9fb
receive_at_d9f5: cmp [receive_wire_low],si
receive_at_d9f9: jz short receive_validated
receive_at_d9fb: cmp word [bp-0xe],0x0
receive_at_d9ff: jz short receive_at_da10
receive_at_da01: mov ax,[receive_wire_high]
receive_at_da04: cmp [bp-0xa],ax
receive_at_da07: jnz short receive_at_da10
receive_at_da09: cmp word [receive_protocol],0x3
receive_at_da0e: jz short receive_validated
receive_at_da10: cmp word [bp-0xe],0x0
receive_at_da14: jnz short receive_at_da19
receive_at_da16: jmp near receive_at_dbbc
receive_at_da19: mov ax,[receive_crc_high]
receive_at_da1c: cmp [receive_wire_high],ax
receive_at_da20: jz short receive_at_da25
receive_at_da22: jmp near receive_at_dbbc
receive_at_da25: mov ax,[receive_crc_low]
receive_at_da28: cmp [receive_wire_low],ax
receive_at_da2c: jz short receive_validated
receive_at_da2e: jmp near receive_at_dbbc
%ifdef TRANSFER_RECEIVE_OMF
jmp receive_validated
%endif
