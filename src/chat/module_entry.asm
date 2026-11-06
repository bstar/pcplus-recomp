; DOS MZ overlay. No PSP, CRT, own stack, data initialization or process entry.
BITS 16
CPU 8086
SEGMENT CHAT_CODE public align=16 class=FARCODE use16
GROUP CHAT_GROUP CHAT_CODE
extern _chat_module_dispatch
global chat_overlay_entry
global _small_code_
_small_code_ equ 0
chat_overlay_entry:
 jmp far _chat_module_dispatch
 db 'LOCCHAT',0
%ifdef CHAT_PRESENTATION
 dw 0x0101,50,362
%else
 dw 0x0100,50,358
%endif
