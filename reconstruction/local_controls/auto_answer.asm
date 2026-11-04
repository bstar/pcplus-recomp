; Original Auto Answer send053A..0552 and Alt-Y entry0553..0565;44 exact bytes.
; REA ev_a7ef70db22c1b1b74d9213ae7e7955ddd9c4060cf25635f706660793183ed0e9.
; DS=SS, cdecl near. Send answer-on; retain local echo and restore pacing.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef AUTO_ANSWER_OMF
SEGMENT AUTO_ANSWER_NATIVE_CODE public align=16 class=FARCODE use16
extern modem_send_pacing_units,modem_answer_on_string,modem_send_original
extern auto_answer_message_pointer,auto_answer_notice,sound_information
global local_auto_answer_send_053a,local_auto_answer_0553
%else
ORG 0x053a
%define modem_send_pacing_units 0x1d68
%define modem_answer_on_string 0x1c16
%define modem_send_original 0x48cc
%define auto_answer_message_pointer 0x2078
%define auto_answer_notice 0x31bb
%define sound_information 0x3778
%endif
local_auto_answer_send_053a:
 push si
 mov si,[modem_send_pacing_units]
 mov word [modem_send_pacing_units],50
 mov ax,modem_answer_on_string
 push ax
 call modem_send_original
 pop bx
 mov [modem_send_pacing_units],si
 pop si
 ret
local_auto_answer_0553:
 call sound_information
 mov ax,36
 push ax
 push word [auto_answer_message_pointer]
 call auto_answer_notice
 pop bx
 pop bx
 jmp near local_auto_answer_send_053a
