; Exact original CS7722..774d (end exclusive).
BITS 16
CPU 8086
%ifdef PROGRAM_SOUND_OMF
SEGMENT _TEXT public class=CODE use16
global sound_tone
extern sound_divisor,sound_on,sound_off,sound_delay
%else
ORG 0x7722
%define sound_divisor 0x7fae
%define sound_on 0x7fa7
%define sound_off 0x7fa0
%define sound_delay 0x6b72
%endif
%include "encodings.inc"
sound_tone:
 mov_load bx,sp
 mov cx,[bx+4]
 mov bx,[bx+2]
 mov ax,10
 mul bx
 push ax
 mov al,0xb6
 out 0x43,al
 mov dx,0x12
 mov ax,0x34de
 div cx
 mov_load bx,ax
 call sound_divisor
 call sound_on
 call sound_delay
 call sound_off
 ret 4
