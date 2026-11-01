; Optional producer entries in the existing logger bank; no resident thunk.
BITS 16
CPU 8086
SEGMENT PHONE_LOG_CODE public align=1 class=FARCODE use16
GROUP PHONE_LOG_GROUP PHONE_LOG_CODE
%include "far_bridge.inc"
%define PHONE_LIFECYCLE_ENTRY FAR_CDECL_ENTRY
%include "phone_log_lifecycle_abi.inc"
