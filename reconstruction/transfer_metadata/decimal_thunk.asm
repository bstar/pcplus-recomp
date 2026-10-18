; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_decimal_thunk
extern directory_dial_integer_original
%else
ORG 0x9b32
%define directory_dial_integer_original 0xa7ce
%endif
%include "encodings.inc"
metadata_decimal_thunk: jmp near directory_dial_integer_original
