; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_wait
extern display_scroll
extern display_text
extern display_wait_key
extern display_last_column
extern display_viewport
extern display_wait_message
%define short
%else
ORG 14149
%define display_scroll 28380
%define display_text 27632
%define display_wait_key 25854
%define display_last_column 31358
%define display_viewport 31364
%define display_wait_message 17090
%endif
%include "encodings.inc"
display_wait:
L_3745: mov ax,0x1
L_3748: push ax
L_3749: sub_load ax,ax
L_374b: push ax
L_374c: mov ax,[display_last_column]
L_374f: or ax,[display_viewport]
L_3753: push ax
L_3754: mov ax,0x7
L_3757: push ax
L_3758: call display_scroll
L_375b: push word [display_viewport]
L_375f: mov ax,0xe
L_3762: push ax
L_3763: push word [display_wait_message]
L_3767: call display_text
L_376a: jmp near display_wait_key
