; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_geometry
extern display_mode
extern display_columns
extern display_stride
extern display_last_column
extern display_cursor_end
extern display_cursor_start
extern display_crt
extern display_mono
extern display_legacy
extern display_segment
extern display_last_row
extern display_cursor_row
extern display_rows
extern display_bytes
extern display_cells
extern display_last_line
extern display_status_port
extern display_snow
%define short
%else
ORG 27930
%define display_mode 31350
%define display_columns 31346
%define display_stride 31354
%define display_last_column 31358
%define display_cursor_end 31370
%define display_cursor_start 31368
%define display_crt 31376
%define display_mono 31366
%define display_legacy 31334
%define display_segment 31352
%define display_last_row 31360
%define display_cursor_row 31365
%define display_rows 31348
%define display_bytes 31356
%define display_cells 31372
%define display_last_line 31362
%define display_status_port 31374
%define display_snow 31378
%endif
%include "encodings.inc"
display_geometry:
L_6d1a: mov ah,0xf
L_6d1c: int byte 0x10
L_6d1e: mov [display_mode],al
L_6d21: mov [display_columns],ah
L_6d25: mov_load al,ah
L_6d27: xor_load ah,ah
L_6d29: shl ax,1
L_6d2b: mov [display_stride],ax
L_6d2e: shr ax,1
L_6d30: dec ax
L_6d31: mov [display_last_column],ax
L_6d34: xor_load ax,ax
L_6d36: mov es,ax
L_6d38: mov al,[es:0x460]
L_6d3c: mov [display_cursor_end],ax
L_6d3f: mov al,[es:0x461]
L_6d43: mov [display_cursor_start],ax
L_6d46: mov ax,[es:0x463]
L_6d4a: mov [display_crt],ax
L_6d4d: mov word [display_mono],0x0
L_6d53: cmp al,0xb4
L_6d55: jnz short L_6d5b
L_6d57: inc word [display_mono]
L_6d5b: cmp word [display_legacy],0x0
L_6d60: jnz short L_6d72
L_6d62: mov word [display_segment],0xb800
L_6d68: cmp al,0xb4
L_6d6a: jnz short L_6d72
L_6d6c: mov word [display_segment],0xb000
L_6d72: mov al,[es:0x484]
L_6d76: cmp al,0x18
L_6d78: jc short L_6d85
L_6d7a: cmp al,0x1d
L_6d7c: jnz short L_6d87
L_6d7e: cmp word [display_legacy],0x0
L_6d83: jz short L_6d87
L_6d85: mov al,0x18
L_6d87: xor_load ah,ah
L_6d89: mov [display_last_row],ax
L_6d8c: mov [display_cursor_row],al
L_6d8f: inc ax
L_6d90: mov [display_rows],ax
L_6d93: mul word [display_stride]
L_6d97: mov [display_bytes],ax
L_6d9a: shr ax,1
L_6d9c: mov [display_cells],ax
L_6d9f: shl ax,1
L_6da1: sub ax,[display_stride]
L_6da5: mov [display_last_line],ax
L_6da8: mov word [display_status_port],0x0
L_6dae: cmp word [display_snow],0x0
L_6db3: jz short L_6dc9
L_6db5: cmp word [display_legacy],0x0
L_6dba: jnz short L_6dc9
L_6dbc: cmp word [display_mono],0x0
L_6dc1: jnz short L_6dc9
L_6dc3: mov word [display_status_port],0x3da
L_6dc9: ret
