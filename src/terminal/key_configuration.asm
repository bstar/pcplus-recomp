; Startup-only keyboard configuration, before UART ownership.
; Modern network defaults are maintained choices, not historical PCPLUS.KBD.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_keymap,csi_terminal_id,terminal_option_mask,terminal_keyboard_path
extern _keymap_dos_read
extern keyboard_bios_mode,keyboard_detect_bios_mode,terminal_keyboard_bios_selection
extern keyboard_read
global terminal_load_keyboard,terminal_initialize_keymap,terminal_select_keyboard_bios
global terminal_read_key
global terminal_build_keymap

; AX0 success, AX9 keymap failure. Raw reader status/result retained privately.
; DS=SS, preserve BP/SI/DI/ES. Explicit /K replaces defaults only after complete
; selected-profile validation and successful close in the near-C reader.
terminal_load_keyboard:
 push bp
 push si
 push di
 push es
 cld
 call terminal_select_keyboard_bios
 call terminal_initialize_keymap
 or ax,ax
 jnz .bad
 test word [terminal_option_mask],512
 jz .ok
 mov ax,terminal_keyboard_io
 push ax
 mov ax,terminal_keymap
 push ax
 push word [csi_terminal_id]
 mov ax,terminal_keyboard_path
 push ax
 call _keymap_dos_read
 add sp,8
 mov [terminal_keyboard_status],ax
 or ax,ax
 jnz .bad
.ok:
 xor ax,ax
 jmp .done
.bad:
 mov ax,9
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Original automatic selection reads BDA0496 bit4. Manual enhanced mode is an
; explicit maintained override for BIOSes whose installed-keyboard flag is bad.
terminal_select_keyboard_bios:
 mov byte [keyboard_bios_mode],0
 cmp word [terminal_keyboard_bios_selection],0
 je .standard
 cmp word [terminal_keyboard_bios_selection],1
 jne .automatic
 mov byte [keyboard_bios_mode],0x10
 mov ax,0x10
 ret
.automatic:
 jmp keyboard_detect_bios_mode
.standard:
 xor ax,ax
 ret

; Use original terminal-style acquisition, retaining keypad/E0 distinctions.
; Alternate low-E0 Enter/slash representations are maintained compatibility
; aliases to the corresponding proved high-E0 keypad identities.
terminal_read_key:
 push bp
 push si
 push di
 push es
 call keyboard_read
 cmp ax,0x1ce0
 je .enter
 cmp ax,0x35e0
 je .slash
 jmp .done
.enter:
 mov ax,0xe00d
 jmp .done
.slash:
 mov ax,0xe02f
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Populate proved slot numbers with source-owned modern network bindings.
; Common defaults work with the supported ANSI and VT220 display profiles;
; importing an explicit KBD can replace each byte, including CR/BS/Tab.
terminal_initialize_keymap:
 mov ax,terminal_keymap
 jmp terminal_build_keymap
; AX caller-owned948-byte near destination. Same maintained defaults; no
; global keymap mutation when staging a new profile. AX0 success/1 bad extent.
terminal_build_keymap:
 push bp
 push si
 push di
 push es
 push ds
 pop es
 cld
 or ax,ax
 jz .bad
 cmp ax,65536-948
 ja .bad
 mov bp,ax
 mov di,ax
 xor ax,ax
 mov cx,948
 rep stosb
 mov si,keyboard_network_defaults
.binding:
 xor ax,ax
 lodsb
 cmp al,0xff
 je .ok
 cmp al,79
 jae .bad
 mov bx,12
 mul bx
 mov di,bp
 add di,ax
 mov cx,12
.byte:
 lodsb
 stosb
 or al,al
 jz .binding
 loop .byte
.bad:
 mov ax,1
 jmp .done
.ok:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

SEGMENT _DATA public class=DATA use16
global terminal_keyboard_status,terminal_keyboard_io
terminal_keyboard_status: dw 0
terminal_keyboard_io: times 14 db 0
keyboard_network_defaults:
 db 0,'*',0              ; Numeric keypad operators and Enter
 db 1,'-',0
 db 2,'+',0
 db 3,'.',0
 db 4,'/',0
 db 5,13,0
 db 6,9,0                 ; Tab
 db 7,27,'[Z',0           ; Backtab
 db 8,27,'[2~',0          ; Insert
 db 9,27,'[3~',0          ; Delete
 db 10,8,0               ; Backspace
 db 11,27,'[1;5H',0       ; Ctrl-Home
 db 12,27,'[1;5F',0       ; Ctrl-End
 db 13,27,'[5~',0         ; Page Up
 db 14,27,'[6~',0         ; Page Down
 db 15,127,0             ; DEL/backspace variant
 db 16,27,'OP',0         ; F1..F12
 db 17,27,'OQ',0
 db 18,27,'OR',0
 db 19,27,'OS',0
 db 20,27,'[15~',0
 db 21,27,'[17~',0
 db 22,27,'[18~',0
 db 23,27,'[19~',0
 db 24,27,'[20~',0
 db 25,27,'[21~',0
 db 26,27,'[23~',0
 db 27,27,'[24~',0
 db 28,'0',0             ; Numeric keypad0..9
 db 29,'1',0
 db 30,'2',0
 db 31,'3',0
 db 32,'4',0
 db 33,'5',0
 db 34,'6',0
 db 35,'7',0
 db 36,'8',0
 db 37,'9',0
 db 38,27,'[1;2P',0      ; Shift-F1..F12
 db 39,27,'[1;2Q',0
 db 40,27,'[1;2R',0
 db 41,27,'[1;2S',0
 db 42,27,'[15;2~',0
 db 43,27,'[17;2~',0
 db 44,27,'[18;2~',0
 db 45,27,'[19;2~',0
 db 46,27,'[20;2~',0
 db 47,27,'[21;2~',0
 db 48,27,'[23;2~',0
 db 49,27,'[24;2~',0
 db 50,27,'[A',0         ; Enhanced navigation bank
 db 51,27,'[B',0
 db 52,27,'[D',0
 db 53,27,'[C',0
 db 54,27,'[2~',0
 db 55,27,'[3~',0
 db 56,27,'[H',0
 db 57,27,'[F',0
 db 58,27,'[5~',0
 db 59,27,'[6~',0
 db 60,27,'[1;5P',0      ; Ctrl-F1..F12
 db 61,27,'[1;5Q',0
 db 62,27,'[1;5R',0
 db 63,27,'[1;5S',0
 db 64,27,'[15;5~',0
 db 65,27,'[17;5~',0
 db 66,27,'[18;5~',0
 db 67,27,'[19;5~',0
 db 68,27,'[20;5~',0
 db 69,27,'[21;5~',0
 db 70,27,'[23;5~',0
 db 71,27,'[24;5~',0
 db 72,27,'[A',0         ; Up/Down/Left/Right
 db 73,27,'[B',0
 db 74,27,'[D',0
 db 75,27,'[C',0
 db 76,27,'[H',0         ; Home/End
 db 77,27,'[F',0
 db 78,13,0              ; Enter
 db 0xff
