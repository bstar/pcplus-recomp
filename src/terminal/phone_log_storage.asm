; Initialized queue precedes DOS/PROGRAM's uninitialized far screen buffers.
; Keep the exact 666-byte C owner layout; the first-use cookie clears it once.
BITS 16
CPU 8086
SEGMENT PHONE_LOG_STORAGE public align=16 class=PHONE_DATA use16
global _phone_log_queue_store,phone_log_queue_storage_end
_phone_log_queue_store:
dw 0x514c
times 664 db 0
phone_log_queue_storage_end:
