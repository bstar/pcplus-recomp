; Diagnostic call sequence corresponding to the recovered Chat Alt-F6 branch.
; This is a harness caller, not another claimed original byte recovery.
BITS 16
CPU 8086
ORG 0xf800
call 0x6b5a
call 0xd830
call 0x6b42
call 0x6dca
ret
