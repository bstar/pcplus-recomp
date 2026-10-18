; Public protocol constants, reconstructed from observed original replies.
; DA IDs2..11 match original table. IDs0/1 are unsupported empty placeholders;
; their original null pointers reference unrelated DS:0 content and are not copied.
BITS 16
CPU 8086
SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA
%macro string 2+
 global %1
 %1: db %2,0
%endmacro
string csi_attributes_prefix,27,'[?'
string csi_status_ok,27,'[0n'
string csi_cursor_prefix,27,'['
string csi_printer_ok,27,'[?10n'
string csi_printer_unavailable,27,'[?13n'
global csi_attributes_table,csi_report_buffer
csi_attributes_table:
 dw empty,empty,vt100,vt102,vt220,vt320,vt100,vt100,vt52,wyse,vt100,vt220
empty: db 0
vt100: db '1;2',0
vt102: db '6',0
vt220: db '62;2',0
vt320: db '63;2',0
vt52: db '1;0',0
wyse: db '7;5;1',0
csi_report_buffer: times 7 db 0
