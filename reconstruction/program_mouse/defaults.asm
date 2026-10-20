; Original startup overlay32 DS5dee..5e0b. Facts in defaults.json.
BITS 16
%ifdef PROGRAM_MOUSE_OMF
SEGMENT _DATA public align=16 class=DATA use16
global mouse_enabled,_mouse_enabled,keyboard_queue_peek,_keyboard_queue_peek
global keyboard_queue_values,_keyboard_queue_values
%endif
mouse_enabled:
_mouse_enabled: db 1,1,1,1,1,1
keyboard_queue_peek:
_keyboard_queue_peek: dw 0x4800,0x4d00,0x5000,0x4b00,0x1c0d,0x011b
keyboard_queue_values:
_keyboard_queue_values: dw 0x4800,0x4d00,0x5000,0x4b00,0x000d,0x001b
