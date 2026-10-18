; Exact PCPlus2.01 recovered original instructions.
BITS 16
CPU 8086
%ifdef DIRECTORY_ACCOUNTING_OMF
SEGMENT _TEXT public class=CODE use16
global directory_accounting_success_fragment
extern directory_accounting_copy
extern directory_accounting_date_original
extern directory_accounting_load
extern directory_accounting_record
extern directory_accounting_store
extern directory_accounting_write_original
%else
ORG 0xd943
%define directory_accounting_load 0xddb6
%define directory_accounting_date_original 0x36d4
%define directory_accounting_copy 0x8268
%define directory_accounting_store 0xdd94
%define directory_accounting_write_original 0xdd28
%define directory_accounting_record 0xe650
%define directory_accounting_record 0xe650
%endif
%include "encodings.inc"
directory_accounting_success_fragment:
L_d943: push word [bp + -0x6]
L_d946: call directory_accounting_load
L_d949: pop bx
L_d94a: inc word [directory_accounting_record+70]
L_d94e: call directory_accounting_date_original
L_d951: push ax
L_d952: mov ax, directory_accounting_record+61
L_d955: push ax
L_d956: call directory_accounting_copy
L_d959: pop bx
L_d95a: pop bx
L_d95b: push word [bp + -0x6]
L_d95e: call directory_accounting_store
L_d961: pop bx
L_d962: sub_load ax,ax
L_d964: push ax
L_d965: push word [bp + -0x6]
L_d968: call directory_accounting_write_original
L_d96b: pop bx
L_d96c: pop bx
%ifdef DIRECTORY_ACCOUNTING_OMF
 ret ;Maintained standalone bridge after original internal span.
%endif
