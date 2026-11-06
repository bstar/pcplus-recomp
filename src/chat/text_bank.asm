; Separate CS for the DOS component fixture. Module integration supplies its
; own code group; no near trampoline, state or data allocation is introduced.
BITS 16
CPU 8086
SEGMENT CHAT_TEXT_CODE public align=16 class=FARCODE use16
GROUP CHAT_TEXT_GROUP CHAT_TEXT_CODE
