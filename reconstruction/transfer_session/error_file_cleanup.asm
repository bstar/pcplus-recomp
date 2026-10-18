; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_file_cleanup
global session_at_d8b3
global session_at_d8b5
global session_at_d8b7
global session_at_d8b8
global session_at_d8bb
global session_at_d8be
global session_at_d8c2
global session_at_d8c5
global session_at_d8c6
global session_at_d8ca
global session_at_d8ce
global session_at_d8d1
global session_at_d8d4
global session_at_d8d9
global session_at_d8db
global session_at_d8de
global session_at_d8e1
global session_at_d8e2
global session_at_d8e5
extern session_at_d7fe
extern session_at_d801
extern session_buffer_pointer
extern session_buffer_used
extern session_file_handle
extern session_file_write
extern session_serial_gate
extern session_serial_gate_set
%else
ORG 0xd8ae
%define session_at_d7fe 0xd7fe
%define session_at_d801 0xd801
%define session_buffer_pointer 0x39c0
%define session_buffer_used 0xcd34
%define session_file_handle 0xcbaa
%define session_file_write 0x86ac
%define session_serial_gate 0x1d1e
%define session_serial_gate_set 0xabfa
%endif
%include "encodings.inc"
session_file_cleanup: cmp word [session_serial_gate],0x0
session_at_d8b3: jz short session_at_d8be
session_at_d8b5: sub_load ax,ax
session_at_d8b7: push ax
session_at_d8b8: call session_serial_gate_set
session_at_d8bb: add sp,0x2
session_at_d8be: push word [session_file_handle]
session_at_d8c2: mov ax,0x1
session_at_d8c5: push ax
session_at_d8c6: push word [session_buffer_used]
session_at_d8ca: push word [session_buffer_pointer]
session_at_d8ce: call session_file_write
session_at_d8d1: add sp,0x8
session_at_d8d4: cmp word [session_serial_gate],0x0
session_at_d8d9: jnz short session_at_d8de
session_at_d8db: jmp near session_at_d801
session_at_d8de: mov ax,0x1
session_at_d8e1: push ax
session_at_d8e2: call session_serial_gate_set
session_at_d8e5: jmp near session_at_d7fe
