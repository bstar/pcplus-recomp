; Diagnostic-only separation: keep the candidate bank beyond a near CALL's
; reach from the ordinary DOS runtime. Never included in a terminal package.
BITS 16
CPU 8086
SEGMENT LINE_PORT_PAD public align=16 class=PADCODE use16
 times 65536 db 0xcc
