; Native PCPlus2.01 FETCH: overlay19 E660..E672,18 exact bytes.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; NearRET, DS=SS. The selector is UNCHECKED, including EOF FFFF/wrapped indices.
; E38E remains1 after return. No status refresh. Table entries own destination ABI.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_FETCH_FLAT
ORG 0xe660
%define aspect_set_query_mode 0xe38e
%define aspect_dispatch_read 0x4cb4
%define aspect_set_table 0x4d24
%else
SEGMENT _TEXT public class=CODE use16
global aspect_fetch_command
extern aspect_set_query_mode,aspect_dispatch_read,aspect_set_table
%ifdef ASPECT_COMPACT_SET
extern aspect_set_resolve
%endif
%endif
aspect_fetch_command:
 mov word [aspect_set_query_mode],1
 call aspect_dispatch_read
%ifdef ASPECT_COMPACT_SET
 call aspect_set_resolve
%else
 mov_load bx,ax
 shl bx,1
 call word [bx+aspect_set_table]
%endif
 ret
