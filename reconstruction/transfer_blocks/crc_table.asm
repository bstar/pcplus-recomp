; Re-authored mathematical CCITT polynomial table; matches original DS39fc.
BITS 16
CPU 8086
%ifdef TRANSFER_BLOCKS_OMF
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global transfer_crc_table
%endif
transfer_crc_table:
%assign index 0
%rep 256
 %assign crc index << 8
 %rep 8
  %if crc & 0x8000
   %assign crc ((crc << 1) ^ 0x1021) & 0xffff
  %else
   %assign crc (crc << 1) & 0xffff
  %endif
 %endrep
 dw crc
 %assign index index+1
%endrep
