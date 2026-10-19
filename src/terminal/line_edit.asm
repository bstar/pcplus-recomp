; Resident near API and typed callbacks for the far line-edit controller.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern line_insert_controller_far,line_delete_controller_far
extern line_alternate_controller_far,line_wait_controller_far
extern csi_insert_line,csi_delete_line,terminal_poll_io,terminal_tick_low,uart_receive_byte
global csi_service_d668,csi_service_d73c,csi_service_daf2,terminal_wait_control_n
csi_service_d668:
 call far line_insert_controller_far
 ret
csi_service_d73c:
 call far line_delete_controller_far
 ret
csi_service_daf2:
 call far line_alternate_controller_far
 ret
terminal_wait_control_n:
 call far line_wait_controller_far
 ret

; No arguments or cleanup: preserve each target's register/FLAGS contract.
global line_native_insert_far,line_native_delete_far,line_poll_far,line_tick_far,line_receive_far
line_native_insert_far:
 call csi_insert_line
 retf
line_native_delete_far:
 call csi_delete_line
 retf
line_poll_far:
 call terminal_poll_io
 retf
line_tick_far:
 call terminal_tick_low
 retf
line_receive_far:
 call uart_receive_byte
 retf

SEGMENT _DATA public class=DATA use16
global terminal_ansi_wait_active,terminal_ansi_wait_cancel,terminal_ansi_wait_timed_out
terminal_ansi_wait_active: dw 0
terminal_ansi_wait_cancel: dw 0
terminal_ansi_wait_timed_out: dw 0
