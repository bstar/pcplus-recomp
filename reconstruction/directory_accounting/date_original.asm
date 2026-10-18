; Exact PCPlus2.01 recovered original instructions.
BITS 16
CPU 8086
%ifdef DIRECTORY_ACCOUNTING_OMF
SEGMENT _TEXT public class=CODE use16
global directory_accounting_date_original
extern directory_accounting_date_buffer
extern directory_accounting_date_format
extern directory_accounting_getdate_original
extern directory_accounting_sprintf
%else
ORG 0x36d4
%define directory_accounting_getdate_original 0x776e
%define directory_accounting_sprintf 0x82b6
%define directory_accounting_date_format 0x4729
%define directory_accounting_date_buffer 0xcdd6
%endif
%include "encodings.inc"
directory_accounting_date_original:
L_36d4: push bp
L_36d5: mov_load bp,sp
L_36d7: sub sp, 0x6
L_36da: lea ax, [bp + -0x6]
L_36dd: push ax
L_36de: call directory_accounting_getdate_original
L_36e1: push word [bp + -0x2]
L_36e4: push word [bp + -0x4]
L_36e7: push word [bp + -0x6]
L_36ea: mov ax, directory_accounting_date_format
L_36ed: push ax
L_36ee: mov ax, directory_accounting_date_buffer
L_36f1: push ax
L_36f2: call directory_accounting_sprintf
L_36f5: mov ax, directory_accounting_date_buffer
L_36f8: mov_load sp,bp
L_36fa: pop bp
L_36fb: ret
