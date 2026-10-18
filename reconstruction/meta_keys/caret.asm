; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_expand
%define short
%else
ORG 0x4934
%endif
%include "encodings.inc"
meta_keys_expand:
L_4934: push bp
L_4935: mov_load bp,sp
L_4937: sub sp,0x2
L_493a: push di
L_493b: push si
L_493c: mov si,[bp+0x4]
L_493f: mov di,[bp+0x6]
L_4942: cmp byte [si],0x0
L_4945: jz short L_4982
L_4947: mov al,[si]
L_4949: mov [bp-0x1],al
L_494c: cmp al,0x5e
L_494e: jnz short L_4965
L_4950: inc si
L_4951: mov al,[si]
L_4953: cbw
L_4954: sub ax,strict word 0x40
L_4957: jz short L_496f
L_4959: sub ax,strict word 0x1e
L_495c: jz short L_4975
L_495e: mov al,[si]
L_4960: and al,0x1f
L_4962: mov [bp-0x1],al
L_4965: inc si
L_4966: mov al,[bp-0x1]
L_4969: inc di
L_496a: mov [di-0x1],al
L_496d: jmp short L_4942
L_496f: mov byte [bp-0x1],0xff
L_4973: jmp short L_4965
L_4975: cmp byte [si+0x1],0x5e
L_4979: jnz short L_495e
L_497b: mov byte [bp-0x1],0x5e
L_497f: inc si
L_4980: jmp short L_4965
L_4982: mov byte [di],0x0
L_4985: pop si
L_4986: pop di
L_4987: mov_load sp,bp
L_4989: pop bp
L_498a: ret
