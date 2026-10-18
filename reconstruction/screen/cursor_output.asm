; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_cursor_output
extern screen_use_bios_cursor
extern screen_columns
%define short
%else
ORG 0x6e78
%define screen_use_bios_cursor 0x7a66
%define screen_columns 0x7a72
%endif
%include "encodings.inc"
screen_cursor_output:
L_6e78: mov_load bx,sp
L_6e7a: mov dx,[bx+0x2]
L_6e7d: cmp word [screen_use_bios_cursor],0x0
L_6e82: jnz short L_6eba
L_6e84: mov ax,0x40
L_6e87: mov es,ax
L_6e89: mov [es:0x50],dx
L_6e8e: mov_load ax,dx
L_6e90: mov_load bx,ax
L_6e92: mov_load al,ah
L_6e94: mul byte [screen_columns]
L_6e98: xor_load bh,bh
L_6e9a: add_load ax,bx
L_6e9c: mov_load cx,ax
L_6e9e: add cx,[es:0x4e]
L_6ea3: mov dx,[es:0x63]
L_6ea8: mov al,0xe
L_6eaa: out dx,al
L_6eab: inc dx
L_6eac: mov_load al,ch
L_6eae: out dx,al
L_6eaf: dec dx
L_6eb0: mov al,0xf
L_6eb2: out dx,al
L_6eb3: inc dx
L_6eb4: mov_load al,cl
L_6eb6: out dx,al
L_6eb7: ret word 0x2
L_6eba: mov bh,0x0
L_6ebc: mov ah,0x2
L_6ebe: int byte 0x10
L_6ec0: jmp short L_6eb7
