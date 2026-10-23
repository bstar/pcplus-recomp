; One producer/consumer state: native mouse events are the keyboard queue.
BITS 16
CPU 8086
SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA
%macro wordvar 1
 global %1,_%1
 %1:
 _%1: dw 0
%endmacro
wordvar mouse_scale_x
wordvar mouse_scale_y
wordvar mouse_present
wordvar mouse_flags
wordvar mouse_motion_x
wordvar mouse_motion_y
wordvar mouse_base_x
wordvar mouse_base_y
global keyboard_queue_active,keyboard_queue_count,keyboard_queue_index
keyboard_queue_active:
wordvar mouse_button_pending
keyboard_queue_count:
wordvar mouse_count
keyboard_queue_index:
wordvar mouse_code
%ifdef MOUSE_EXTERNAL_BIOS
extern keyboard_bios_mode
global keyboard_debug_gate
%else
global keyboard_bios_mode,_keyboard_bios_mode,keyboard_debug_gate
keyboard_bios_mode:
_keyboard_bios_mode: db 0
%endif
keyboard_debug_gate: dw -1
SEGMENT _TEXT public class=CODE use16
%ifndef TERMINAL_MOUSE
global keyboard_debug_callback
keyboard_debug_callback:
 ; The unrelated debug UI is unimplemented; its disabled gate cannot succeed.
 mov ax,0x4cf1
 int 0x21
%endif
