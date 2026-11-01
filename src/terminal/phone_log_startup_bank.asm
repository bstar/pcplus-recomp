; Optional startup entry in the existing logger CS; no resident trampoline.
BITS 16
CPU 8086
SEGMENT PHONE_LOG_CODE public align=1 class=FARCODE use16
GROUP PHONE_LOG_GROUP PHONE_LOG_CODE
%include "far_bridge.inc"
FAR_CDECL_ENTRY _phone_log_startup_owner,0
