; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_context_enter
global session_at_d87f
global session_at_d880
global session_at_d883
global session_at_d886
global session_at_d889
global session_at_d88b
global session_at_d88d
global session_at_d890
global session_at_d891
global session_at_d893
global session_at_d896
global session_at_d898
global session_at_d89c
global session_at_d89e
global session_at_d8a1
global session_at_d8a3
global session_at_d8a4
global session_at_d8a7
global session_at_d8a8
global session_at_d8ab
extern session_context
extern session_retry_enter
extern session_setjmp
extern session_status
extern session_file_cleanup
%else
ORG 0xd87c
%define session_context 0xcd94
%define session_retry_enter 0xdc1f
%define session_setjmp 0x9048
%define session_status 0xe498
%endif
%include "encodings.inc"
session_context_enter: mov ax,session_context
session_at_d87f: push ax
session_at_d880: call session_setjmp
session_at_d883: add sp,0x2
session_at_d886: mov [bp-0x12],ax
session_at_d889: or_load ax,ax
session_at_d88b: jnz short session_at_d890
session_at_d88d: jmp near session_retry_enter
session_at_d890: dec ax
session_at_d891: jnz short session_at_d898
session_at_d893: mov ax,0xa
session_at_d896: jmp short session_at_d8a7
session_at_d898: cmp word [bp-0x12],0xf
session_at_d89c: jnz short session_at_d8a4
session_at_d89e: mov ax,0xf
session_at_d8a1: jmp short session_at_d8a7
session_at_d8a3: nop
session_at_d8a4: mov ax,0xb
session_at_d8a7: push ax
session_at_d8a8: call session_status
session_at_d8ab: add sp,0x2
%ifdef TRANSFER_SESSION_OMF
%ifdef TRANSFER_SESSION_DIAGNOSTIC
extern session_file_cleanup_checkpoint
jmp session_file_cleanup_checkpoint
%else
jmp session_file_cleanup
%endif
%endif
