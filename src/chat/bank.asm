; Give the opt-in controller fixture a separate aligned retained code group.
; No DGROUP data or resident near-code trampoline is introduced here.
BITS 16
CPU 8086
SEGMENT CHAT_CODE public align=16 class=FARCODE use16
GROUP CHAT_GROUP CHAT_CODE
