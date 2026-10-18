; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_at_ddf6
global files_at_ddfa
global files_at_ddfd
global files_at_ddfe
global files_at_de02
global files_at_de06
global files_at_de09
global files_at_de0c
global files_at_de10
global files_at_de13
global files_at_de16
global files_at_de19
global files_at_de1a
global files_at_de1d
global files_at_de1f
global files_at_de20
global files_at_de24
global files_at_de27
global files_at_de28
global files_at_de2c
global files_at_de30
global files_at_de33
global files_at_de36
global files_at_de3a
global files_at_de3d
global files_at_de40
global files_at_de45
global files_at_de47
global files_at_de4a
global files_at_de4d
global files_at_de4e
global files_at_de51
global files_at_de54
global files_at_de57
extern files_receive_flow_switch
extern files_receive_buffer
extern files_receive_timestamp
extern files_fclose
extern files_fwrite
extern files_receive_flow
extern files_receive_stream
extern files_receive_used
extern files_receive_success
%else
ORG 0xddf6
%define files_receive_flow_switch 0x1d1e
%define files_receive_buffer 0x39c0
%define files_receive_timestamp 0x3af8
%define files_fclose 0x8318
%define files_fwrite 0x86ac
%define files_receive_flow 0xabfa
%define files_receive_stream 0xcbaa
%define files_receive_used 0xcd34
%define files_receive_success 0xda9e
%endif
%include "encodings.inc"
files_at_ddf6: push word [files_receive_stream]
files_at_ddfa: mov ax,0x1
files_at_ddfd: push ax
files_at_ddfe: push word [files_receive_used]
files_at_de02: push word [files_receive_buffer]
files_at_de06: call files_fwrite
files_at_de09: add sp,0x8
files_at_de0c: push word [files_receive_stream]
files_at_de10: call files_fclose
files_at_de13: add sp,0x2
files_at_de16: lea ax,[bp-0x56]
files_at_de19: push ax
files_at_de1a: call files_receive_timestamp
files_at_de1d: jmp short files_at_de3d
files_at_de1f: nop
files_at_de20: push word [files_receive_stream]
files_at_de24: mov ax,0x1
files_at_de27: push ax
files_at_de28: push word [files_receive_used]
files_at_de2c: push word [files_receive_buffer]
files_at_de30: call files_fwrite
files_at_de33: add sp,0x8
files_at_de36: push word [files_receive_stream]
files_at_de3a: call files_fclose
files_at_de3d: add sp,0x2
files_at_de40: cmp word [files_receive_flow_switch],0x0
files_at_de45: jnz short files_at_de4a
files_at_de47: jmp near files_receive_success
files_at_de4a: mov ax,0x1
files_at_de4d: push ax
files_at_de4e: call files_receive_flow
files_at_de51: add sp,0x2
files_at_de54: jmp near files_receive_success
files_at_de57: nop
%ifdef TRANSFER_FILES_OMF
jmp files_receive_success
%endif
