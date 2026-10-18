; Source-only real-BIOS cursor shape diagnostic.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern modes_cursor_shape
global cursor_shape_test
cursor_shape_test:
 push word [cursor_shape_test_flags]
 call modes_cursor_shape
 add sp,2
 ret
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 mov ax,3
 int 0x10
 mov ah,3
 xor bh,bh
 int 0x10
 mov [saved_cursor_shape],cx
 call cursor_shape_test
 mov ah,3
 xor bh,bh
 int 0x10
 cmp cx,0x000f
 jne .failed
 mov word [cursor_shape_test_flags],0
 call cursor_shape_test
 mov ah,3
 xor bh,bh
 int 0x10
 test ch,0x20
 jz .failed
 cmp cl,15
 jne .failed
 mov word [cursor_shape_test_flags],6
 call cursor_shape_test
 mov ah,3
 xor bh,bh
 int 0x10
 cmp cx,0x080f
 jne .failed
 mov word [cursor_shape_test_flags],5
 call cursor_shape_test
 mov ah,3
 xor bh,bh
 int 0x10
 cmp cx,0x0e0f
 jne .failed
 mov cx,[saved_cursor_shape]
 mov ah,1
 int 0x10
 mov ax,0x4c00
 int 0x21
.failed:
 mov cx,[saved_cursor_shape]
 mov ah,1
 int 0x10
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public class=DATA use16
global cursor_shape_test_flags,cursor_shape_start_scanline,cursor_shape_end_scanline,cursor_shape_visibility_state
cursor_shape_test_flags: dw 4
cursor_shape_start_scanline: dw 6
cursor_shape_end_scanline: dw 15
cursor_shape_visibility_state: dw 1
saved_cursor_shape: dw 0
SEGMENT STACK stack class=STACK use16
 resb 4096
stack_top:
