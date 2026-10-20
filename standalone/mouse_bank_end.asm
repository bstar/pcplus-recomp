; Last linker input: delimit all uninitialized near data for assembly startup.
BITS 16
SEGMENT _BSS public align=16 class=BSS use16
global mouse_bank_bss_end
mouse_bank_bss_end:
; Keep near-code pressure comparable to the application. Force the mouse bank
; into a different CS even though this purpose-built parent's UI is small.
SEGMENT _TEXT public class=CODE use16
times 60000 db 0xcc
