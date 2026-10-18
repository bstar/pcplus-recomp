; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_validated
global session_at_da35
global session_at_da37
extern session_accept_data
extern session_batch_metadata_boundary
%else
ORG 0xda31
%define session_accept_data 0xdaea
%define session_batch_metadata_boundary 0xda3a
%endif
%include "encodings.inc"
session_validated: cmp word [bp-0xe],0x0
session_at_da35: jnz short session_batch_metadata_boundary
session_at_da37: jmp near session_accept_data
