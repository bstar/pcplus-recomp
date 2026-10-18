; Exact PCPlus2.01 recovered original instructions.
BITS 16
CPU 8086
%ifdef DIRECTORY_ACCOUNTING_OMF
SEGMENT _TEXT public class=CODE use16
global directory_accounting_write_original
extern directory_accounting_file
extern directory_accounting_flush
extern directory_accounting_fwrite
extern directory_accounting_load
extern directory_accounting_record
extern directory_accounting_seek
%else
ORG 0xdd28
%define directory_accounting_load 0xddb6
%define directory_accounting_seek 0x853a
%define directory_accounting_fwrite 0x86ac
%define directory_accounting_flush 0x8c54
%define directory_accounting_file 0xe648
%define directory_accounting_record 0xe650
%define directory_accounting_record 0xe650
%endif
%include "encodings.inc"
directory_accounting_write_original:
L_dd28: push bp
L_dd29: mov_load bp,sp
L_dd2b: sub sp, 0x4
L_dd2e: push di
L_dd2f: push si
L_dd30: push word [bp + 0x4]
L_dd33: call directory_accounting_load
L_dd36: pop bx
L_dd37: mov ax, 0x72
L_dd3a: imul word [bp + 0x4]
L_dd3d: add ax, 0x88
L_dd40: cwd
L_dd41: mov word [bp + -0x4], ax
L_dd44: mov word [bp + -0x2], dx
L_dd47: cmp word [bp + 0x6], 0x0
L_dd4b: jz short L_dd55
L_dd4d: mov di, 0x72
L_dd50: mov si, directory_accounting_record
L_dd53: jmp short L_dd63
L_dd55: add word [bp + -0x4], 0x3d
L_dd59: adc word [bp + -0x2], 0x0
L_dd5d: mov di, 0xb
L_dd60: mov si, directory_accounting_record+61
L_dd63: sub_load ax,ax
L_dd65: push ax
L_dd66: push word [bp + -0x2]
L_dd69: push word [bp + -0x4]
L_dd6c: push word [directory_accounting_file]
L_dd70: call directory_accounting_seek
L_dd73: add sp, 0x8
L_dd76: push word [directory_accounting_file]
L_dd7a: mov ax, 0x1
L_dd7d: push ax
L_dd7e: push di
L_dd7f: push si
L_dd80: call directory_accounting_fwrite
L_dd83: add sp, 0x8
L_dd86: push word [directory_accounting_file]
L_dd8a: call directory_accounting_flush
L_dd8d: pop bx
L_dd8e: pop si
L_dd8f: pop di
L_dd90: mov_load sp,bp
L_dd92: pop bp
L_dd93: ret
