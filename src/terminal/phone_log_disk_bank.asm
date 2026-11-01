; Main-loop entry and checked existing MODEM notice callback, no new resident
; code service. Only this tiny near helper forwards a C pointer in SI.
BITS 16
CPU 8086
SEGMENT PHONE_LOG_CODE public align=1 class=FARCODE use16
GROUP PHONE_LOG_GROUP PHONE_LOG_CODE
%include "far_bridge.inc"
FAR_CDECL_ENTRY _terminal_phone_log_disk_poll,0
FAR_CDECL_ENTRY _phone_log_disk_before_program,0
global _phone_log_disk_notify
extern connection_notice_resident
_phone_log_disk_notify:
 push bp
 mov bp,sp
 push si
 mov si,[bp+4]
 call far connection_notice_resident
 pop si
 pop bp
 ret

SEGMENT _TEXT public class=CODE use16
extern terminal_capture_before_program
global phone_capture_before_program_resident
phone_capture_before_program_resident:
 call terminal_capture_before_program
 retf
