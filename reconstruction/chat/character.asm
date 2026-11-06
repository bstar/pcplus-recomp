; Original2.01 bounded-region character renderer CS3D94. DS=SS.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0x3d94
%define screen_set_cursor 0x1bbe
%define screen_cursor_left 0x1e30
%define chat_bios_character 0x6c4a
%define chat_scroll 0x2530
%define chat_crlf 0x1d24
%define chat_row 0x399c
%define chat_column 0x399e
%define chat_last_column 0x3258
%define chat_attribute 0x1f70
%else
SEGMENT _TEXT public class=CODE use16
global chat_native_character
extern screen_set_cursor
extern screen_cursor_left
extern chat_bios_character
extern chat_scroll
extern chat_crlf
extern chat_row
extern chat_column
extern chat_last_column
extern chat_attribute
%endif
%include "encodings.inc"
chat_native_character:
L_3d94:
 push bp
L_3d95:
 mov_load bp,sp
L_3d97:
 cmp byte [bp+0x4],0xd
L_3d9b:
 jnz short L_3dd8
L_3d9d:
 cmp word [chat_crlf],0x1
L_3da2:
 jz short L_3dad
L_3da4:
 cmp word [bp+0x6],0x0
L_3da8:
 jg short L_3dad
L_3daa:
 jmp near L_3e64
L_3dad:
 mov ax,[bp+0x8]
L_3db0:
 cmp [chat_row],ax
L_3db4:
 jnl short L_3db9
L_3db6:
 jmp near L_3e60
L_3db9:
 mov ax,0x1
L_3dbc:
 push ax
L_3dbd:
 mov ah,[bp+0x6]
L_3dc0:
 sub_load al,al
L_3dc2:
 push ax
L_3dc3:
 mov ah,[bp+0x8]
L_3dc6:
 or ax,[chat_last_column]
L_3dca:
 push ax
L_3dcb:
 push word [chat_attribute]
L_3dcf:
 call chat_scroll
L_3dd2:
 mov ax,[bp+0x8]
L_3dd5:
 jmp near L_3e67
L_3dd8:
 cmp byte [bp+0x4],0xa
L_3ddc:
 jnz short L_3e13
L_3dde:
 cmp word [bp+0x6],0x0
L_3de2:
 jnz short L_3e13
L_3de4:
 mov ax,[bp+0x8]
L_3de7:
 cmp [chat_row],ax
L_3deb:
 jl short L_3e0c
L_3ded:
 mov ax,0x1
L_3df0:
 push ax
L_3df1:
 mov ah,[bp+0x6]
L_3df4:
 sub_load al,al
L_3df6:
 push ax
L_3df7:
 mov ah,[bp+0x8]
L_3dfa:
 or ax,[chat_last_column]
L_3dfe:
 push ax
L_3dff:
 push word [chat_attribute]
L_3e03:
 call chat_scroll
L_3e06:
 mov ax,[bp+0x8]
L_3e09:
 jmp near L_3e99
L_3e0c:
 inc word [chat_row]
L_3e10:
 jmp near L_3e96
L_3e13:
 cmp byte [bp+0x4],0xa
L_3e17:
 jnz short L_3e1c
L_3e19:
 jmp near L_3ea0
L_3e1c:
 cmp byte [bp+0x4],0x8
L_3e20:
 jnz short L_3e31
L_3e22:
 call screen_cursor_left
L_3e25:
 mov al,0x20
L_3e27:
 push ax
L_3e28:
 push word [chat_attribute]
L_3e2c:
 call chat_bios_character
L_3e2f:
 jmp short L_3ea0
L_3e31:
 cmp byte [bp+0x4],0x9
L_3e35:
 jz short L_3e78
L_3e37:
 mov al,[bp+0x4]
L_3e3a:
 push ax
L_3e3b:
 push word [chat_attribute]
L_3e3f:
 call chat_bios_character
L_3e42:
 mov ax,[chat_last_column]
L_3e45:
 cmp [chat_column],ax
L_3e49:
 jc short L_3e57
L_3e4b:
 mov ax,[bp+0x8]
L_3e4e:
 cmp [chat_row],ax
L_3e52:
 jl short L_3e57
L_3e54:
 jmp near L_3db9
L_3e57:
 mov ax,[chat_last_column]
L_3e5a:
 cmp [chat_column],ax
L_3e5e:
 jc short L_3e6b
L_3e60:
 inc word [chat_row]
L_3e64:
 mov ax,[chat_row]
L_3e67:
 sub_load dx,dx
L_3e69:
 jmp short L_3e9d
L_3e6b:
 inc word [chat_column]
L_3e6f:
 mov dx,[chat_column]
L_3e73:
 mov ax,[chat_row]
L_3e76:
 jmp short L_3e9d
L_3e78:
 inc word [chat_column]
L_3e7c:
 mov ax,[chat_column]
L_3e7f:
 mov cx,0x8
L_3e82:
 cwd
L_3e83:
 idiv cx
L_3e85:
 or_load dx,dx
L_3e87:
 jnz short L_3e78
L_3e89:
 mov ax,[chat_last_column]
L_3e8c:
 cmp [chat_column],ax
L_3e90:
 jna short L_3e96
L_3e92:
 mov [chat_column],dx
L_3e96:
 mov ax,[chat_row]
L_3e99:
 mov dx,[chat_column]
L_3e9d:
 call screen_set_cursor
L_3ea0:
 mov_load sp,bp
L_3ea2:
 pop bp
L_3ea3:
 ret
