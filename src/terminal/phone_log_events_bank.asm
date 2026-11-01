; Optional zero-argument session hooks in the logger CS.
BITS 16
CPU 8086
SEGMENT PHONE_LOG_CODE public align=1 class=FARCODE use16
GROUP PHONE_LOG_GROUP PHONE_LOG_CODE
%include "far_bridge.inc"
FAR_CDECL_ENTRY _terminal_phone_log_events_ready,0
FAR_CDECL_ENTRY _terminal_phone_log_events_connected,0
FAR_CDECL_ENTRY _terminal_phone_log_events_disconnected,0
FAR_CDECL_ENTRY _terminal_phone_log_events_shutdown,0
