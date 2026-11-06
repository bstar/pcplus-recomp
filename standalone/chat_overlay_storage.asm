; Fixture-owned existing scratch storage, not an allocation by the loader.
BITS 16
CPU 8086
SEGMENT CHAT_SCRATCH public align=16 class=FAR_DATA use16
GROUP CHAT_STORAGE CHAT_SCRATCH
global _chat_scratch
_chat_scratch: resb 63032
%ifdef CHAT_PROXY
SEGMENT PROXY_CODE public align=16 class=FARCODE use16
GROUP CHAT_PROXY_GROUP PROXY_CODE
%endif
