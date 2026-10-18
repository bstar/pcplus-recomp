; State for actual recovered BIOS keyboard routines; application queue disabled.
; No reconstructed queue producer or debugging UI is claimed here.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_quit,terminal_exit_code
global keyboard_debug_callback
keyboard_debug_callback:
 ; This path is disabled by debug_gate=-1. If enabled accidentally, fail visibly.
 mov word [terminal_exit_code],4
 mov word [terminal_quit],1
 ret
SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA
global keyboard_queue_count,keyboard_queue_index,keyboard_queue_active
global keyboard_queue_peek,keyboard_queue_values,keyboard_bios_mode,keyboard_debug_gate
keyboard_queue_count: dw 0
keyboard_queue_index: dw 0
keyboard_queue_active: dw 0
keyboard_debug_gate: dw -1
; Keep the original twelve-byte separation; do not invent producer semantics.
keyboard_queue_peek: times 6 dw 0
keyboard_queue_values: times 64 dw 0
keyboard_bios_mode: db 0
