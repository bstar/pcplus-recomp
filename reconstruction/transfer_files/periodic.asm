; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_at_db2a
global files_at_db2d
global files_at_db31
global files_at_db33
global files_at_db36
global files_at_db3a
global files_at_db3e
global files_at_db40
global files_at_db43
global files_at_db45
global files_at_db49
global files_at_db4b
global files_at_db4e
global files_at_db53
global files_at_db55
global files_at_db57
global files_at_db58
global files_at_db5b
global files_at_db5e
global files_at_db62
global files_at_db65
global files_at_db66
global files_at_db6a
global files_at_db6e
global files_at_db71
global files_at_db74
global files_at_db77
global files_at_db79
global files_at_db7c
global files_at_db7d
global files_at_db80
global files_at_db83
global files_at_db87
global files_at_db8a
global files_at_db8d
global files_at_db92
global files_at_db94
global files_at_db97
global files_at_db9a
global files_at_db9b
global files_at_db9e
global files_at_dba1
global files_at_dba2
global files_at_dba7
global files_at_dba9
global files_at_dbac
global files_at_dbad
global files_at_dbb0
global files_at_dbb3
global files_at_dbb9
global files_at_dbbb
extern files_receive_flow_switch
extern files_receive_buffer
extern files_fclose
extern files_fwrite
extern files_receive_total_low
extern files_receive_total_high
extern files_receive_size_low
extern files_receive_size_high
extern files_receive_flow
extern files_receive_stream
extern files_receive_used
extern files_receive_stack_failure
extern files_receive_failure
extern files_receive_resume
extern files_receive_status
%else
ORG 0xdb2a
%define files_receive_flow_switch 0x1d1e
%define files_receive_buffer 0x39c0
%define files_fclose 0x8318
%define files_fwrite 0x86ac
%define files_receive_total_low 0x8ffa
%define files_receive_total_high 0x8ffc
%define files_receive_size_low 0x9006
%define files_receive_size_high 0x9008
%define files_receive_flow 0xabfa
%define files_receive_stream 0xcbaa
%define files_receive_used 0xcd34
%define files_receive_stack_failure 0xd731
%define files_receive_failure 0xd734
%define files_receive_resume 0xdc07
%define files_receive_status 0xe498
%endif
%include "encodings.inc"
files_at_db2a: mov ax,[files_receive_size_high]
files_at_db2d: or ax,[files_receive_size_low]
files_at_db31: jz short files_at_db4e
files_at_db33: mov ax,[files_receive_total_low]
files_at_db36: mov dx,[files_receive_total_high]
files_at_db3a: cmp [files_receive_size_high],dx
files_at_db3e: jnl short files_at_db43
files_at_db40: jmp near files_receive_resume
files_at_db43: jg short files_at_db4e
files_at_db45: cmp [files_receive_size_low],ax
files_at_db49: ja short files_at_db4e
files_at_db4b: jmp near files_receive_resume
files_at_db4e: cmp word [files_receive_flow_switch],0x0
files_at_db53: jz short files_at_db5e
files_at_db55: sub_load ax,ax
files_at_db57: push ax
files_at_db58: call files_receive_flow
files_at_db5b: add sp,0x2
files_at_db5e: push word [files_receive_stream]
files_at_db62: mov ax,0x1
files_at_db65: push ax
files_at_db66: push word [files_receive_used]
files_at_db6a: push word [files_receive_buffer]
files_at_db6e: call files_fwrite
files_at_db71: add sp,0x8
files_at_db74: cmp ax,strict word 0x1
files_at_db77: jnc short files_at_dba2
files_at_db79: mov ax,0x3
files_at_db7c: push ax
files_at_db7d: call files_receive_status
files_at_db80: add sp,0x2
files_at_db83: push word [files_receive_stream]
files_at_db87: call files_fclose
files_at_db8a: add sp,0x2
files_at_db8d: cmp word [files_receive_flow_switch],0x0
files_at_db92: jnz short files_at_db97
files_at_db94: jmp near files_receive_failure
files_at_db97: mov ax,0x1
files_at_db9a: push ax
files_at_db9b: call files_receive_flow
files_at_db9e: jmp near files_receive_stack_failure
files_at_dba1: nop
files_at_dba2: cmp word [files_receive_flow_switch],0x0
files_at_dba7: jz short files_at_dbb3
files_at_dba9: mov ax,0x1
files_at_dbac: push ax
files_at_dbad: call files_receive_flow
files_at_dbb0: add sp,0x2
files_at_dbb3: mov word [files_receive_used],0x0
files_at_dbb9: jmp short files_receive_resume
files_at_dbbb: nop
%ifdef TRANSFER_FILES_OMF
jmp files_receive_resume
%endif
