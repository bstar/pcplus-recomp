; Exact original CS774e..775a (end exclusive).
BITS 16
CPU 8086
%ifdef PROGRAM_SOUND_OMF
SEGMENT _TEXT public class=CODE use16
global sound_bell
extern sound_tone
%else
ORG 0x774e
%define sound_tone 0x7722
%endif
sound_bell:
 mov ax,220
 push ax
 mov ax,15
 push ax
 call sound_tone
 ret
