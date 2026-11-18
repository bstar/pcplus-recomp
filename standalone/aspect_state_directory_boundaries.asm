; Test-only data/callback boundaries. No original executable input.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global terminal_script_start
extern _state_directory_loader
terminal_script_start:
 jmp _state_directory_loader
SEGMENT _DATA public class=DATA use16
global _aspect_fromddir,_state_directory_before,_state_directory_after
_state_directory_before: dw 0x1357
_aspect_fromddir: dw 0
_state_directory_after: dw 0x2468
SEGMENT STATE_DIRECTORY_SNAPSHOT public class=FAR_DATA use16
global redisplay_snapshot
redisplay_snapshot: times 63000 db 0
