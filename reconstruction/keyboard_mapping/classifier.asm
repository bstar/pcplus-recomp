; Maintained pure classifier derived from original DS44e0 / CS1604 branches.
; AX normalized keyboard_read_extended word -> 0..78 slot, 0100|byte literal,
; FFFE local/unimplemented application service, FFFF unmapped. No I/O.
; BP/SI/DI/ES preserved. BX/CX/DX/flags volatile. Profile affects slot bytes,
; not this key classification. Raw retained-E0 words are outside this ABI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global keyboard_classify
keyboard_classify:
 test al,al
 jz .scan
 mov bx,ax
 cmp word [keyboard_mapping_hook_enabled],0
 je .plain
 mov al,[keyboard_mapping_hook_character]
 cbw
 cmp ax,bx
 je .local
 mov ax,bx
.plain:
 cmp ax,0x0e08
 je .backspace
 cmp ax,0x0e7f
 je .control_backspace
 test ah,ah
 jnz .unmapped
 cmp al,9
 je .tab
 cmp al,13
 je .enter
 cmp al,0x1c
 je .local
 cmp al,0x1d
 je .local
 cmp al,0x1f
 je .local
 or ax,0x100
 ret
.scan:
 mov al,ah
 xor ah,ah
 cmp ax,0x8c
 ja .unmapped
 cmp ax,0x49
 je .page
 cmp ax,0x51
 je .page
 cmp ax,0x84
 je .control_page
 cmp ax,0x76
 je .control_page
.lookup:
 mov bx,ax
 shl bx,1
 mov ax,[cs:scan_results+bx]
 ret
.page:
 cmp word [keyboard_mapping_scrollback_mode],0
 jne .local
 jmp short .lookup
.control_page:
 cmp word [keyboard_mapping_scrollback_mode],0
 jne .lookup
.local:
 mov ax,0xfffe
 ret
.unmapped:
 mov ax,0xffff
 ret
.backspace:
 mov ax,10
 ret
.control_backspace:
 mov ax,15
 ret
.tab:
 mov ax,6
 ret
.enter:
 mov ax,78
 ret
