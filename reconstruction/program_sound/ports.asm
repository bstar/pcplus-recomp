; Exact original CS7fa0..7fb7 (end exclusive).
BITS 16
CPU 8086
%ifdef PROGRAM_SOUND_OMF
SEGMENT _TEXT public class=CODE use16
global sound_off,sound_on,sound_divisor
%else
ORG 0x7fa0
%endif
%include "encodings.inc"
sound_off:
 in al,0x61
 and al,0xfc
 out 0x61,al
 ret
sound_on:
 in al,0x61
 or al,3
 out 0x61,al
 ret
sound_divisor:
 mov_load al,bl
 out 0x42,al
 mov_load al,bh
 out 0x42,al
 ret
