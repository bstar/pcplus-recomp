; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_get_ds
%define short
%else
ORG 0x76b0
%endif
%include "encodings.inc"
meta_keys_get_ds:
L_76b0: mov ax,ds
L_76b2: ret
