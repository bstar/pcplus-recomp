; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_decimal32
extern meta_keys_decimal_core
%define short
%else
ORG 0x89fa
%define meta_keys_decimal_core 0xa5e8
%endif
%include "encodings.inc"
meta_keys_decimal32:
L_89fa: push bp
L_89fb: mov_load bp,sp
L_89fd: push si
L_89fe: push di
L_89ff: mov bl,0x0
L_8a01: jmp near meta_keys_decimal_core
