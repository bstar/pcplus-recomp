; Source-owned singleton matcher state. Copy validated PRM response bytes here.
BITS 16
CPU 8086
SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA
global modem_response_slots,modem_response_cursors,modem_response_available,modem_response_input_byte
modem_response_slots: times 176 db 0
modem_response_cursors: times 11 dw 0
modem_response_available: dw 0
modem_response_input_byte: db 0
