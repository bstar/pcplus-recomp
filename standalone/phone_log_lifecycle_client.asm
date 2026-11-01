; Diagnostic-only lifecycle client and explicit END-refusal boundary model.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%define PHONE_LIFECYCLE_ENTRY NEAR_CDECL_ENTRY
%include "phone_log_lifecycle_abi.inc"
; Three copied words: DWORD generation followed by near timestamp pointer.
NEAR_CDECL_SERVICE _lifecycle_queue_end,_lifecycle_queue_end_fault,3
global _lifecycle_real_queue_end
extern _phone_log_queue_end_far
_lifecycle_real_queue_end:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call far _phone_log_queue_end_far
 lea sp,[bp]
 pop bp
 ret
SEGMENT PHONE_LOG_CODE public align=1 class=FARCODE use16
FAR_CDECL_SERVICE _lifecycle_queue_end,_lifecycle_queue_end_fault,3
