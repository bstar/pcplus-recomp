; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_basename
global metadata_at_3ea5
global metadata_at_3ea7
global metadata_at_3ea8
global metadata_at_3ea9
global metadata_at_3eac
global metadata_at_3eaf
global metadata_at_3eb0
global metadata_at_3eb1
global metadata_at_3eb4
global metadata_at_3eb5
global metadata_at_3eb6
global metadata_at_3eb8
global metadata_at_3eba
global metadata_at_3ebc
global metadata_at_3ebf
global metadata_at_3ec1
global metadata_at_3ec4
global metadata_at_3ec5
global metadata_at_3ec6
global metadata_at_3ec9
global metadata_at_3eca
global metadata_at_3ecb
global metadata_at_3ecd
global metadata_at_3ecf
global metadata_at_3ed1
global metadata_at_3ed3
global metadata_at_3ed4
global metadata_at_3ed5
global metadata_at_3ed7
global metadata_at_3ed8
extern program_strrchr
%else
ORG 0x3ea4
%define program_strrchr 0x83c6
%endif
%include "encodings.inc"
metadata_basename: push bp
metadata_at_3ea5: mov_load bp,sp
metadata_at_3ea7: push di
metadata_at_3ea8: push si
metadata_at_3ea9: mov di,[bp+0x4]
metadata_at_3eac: mov ax,0x5c
metadata_at_3eaf: push ax
metadata_at_3eb0: push di
metadata_at_3eb1: call program_strrchr
metadata_at_3eb4: pop bx
metadata_at_3eb5: pop bx
metadata_at_3eb6: mov_load si,ax
metadata_at_3eb8: or_load si,si
metadata_at_3eba: jz short metadata_at_3ec1
metadata_at_3ebc: lea ax,[si+0x1]
metadata_at_3ebf: jmp short metadata_at_3ed3
metadata_at_3ec1: mov ax,0x3a
metadata_at_3ec4: push ax
metadata_at_3ec5: push di
metadata_at_3ec6: call program_strrchr
metadata_at_3ec9: pop bx
metadata_at_3eca: pop bx
metadata_at_3ecb: mov_load si,ax
metadata_at_3ecd: or_load si,si
metadata_at_3ecf: jnz short metadata_at_3ebc
metadata_at_3ed1: mov_load ax,di
metadata_at_3ed3: pop si
metadata_at_3ed4: pop di
metadata_at_3ed5: mov_load sp,bp
metadata_at_3ed7: pop bp
metadata_at_3ed8: ret
