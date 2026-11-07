; Recovered 2.01 Meta Keys component; external UI boundaries remain explicit.
BITS 16
CPU 8086
%ifdef META_EDITOR_OMF
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
global meta_editor_defaults
extern meta_editor_records:wrt DGROUP
%define meta_editor_records_end (meta_editor_records+540)
%else
ORG 57930
%define meta_editor_records 0x3756
%define meta_editor_records_end 0x3972
%endif
%include "encodings.inc"
meta_editor_defaults:
L_e24a: mov bx,meta_editor_records
L_e24d: jmp short L_e25a
L_e24f: mov word [bx],0x3
L_e253: mov byte [bx+0x2],0x0
L_e257: add bx,0x36
L_e25a: cmp bx,meta_editor_records_end
L_e25e: jc short L_e24f
L_e260: ret
%ifdef META_EDITOR_OMF
SEGMENT _DATA public class=DATA use16
%endif
