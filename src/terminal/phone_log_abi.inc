; Explicit caller-cleaned word counts; no change to DS=SS.
PHONE_ENTRY _phone_log_queue_initialize,0
PHONE_ENTRY _phone_log_queue_configure,2
PHONE_ENTRY _phone_log_queue_start,5
PHONE_ENTRY _phone_log_queue_end,3
PHONE_ENTRY _phone_log_queue_poll,0
PHONE_ENTRY _phone_log_queue_retry,0
PHONE_ENTRY _phone_log_queue_inspect,1
PHONE_ENTRY _phone_log_decode_enabled,3
PHONE_ENTRY _phone_log_read_stamp,1
PHONE_ENTRY _phone_log_stamp_seconds,2
; Compiler register ABI, all arguments fit registers (no stack forwarding).
PHONE_REGISTER phone_capture_attributes_service_,capture_fs_attributes_
PHONE_REGISTER phone_capture_create_service_,capture_fs_create_
PHONE_REGISTER phone_capture_open_service_,capture_fs_open_append_
PHONE_REGISTER phone_capture_seek_service_,capture_fs_seek_end_
PHONE_REGISTER phone_capture_write_service_,capture_fs_write_
PHONE_REGISTER phone_capture_close_service_,capture_fs_close_
PHONE_REGISTER phone_intdos_service_,intdos_
; _dos_write's far buffer consumes two registers; its final near written-count
; pointer is a callee-cleaned stack word. It needs its own exact adapter.
PHONE_STACK phone_dos_write_service_,_dos_write_
