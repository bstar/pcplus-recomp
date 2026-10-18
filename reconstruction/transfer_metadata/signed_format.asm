; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_signed_format
global metadata_at_9ae9
global metadata_at_9aeb
global metadata_at_9aec
global metadata_at_9aed
global metadata_at_9aef
extern meta_keys_decimal_core
%else
ORG 0x9ae8
%define meta_keys_decimal_core 0xa5e8
%endif
%include "encodings.inc"
metadata_signed_format: push bp
metadata_at_9ae9: mov_load bp,sp
metadata_at_9aeb: push si
metadata_at_9aec: push di
metadata_at_9aed: mov bl,0x1
metadata_at_9aef: jmp near meta_keys_decimal_core
