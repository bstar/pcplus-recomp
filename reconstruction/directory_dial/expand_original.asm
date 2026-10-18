; Exact PCPlus2.01 overlay5:ec61..edf1.
BITS 16
CPU 8086
%ifdef DIRECTORY_DIAL_OMF
SEGMENT _TEXT public class=CODE use16
global directory_dial_expand_original
extern directory_dial_append_original
extern directory_dial_codes
extern directory_dial_integer_original
extern directory_dial_length_original
extern directory_dial_load_record
extern directory_dial_record
extern directory_dial_tokens
extern directory_dial_upper_original
%else
ORG 0xec61
%define directory_dial_tokens 0x70b4
%define directory_dial_codes 0xe484
%define directory_dial_record 0xe650
%define directory_dial_upper_original 0x9128
%define directory_dial_append_original 0x9852
%define directory_dial_length_original 0x8d18
%define directory_dial_integer_original 0x984e
%define directory_dial_load_record 0xddb6
%endif
%include "encodings.inc"
directory_dial_expand_original:
L_ec61: push bp
L_ec62: mov_load bp,sp
L_ec64: sub sp, 0xa
L_ec67: push di
L_ec68: push si
L_ec69: mov bx, word [bp + 0x6]
L_ec6c: mov byte [bx], 0x0
L_ec6f: mov ax, 0x7
L_ec72: imul word [bp + 0x4]
L_ec75: mov word [bp + -0xa], ax
L_ec78: add ax,strict word directory_dial_tokens
L_ec7b: push ax
L_ec7c: call directory_dial_upper_original
L_ec7f: pop bx
L_ec80: sub_load ax,ax
L_ec82: mov word [bp + -0x6], ax
L_ec85: mov word [bp + -0x4], ax
L_ec88: jmp short L_ecce
L_ec8a: mov ax, 0x7
L_ec8d: imul word [bp + 0x4]
L_ec90: mov_load si,ax
L_ec92: cmp byte [bx + si + directory_dial_tokens], 0x4b
L_ec97: jge L_ecdb
L_ec99: cmp word [bp + -0x6], 0x3c
L_ec9d: jge L_ecdb
L_ec9f: mov ax, 0x3c
L_eca2: sub ax, word [bp + -0x6]
L_eca5: push ax
L_eca6: mov ax, 0x7
L_eca9: imul word [bp + 0x4]
L_ecac: mov_load si,ax
L_ecae: mov al, 0x19
L_ecb0: imul byte [bx + si + directory_dial_tokens]
L_ecb4: add ax,strict word directory_dial_codes-1625
L_ecb7: push ax
L_ecb8: push word [bp + 0x6]
L_ecbb: call directory_dial_append_original
L_ecbe: add sp, 0x6
L_ecc1: push word [bp + 0x6]
L_ecc4: call directory_dial_length_original
L_ecc7: pop bx
L_ecc8: mov word [bp + -0x6], ax
L_eccb: inc word [bp + -0x4]
L_ecce: mov si, word [bp + -0xa]
L_ecd1: mov bx, word [bp + -0x4]
L_ecd4: cmp byte [bx + si + directory_dial_tokens], 0x40
L_ecd9: jg L_ec8a
L_ecdb: mov ax, 0x7
L_ecde: imul word [bp + 0x4]
L_ece1: add_load ax,bx
L_ece3: add ax,strict word directory_dial_tokens
L_ece6: push ax
L_ece7: call directory_dial_integer_original
L_ecea: pop bx
L_eceb: mov word [bp + -0x8], ax
L_ecee: or_load ax,ax
L_ecf0: jl L_ecf7
L_ecf2: cmp ax,strict word 0xc8
L_ecf5: jle L_ecfa
L_ecf7: jmp near L_ede8
L_ecfa: or_load ax,ax
L_ecfc: jz L_ed03
L_ecfe: push ax
L_ecff: call directory_dial_load_record
L_ed02: pop bx
L_ed03: mov ax, directory_dial_record+25
L_ed06: push ax
L_ed07: call directory_dial_upper_original
L_ed0a: pop bx
L_ed0b: mov word [bp + -0x2], 0x0
L_ed10: mov di, word [bp + -0x2]
L_ed13: jmp short L_ed59
L_ed15: cmp word [bp + -0x6], 0x3c
L_ed19: jge L_ed60
L_ed1b: cmp byte [di + directory_dial_record+25], 0x40
L_ed20: jle L_ed3b
L_ed22: cmp byte [di + directory_dial_record+25], 0x4b
L_ed27: jge L_ed3b
L_ed29: mov ax, 0x3c
L_ed2c: sub ax, word [bp + -0x6]
L_ed2f: push ax
L_ed30: mov al, 0x19
L_ed32: imul byte [di + directory_dial_record+25]
L_ed36: add ax,strict word directory_dial_codes-1625
L_ed39: jmp short L_ed44
L_ed3b: mov ax, 0x1
L_ed3e: push ax
L_ed3f: mov_load ax,di
L_ed41: add ax,strict word directory_dial_record+25
L_ed44: push ax
L_ed45: push word [bp + 0x6]
L_ed48: call directory_dial_append_original
L_ed4b: add sp, 0x6
L_ed4e: inc di
L_ed4f: push word [bp + 0x6]
L_ed52: call directory_dial_length_original
L_ed55: pop bx
L_ed56: mov word [bp + -0x6], ax
L_ed59: cmp byte [di + directory_dial_record+25], 0x0
L_ed5e: jnz L_ed15
L_ed60: mov ax, 0x7
L_ed63: imul word [bp + 0x4]
L_ed66: mov word [bp + -0xa], ax
L_ed69: mov si, word [bp + -0x4]
L_ed6c: mov di, word [bp + 0x4]
L_ed6f: jmp short L_ed82
L_ed71: mov_load ax,di
L_ed73: mov cx, 0x7
L_ed76: imul cx
L_ed78: mov_load bx,ax
L_ed7a: cmp byte [bx + si + directory_dial_tokens], 0x3a
L_ed7f: jge L_ed8c
L_ed81: inc si
L_ed82: mov bx, word [bp + -0xa]
L_ed85: cmp byte [bx + si + directory_dial_tokens], 0x2f
L_ed8a: jg L_ed71
L_ed8c: mov_load ax,di
L_ed8e: mov cx, 0x7
L_ed91: imul cx
L_ed93: mov word [bp + -0xa], ax
L_ed96: jmp short L_edd9
L_ed98: mov_load ax,di
L_ed9a: mov cx, 0x7
L_ed9d: imul cx
L_ed9f: mov_load bx,ax
L_eda1: cmp byte [bx + si + directory_dial_tokens], 0x4b
L_eda6: jge L_ede3
L_eda8: cmp word [bp + -0x6], 0x3c
L_edac: jge L_ede3
L_edae: mov ax, 0x3c
L_edb1: sub ax, word [bp + -0x6]
L_edb4: push ax
L_edb5: mov_load ax,di
L_edb7: imul cx
L_edb9: mov_load bx,ax
L_edbb: mov al, 0x19
L_edbd: imul byte [bx + si + directory_dial_tokens]
L_edc1: add ax,strict word directory_dial_codes-1625
L_edc4: push ax
L_edc5: push word [bp + 0x6]
L_edc8: call directory_dial_append_original
L_edcb: add sp, 0x6
L_edce: push word [bp + 0x6]
L_edd1: call directory_dial_length_original
L_edd4: pop bx
L_edd5: mov word [bp + -0x6], ax
L_edd8: inc si
L_edd9: mov bx, word [bp + -0xa]
L_eddc: cmp byte [bx + si + directory_dial_tokens], 0x40
L_ede1: jg L_ed98
L_ede3: mov ax, word [bp + -0x8]
L_ede6: jmp short L_edeb
L_ede8: mov ax, 0xc9
L_edeb: pop si
L_edec: pop di
L_eded: mov_load sp,bp
L_edef: pop bp
L_edf0: ret
