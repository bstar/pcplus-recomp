; Exact PCPlus2.01 recovered original instructions.
BITS 16
CPU 8086
%ifdef DIRECTORY_ACCOUNTING_OMF
SEGMENT _TEXT public class=CODE use16
global directory_accounting_getdate_original
%else
ORG 0x776e
%endif
%include "encodings.inc"
directory_accounting_getdate_original:
L_776e: mov_load bx,sp
L_7770: mov bx, word [bx + 0x2]
L_7773: mov ah, 0x2a
L_7775: int 0x21
L_7777: sub_load ah,ah
L_7779: mov_load al,dh
L_777b: mov word [bx], ax
L_777d: mov_load al,dl
L_777f: mov word [bx + 0x2], ax
L_7782: sub cx, 0x76c
L_7786: mov word [bx + 0x4], cx
L_7789: ret 0x2
