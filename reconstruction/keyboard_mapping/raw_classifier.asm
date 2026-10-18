; Maintained pure classifier for exact keyboard_read (first BIOS normalizer).
; Same result/register ABI as keyboard_classify; no I/O or callbacks.
; Original CS1604 raw keypad/E0 branches; table bytes are profile-selected.
; 1ce0/35e0 aliases are intentionally NOT invented here.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global keyboard_classify_raw
extern keyboard_classify,terminal_keymap
keyboard_classify_raw:
 test al,al
 jz .common
 test ah,ah
 jz .common
 cmp ax,0x49e0
 je .page_up
 cmp ax,0x51e0
 je .page_down
 cmp ax,0x73e0
 je .local
 cmp ax,0x74e0
 je .local
 mov bx,raw_vectors
 mov cx,raw_vector_count
.next:
 cmp ax,[cs:bx]
 je .found
 add bx,4
 loop .next
.common:
 jmp keyboard_classify
.found:
 mov ax,[cs:bx+2]
 ret
.page_up:
 cmp byte [terminal_keymap+58*12],0
 je .local
 mov ax,58
 ret
.page_down:
 cmp byte [terminal_keymap+59*12],0
 je .local
 mov ax,59
 ret
.local:
 mov ax,0xfffe
 ret
raw_vectors:
 dw 0x372a,0 ; keypad multiply
 dw 0x4a2d,1 ; keypad subtract
 dw 0x4e2b,2 ; keypad add
 dw 0x532e,3 ; keypad decimal
 dw 0xe02f,4 ; enhanced keypad divide
 dw 0xe00d,5 ; enhanced keypad Enter
 dw 0x5230,28 ; keypad zero through nine
 dw 0x4f31,29
 dw 0x5032,30
 dw 0x5133,31
 dw 0x4b34,32
 dw 0x4c35,33
 dw 0x4d36,34
 dw 0x4737,35
 dw 0x4838,36
 dw 0x4939,37
 dw 0x48e0,50 ; enhanced Up/Down/Left/Right
 dw 0x50e0,51
 dw 0x4be0,52
 dw 0x4de0,53
 dw 0x52e0,54 ; enhanced Insert/Delete/Home/End
 dw 0x53e0,55
 dw 0x47e0,56
 dw 0x4fe0,57
raw_vector_count equ ($-raw_vectors)/4
