; Recovered PCPlus 2.01 terminal support instructions; see docs/PROTECTED_ERASE.md.
BITS 16
CPU 8086
%ifdef PROTECTED_ERASE_OMF
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
global protected_erase_native
extern attribute_position_to_video
extern attribute_repair_write
extern attribute_repair_advance
extern erase_repair_attributes
extern screen_cursor_column
extern screen_cursor_row
extern screen_attribute_row_bytes
extern erase_cell_count
extern screen_attributes_base
extern erase_protection_mode
%define short
%else
ORG 0xf47c
%define attribute_position_to_video 0x2b86
%define attribute_repair_write 0x2c3a
%define attribute_repair_advance 0x2cf2
%define erase_repair_attributes 0x2d98
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_attribute_row_bytes 0x325a
%define erase_cell_count 0x325c
%define screen_attributes_base 0x39c4
%define erase_protection_mode 0x3736
%endif
%include "encodings.inc"
protected_erase_native:
L_f47c: push bp
L_f47d: mov_load bp,sp
L_f47f: sub sp,0xc
L_f482: push di
L_f483: push si
L_f484: mov ax,[screen_cursor_column]
L_f487: mov [bp-0x8],ax
L_f48a: mov ax,[screen_cursor_row]
L_f48d: mov [bp-0xa],ax
L_f490: lea ax,[bp-0xc]
L_f493: push ax
L_f494: call attribute_position_to_video
L_f497: mov ax,[screen_cursor_row]
L_f49a: mul word [screen_attribute_row_bytes]
L_f49e: mov_load si,ax
L_f4a0: cmp word [bp+0x4],0x0
L_f4a4: jz short L_f4ac
L_f4a6: mov dx,[erase_cell_count]
L_f4aa: jmp short L_f4b2
L_f4ac: mov dx,[screen_attribute_row_bytes]
L_f4b0: add_load dx,si
L_f4b2: mov_load cx,dx
L_f4b4: add cx,[screen_attributes_base]
L_f4b8: mov_load di,ax
L_f4ba: add di,[screen_cursor_column]
L_f4be: add di,[screen_attributes_base]
L_f4c2: cmp_load di,cx
L_f4c4: jnc short L_f4fd
L_f4c6: mov [bp-0x4],cx
L_f4c9: mov [bp-0x2],di
L_f4cc: mov_load si,di
L_f4ce: mov di,[bp+0x4]
L_f4d1: test byte [si],0x81
L_f4d4: jz short L_f4dc
L_f4d6: or_load di,di
L_f4d8: jz short L_f4fd
L_f4da: jmp short L_f4f0
L_f4dc: mov al,0x20
L_f4de: push ax
L_f4df: lea ax,[bp-0xc]
L_f4e2: push ax
L_f4e3: call attribute_repair_write
L_f4e6: cmp word [erase_protection_mode],0x0
L_f4eb: jz short L_f4f0
L_f4ed: or byte [si],0x1
L_f4f0: lea ax,[bp-0xc]
L_f4f3: push ax
L_f4f4: call attribute_repair_advance
L_f4f7: inc si
L_f4f8: cmp [bp-0x4],si
L_f4fb: ja short L_f4d1
L_f4fd: mov ax,0x3
L_f500: push ax
L_f501: call erase_repair_attributes
L_f504: pop si
L_f505: pop di
L_f506: mov_load sp,bp
L_f508: pop bp
L_f509: ret
