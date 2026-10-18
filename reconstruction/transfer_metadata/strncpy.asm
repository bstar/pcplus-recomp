; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_strncpy
global metadata_at_9889
global metadata_at_988b
global metadata_at_988c
global metadata_at_988d
global metadata_at_988e
global metadata_at_988f
global metadata_at_9892
global metadata_at_9895
global metadata_at_9897
global metadata_at_989a
global metadata_at_989c
global metadata_at_989d
global metadata_at_989f
global metadata_at_98a1
global metadata_at_98a2
global metadata_at_98a4
global metadata_at_98a6
global metadata_at_98a8
global metadata_at_98aa
global metadata_at_98ab
global metadata_at_98ac
global metadata_at_98ae
global metadata_at_98af
%else
ORG 0x9888
%endif
%include "encodings.inc"
metadata_strncpy: push bp
metadata_at_9889: mov_load bp,sp
metadata_at_988b: push di
metadata_at_988c: push si
metadata_at_988d: push ds
metadata_at_988e: pop es
metadata_at_988f: mov di,[bp+0x4]
metadata_at_9892: mov si,[bp+0x6]
metadata_at_9895: mov_load bx,di
metadata_at_9897: mov cx,[bp+0x8]
metadata_at_989a: jcxz metadata_at_98a8
metadata_at_989c: lodsb
metadata_at_989d: or_load al,al
metadata_at_989f: jz short metadata_at_98a4
metadata_at_98a1: stosb
metadata_at_98a2: loop metadata_at_989c
metadata_at_98a4: xor_load al,al
metadata_at_98a6: rep stosb
metadata_at_98a8: mov_load ax,bx
metadata_at_98aa: pop si
metadata_at_98ab: pop di
metadata_at_98ac: mov_load sp,bp
metadata_at_98ae: pop bp
metadata_at_98af: ret