scan_results:
 dw 65535 ; scan 00, original CS:0e60
 dw 65535 ; scan 01, original CS:0e60
 dw 65535 ; scan 02, original CS:0e60
 dw 65534 ; scan 03, original CS:40aa
 dw 65535 ; scan 04, original CS:0e60
 dw 65535 ; scan 05, original CS:0e60
 dw 65535 ; scan 06, original CS:0e60
 dw 65535 ; scan 07, original CS:0e60
 dw 65535 ; scan 08, original CS:0e60
 dw 65535 ; scan 09, original CS:0e60
 dw 65535 ; scan 0a, original CS:0e60
 dw 65535 ; scan 0b, original CS:0e60
 dw 65535 ; scan 0c, original CS:0e60
 dw 65535 ; scan 0d, original CS:0e60
 dw 65535 ; scan 0e, original CS:0e60
 dw 7 ; scan 0f, original CS:138a
 dw 65534 ; scan 10, original CS:1350
 dw 65534 ; scan 11, original CS:ba0f
 dw 65534 ; scan 12, original CS:3316
 dw 65534 ; scan 13, original CS:baf3
 dw 65534 ; scan 14, original CS:ba1b
 dw 65534 ; scan 15, original CS:0553
 dw 65534 ; scan 16, original CS:1368
 dw 65534 ; scan 17, original CS:ba57
 dw 65534 ; scan 18, original CS:bac3
 dw 65534 ; scan 19, original CS:134c
 dw 65535 ; scan 1a, original CS:0e60
 dw 65535 ; scan 1b, original CS:0e60
 dw 65535 ; scan 1c, original CS:0e60
 dw 65535 ; scan 1d, original CS:0e60
 dw 65534 ; scan 1e, original CS:ba7b
 dw 65534 ; scan 1f, original CS:ba63
 dw 65534 ; scan 20, original CS:12d2
 dw 65534 ; scan 21, original CS:1302
 dw 65534 ; scan 22, original CS:1310
 dw 65534 ; scan 23, original CS:132e
 dw 65534 ; scan 24, original CS:3a25
 dw 65534 ; scan 25, original CS:1340
 dw 65534 ; scan 26, original CS:1a76
 dw 65535 ; scan 27, original CS:0e60
 dw 65535 ; scan 28, original CS:0e60
 dw 65535 ; scan 29, original CS:0e60
 dw 65535 ; scan 2a, original CS:0e60
 dw 65535 ; scan 2b, original CS:0e60
 dw 65534 ; scan 2c, original CS:56fe
 dw 65534 ; scan 2d, original CS:3250
 dw 65534 ; scan 2e, original CS:24e2
 dw 65534 ; scan 2f, original CS:1374
 dw 65534 ; scan 30, original CS:0401
 dw 65534 ; scan 31, original CS:ba6f
 dw 65534 ; scan 32, original CS:ba9f
 dw 65535 ; scan 33, original CS:0e60
 dw 65535 ; scan 34, original CS:0e60
 dw 65535 ; scan 35, original CS:0e60
 dw 65535 ; scan 36, original CS:0e60
 dw 65535 ; scan 37, original CS:0e60
 dw 65535 ; scan 38, original CS:0e60
 dw 65535 ; scan 39, original CS:0e60
 dw 65535 ; scan 3a, original CS:0e60
 dw 16 ; scan 3b, original CS:1564
 dw 17 ; scan 3c, original CS:1564
 dw 18 ; scan 3d, original CS:1564
 dw 19 ; scan 3e, original CS:1564
 dw 20 ; scan 3f, original CS:1564
 dw 21 ; scan 40, original CS:1564
 dw 22 ; scan 41, original CS:1564
 dw 23 ; scan 42, original CS:1564
 dw 24 ; scan 43, original CS:1564
 dw 25 ; scan 44, original CS:1564
 dw 65535 ; scan 45, original CS:0e60
 dw 65535 ; scan 46, original CS:0e60
 dw 76 ; scan 47, original CS:1524
 dw 72 ; scan 48, original CS:13c0
 dw 13 ; scan 49, original CS:14a8
 dw 65535 ; scan 4a, original CS:0e60
 dw 74 ; scan 4b, original CS:139c
 dw 65535 ; scan 4c, original CS:0e60
 dw 75 ; scan 4d, original CS:13ae
 dw 65535 ; scan 4e, original CS:0e60
 dw 77 ; scan 4f, original CS:153a
 dw 73 ; scan 50, original CS:13d2
 dw 14 ; scan 51, original CS:14c2
 dw 8 ; scan 52, original CS:15d6
 dw 9 ; scan 53, original CS:15b6
 dw 38 ; scan 54, original CS:154c
 dw 39 ; scan 55, original CS:154c
 dw 40 ; scan 56, original CS:154c
 dw 41 ; scan 57, original CS:154c
 dw 42 ; scan 58, original CS:154c
 dw 43 ; scan 59, original CS:154c
 dw 44 ; scan 5a, original CS:154c
 dw 45 ; scan 5b, original CS:154c
 dw 46 ; scan 5c, original CS:154c
 dw 47 ; scan 5d, original CS:154c
 dw 60 ; scan 5e, original CS:157c
 dw 61 ; scan 5f, original CS:157c
 dw 62 ; scan 60, original CS:157c
 dw 63 ; scan 61, original CS:157c
 dw 64 ; scan 62, original CS:157c
 dw 65 ; scan 63, original CS:157c
 dw 66 ; scan 64, original CS:157c
 dw 67 ; scan 65, original CS:157c
 dw 68 ; scan 66, original CS:157c
 dw 69 ; scan 67, original CS:157c
 dw 65534 ; scan 68, original CS:bb23
 dw 65534 ; scan 69, original CS:bb17
 dw 65534 ; scan 6a, original CS:332e
 dw 65534 ; scan 6b, original CS:ba3f
 dw 65534 ; scan 6c, original CS:1440
 dw 65534 ; scan 6d, original CS:bb47
 dw 65534 ; scan 6e, original CS:ba27
 dw 65534 ; scan 6f, original CS:145a
 dw 65535 ; scan 70, original CS:0e60
 dw 65534 ; scan 71, original CS:13e4
 dw 65535 ; scan 72, original CS:0e60
 dw 65534 ; scan 73, original CS:bab7
 dw 65534 ; scan 74, original CS:ba93
 dw 12 ; scan 75, original CS:1512
 dw 14 ; scan 76, original CS:14f6
 dw 11 ; scan 77, original CS:151a
 dw 65534 ; scan 78, original CS:1594
 dw 65534 ; scan 79, original CS:1594
 dw 65534 ; scan 7a, original CS:1594
 dw 65534 ; scan 7b, original CS:1594
 dw 65534 ; scan 7c, original CS:1594
 dw 65534 ; scan 7d, original CS:1594
 dw 65534 ; scan 7e, original CS:1594
 dw 65534 ; scan 7f, original CS:1594
 dw 65534 ; scan 80, original CS:1594
 dw 65534 ; scan 81, original CS:1594
 dw 65535 ; scan 82, original CS:0e60
 dw 65534 ; scan 83, original CS:1542
 dw 13 ; scan 84, original CS:14dc
 dw 26 ; scan 85, original CS:1404
 dw 27 ; scan 86, original CS:140e
 dw 48 ; scan 87, original CS:1418
 dw 49 ; scan 88, original CS:1422
 dw 70 ; scan 89, original CS:142c
 dw 71 ; scan 8a, original CS:1436
 dw 65535 ; scan 8b, original CS:0e60
 dw 65535 ; scan 8c, original CS:0e60
SEGMENT _DATA public class=DATA use16
global keyboard_mapping_scrollback_mode,keyboard_mapping_hook_enabled,keyboard_mapping_hook_character
keyboard_mapping_scrollback_mode: dw 0
keyboard_mapping_hook_enabled: dw 0
keyboard_mapping_hook_character: db 0
