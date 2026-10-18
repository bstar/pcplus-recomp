; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_history_pair
extern terminal_history_pointer
extern terminal_history_end
extern terminal_history_start
extern terminal_history_wrapped
%define short
%else
ORG 0x58ce
%define terminal_history_pointer 0x4ebe
%define terminal_history_end 0x4ec6
%define terminal_history_start 0x4eba
%define terminal_history_wrapped 0x4ec8
%endif
%include "encodings.inc"
terminal_history_pair:
L_58ce: les di,word [terminal_history_pointer]
L_58d2: xchg ah,al
L_58d4: stosb
L_58d5: mov_load al,ah
L_58d7: cmp di,[terminal_history_end]
L_58db: jnc short L_58de
L_58dd: ret
L_58de: mov ax,[terminal_history_start]
L_58e1: mov_load di,ax
L_58e3: mov word [terminal_history_wrapped],0x1
L_58e9: ret
