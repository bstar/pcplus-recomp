; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_receive
global session_at_d6a5
global session_at_d6a7
global session_at_d6aa
global session_at_d6ab
global session_at_d6ac
global session_at_d6af
global session_at_d6b3
global session_at_d6b5
global session_at_d6b8
global session_at_d6bc
global session_at_d6bf
global session_at_d6c2
global session_at_d6c5
global session_at_d6c7
global session_at_d6c9
global session_at_d6ca
global session_at_d6cb
global session_at_d6ce
global session_at_d6d1
global session_at_d6d2
global session_at_d6d3
global session_at_d6d6
global session_at_d6d8
global session_at_d6da
global session_at_d6dc
global session_at_d6de
global session_at_d6e0
global session_at_d6e2
global session_at_d6e4
global session_at_d6e6
global session_at_d6e8
global session_at_d6e9
global session_at_d6ea
global session_at_d6eb
global session_at_d6ec
global session_at_d6ef
global session_at_d6f0
global session_at_d6f1
global session_at_d6f4
global session_at_d6f7
global session_at_d6f9
global session_at_d6fb
global session_at_d6fd
global session_at_d6ff
global session_at_d701
global session_at_d703
global session_at_d706
global session_at_d708
global session_at_d709
global session_at_d70b
global session_at_d70d
global session_at_d70f
global session_at_d711
global session_at_d713
global session_at_d714
global session_at_d715
global session_at_d718
global session_at_d719
global session_at_d71c
global session_at_d71d
global session_at_d720
global session_at_d723
global session_at_d726
global session_at_d728
global session_at_d72a
global session_at_d72d
global session_at_d72e
extern session_at_d73c
extern session_download_prefix
extern session_file_handle
extern session_file_open
extern session_handshake_enter
extern session_initialize
extern session_open_mode
extern session_path_test
extern session_status
extern session_failure_cleanup_argument
%else
ORG 0xd6a4
%define session_at_d73c 0xd73c
%define session_download_prefix 0x1ea0
%define session_file_handle 0xcbaa
%define session_file_open 0x841a
%define session_handshake_enter 0xd752
%define session_initialize 0xd656
%define session_open_mode 0x77f0
%define session_path_test 0x3717
%define session_status 0xe498
%endif
%include "encodings.inc"
session_receive: push bp
session_at_d6a5: mov_load bp,sp
session_at_d6a7: sub sp,0x58
session_at_d6aa: push di
session_at_d6ab: push si
session_at_d6ac: call session_initialize
session_at_d6af: cmp word [bp+0x4],0x0
session_at_d6b3: jnz short session_at_d6b8
session_at_d6b5: jmp near session_handshake_enter
session_at_d6b8: mov byte [bp-0x56],0x0
session_at_d6bc: push word [bp+0x4]
session_at_d6bf: call session_path_test
session_at_d6c2: add sp,0x2
session_at_d6c5: or_load ax,ax
session_at_d6c7: jz short session_at_d6ea
session_at_d6c9: push di
session_at_d6ca: push si
session_at_d6cb: mov di,session_download_prefix
session_at_d6ce: lea si,[bp-0x56]
session_at_d6d1: push ds
session_at_d6d2: pop es
session_at_d6d3: mov cx,0xffff
session_at_d6d6: xor_load ax,ax
session_at_d6d8: repne scasb
session_at_d6da: not cx
session_at_d6dc: sub_load di,cx
session_at_d6de: xchg di,si
session_at_d6e0: shr cx,1
session_at_d6e2: rep movsw
session_at_d6e4: adc_load cx,cx
session_at_d6e6: rep movsb
session_at_d6e8: pop si
session_at_d6e9: pop di
session_at_d6ea: push di
session_at_d6eb: push si
session_at_d6ec: lea si,[bp-0x56]
session_at_d6ef: push ds
session_at_d6f0: pop es
session_at_d6f1: mov di,[bp+0x4]
session_at_d6f4: mov cx,0xffff
session_at_d6f7: xor_load ax,ax
session_at_d6f9: repne scasb
session_at_d6fb: not cx
session_at_d6fd: sub_load di,cx
session_at_d6ff: mov_load bx,cx
session_at_d701: xchg di,si
session_at_d703: mov cx,0xffff
session_at_d706: repne scasb
session_at_d708: dec di
session_at_d709: mov_load cx,bx
session_at_d70b: shr cx,1
session_at_d70d: rep movsw
session_at_d70f: adc_load cx,cx
session_at_d711: rep movsb
session_at_d713: pop si
session_at_d714: pop di
session_at_d715: mov ax,session_open_mode
session_at_d718: push ax
session_at_d719: lea ax,[bp-0x56]
session_at_d71c: push ax
session_at_d71d: call session_file_open
session_at_d720: add sp,0x4
session_at_d723: mov [session_file_handle],ax
session_at_d726: or_load ax,ax
session_at_d728: jnz short session_at_d73c
session_at_d72a: mov ax,0xc
session_at_d72d: push ax
session_at_d72e: call session_status
%ifdef TRANSFER_SESSION_OMF
jmp session_failure_cleanup_argument
%endif
