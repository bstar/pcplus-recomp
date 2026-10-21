; All nonlocal fault unwinds run with the native _TEXT CS active.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_transfer_service,transfer_maybe_unwind,uart_receive_byte
GLOBAL terminal_upload_startup_service_far,terminal_upload_startup_receive_far
terminal_upload_startup_service_far:
 call terminal_transfer_service
 call transfer_maybe_unwind
 retf
terminal_upload_startup_receive_far:
 call uart_receive_byte
 retf
