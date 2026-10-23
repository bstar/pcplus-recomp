; Exact PCPlus2.01 configurable notice sounds; see provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_SOUND_OMF
SEGMENT _TEXT public class=CODE use16
global sound_error,sound_information
extern sound_enabled,sound_bell,sound_tone
%define short
%else
ORG 0x376d
%define sound_enabled 0x1d40
%define sound_bell 0x774e
%define sound_tone 0x7722
%endif
sound_error:
 cmp word [sound_enabled],byte 0
 jz short .done
 call sound_bell
.done: ret
sound_information:
 cmp word [sound_enabled],byte 0
 jz short .done
 mov ax,440
 push ax
 mov ax,20
 push ax
 call sound_tone
.done: ret
