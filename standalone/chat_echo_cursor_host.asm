; Diagnostic adapter for the exact production cursor register-service ABI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern screen_set_cursor
global terminal_key_position_far
terminal_key_position_far:
 call screen_set_cursor
 retf
