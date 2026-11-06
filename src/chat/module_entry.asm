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
%ifdef CHAT_REDISPLAY
 dw 0x0106,50,480
%elifdef CHAT_FOREGROUND_TEXT
 dw 0x0104,50,476
%elifdef CHAT_TIMING
 dw 0x0103,50,448
%elifdef CHAT_TEXT
 dw 0x0102,50,430
%elifdef CHAT_PRESENTATION
 dw 0x0101,50,362
%else
 dw 0x0100,50,358
%endif
