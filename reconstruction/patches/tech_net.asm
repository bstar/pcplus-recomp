; Datastorm TECH_NET.DTP replaces the conditional branch at file offset 96067.
; Target: exact PCPLUS.EXE 2.01 baseline, old bytes 7D 03.
; This skips the CSI q handler's additional-byte consumption loop.
BITS 16
CPU 8086
ORG 0xea93
    nop
    nop
