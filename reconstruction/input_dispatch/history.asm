; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_history_character
extern terminal_history_pair
extern terminal_history_pending
extern terminal_history_pointer
extern terminal_history_end
extern terminal_history_start
extern terminal_history_wrapped
%define short
%else
ORG 0x5832
%define terminal_history_pair 0x58ce
%define terminal_history_pending 0x4ecc
%define terminal_history_pointer 0x4ebe
%define terminal_history_end 0x4ec6
%define terminal_history_start 0x4eba
%define terminal_history_wrapped 0x4ec8
%endif
%include "encodings.inc"
terminal_history_character:
L_5832: mov_load bx,sp
L_5834: mov al,[bx+0x2]
L_5837: mov_load bx,di
L_5839: cmp al,0xd
L_583b: jng short L_5874
L_583d: cmp byte [terminal_history_pending],0x1
L_5842: jnc short L_5866
L_5844: les di,word [terminal_history_pointer]
L_5848: stosb
L_5849: cmp di,[terminal_history_end]
L_584d: jnc short L_5858
L_584f: mov [terminal_history_pointer],di
L_5853: mov_load di,bx
L_5855: ret word 0x2
L_5858: mov ax,[terminal_history_start]
L_585b: mov [terminal_history_pointer],ax
L_585e: mov word [terminal_history_wrapped],0x1
L_5864: jmp short L_5853
L_5866: mov byte [terminal_history_pending],0x0
L_586b: jnz short L_5844
L_586d: mov ah,0xd
L_586f: call terminal_history_pair
L_5872: jmp short L_5848
L_5874: jnz short L_5886
L_5876: cmp byte [terminal_history_pending],0x1
L_587b: mov byte [terminal_history_pending],0x1
L_5880: jna short L_5853
L_5882: mov al,0x20
L_5884: jmp short L_5844
L_5886: cmp al,0xa
L_5888: jnz short L_58a2
L_588a: cmp byte [terminal_history_pending],0x1
L_588f: mov byte [terminal_history_pending],0x2
L_5894: ja short L_589a
L_5896: mov al,0xd
L_5898: jmp short L_5844
L_589a: mov ax,0x200d
L_589d: call terminal_history_pair
L_58a0: jmp short L_5848
L_58a2: cmp al,0x8
L_58a4: jnz short L_58c7
L_58a6: les di,word [terminal_history_pointer]
L_58aa: cmp di,[terminal_history_start]
L_58ae: jz short L_58ba
L_58b0: dec di
L_58b1: mov al,[es:di]
L_58b4: cmp al,0xd
L_58b6: jnz short L_584f
L_58b8: jmp short L_5853
L_58ba: cmp word [terminal_history_wrapped],0x1
L_58bf: jnz short L_5853
L_58c1: mov di,[terminal_history_end]
L_58c5: jmp short L_58b0
L_58c7: cmp al,0x0
L_58c9: jz short L_5853
L_58cb: jmp near L_583d
