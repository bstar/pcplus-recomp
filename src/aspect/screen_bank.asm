; Native near command/operand ABIs across SCRIPT_SCREEN_CODE and resident CS.
BITS 16
CPU 8086
%ifndef SCREEN_BANK_OVERLAY_ONLY
SEGMENT _TEXT public class=CODE use16
%macro ENTRY 2
 %ifdef SCREEN_BANK_ROOT_ONLY
 extern screen_%1_far
 %endif
 global aspect_screen_%1_entry
 aspect_screen_%1_entry: call far screen_%1_far
 ret
%endmacro
ENTRY box,0
ENTRY clear,0
ENTRY locate,0
ENTRY scroll,0
ENTRY getvattr,0
ENTRY putvattr,0
ENTRY home,0
extern aspect_string_bounded_integer,aspect_string_byte_operand
extern aspect_string_option_flag,aspect_string_store_integer
global screen_bounded_resident,screen_store_resident
global screen_byte_resident,screen_option_resident
screen_bounded_resident:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 call aspect_string_bounded_integer
 mov sp,bp
 pop bp
 retf
screen_store_resident:
 push bp
 mov bp,sp
 push word [bp+8]
 call aspect_string_store_integer
 mov sp,bp
 pop bp
 retf
screen_byte_resident: call aspect_string_byte_operand
 retf
screen_option_resident: call aspect_string_option_flag
 retf
extern _runtime_set_error,aspect_abort
global _screen_runtime_failure
_screen_runtime_failure:
 mov bx,sp
 push word [bx+4]
 call _runtime_set_error
 add sp,2
 jmp aspect_abort
%ifdef ASPECT_SCREEN_PARENT
extern _aspect_render_request,_aspect_render_client_check
global _screen_wire_request,_screen_client_check
_screen_wire_request:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 call _aspect_render_request
 mov sp,bp
 pop bp
 retf
_screen_client_check: call _aspect_render_client_check
 retf
%endif
%endif

%ifndef SCREEN_BANK_ROOT_ONLY
SEGMENT SCRIPT_SCREEN_CODE public align=16 class=FARCODE use16
%ifdef SCREEN_BANK_OVERLAY_ONLY
extern screen_bounded_resident,screen_store_resident
extern screen_byte_resident,screen_option_resident
%endif
extern _runtime_screen_enter
extern aspect_screen_box,aspect_screen_clear,aspect_screen_locate
extern aspect_screen_scroll,aspect_screen_getvattr,aspect_screen_putvattr
extern _runtime_screen_scroll,_runtime_screen_box,_runtime_screen_clear
extern _runtime_screen_reset_attribute,_runtime_screen_locate,_runtime_screen_read
extern _runtime_screen_write,_runtime_screen_home
%macro FAR_ENTRY 1
 global screen_%1_far
 screen_%1_far:
 call _runtime_screen_enter
 call aspect_screen_%1
 retf
%endmacro
FAR_ENTRY box
FAR_ENTRY clear
FAR_ENTRY locate
FAR_ENTRY scroll
FAR_ENTRY getvattr
FAR_ENTRY putvattr
global screen_home_far
screen_home_far:
 call _runtime_screen_enter
 call _runtime_screen_home
 retf
global screen_bounded_integer,screen_byte_operand,screen_option_flag,screen_store_integer
screen_bounded_integer:
 call far screen_bounded_resident
 ret 4
screen_byte_operand: call far screen_byte_resident
 ret
screen_option_flag: call far screen_option_resident
 ret
screen_store_integer: call far screen_store_resident
 ret 2
; Mirror native callee-cleanup arguments to ordinary bank-local C cdecl.
%macro PLATFORM 3
 global aspect_screen_%1
 aspect_screen_%1:
 push bp
 mov bp,sp
 %assign %%arg %3-1
 %rep %3
 push word [bp+4+2*%%arg]
 %assign %%arg %%arg-1
 %endrep
 call _runtime_screen_%2
 mov sp,bp
 pop bp
 %if %3
 ret %3*2
 %else
 ret
 %endif
%endmacro
PLATFORM scroll_rectangle,scroll,4
PLATFORM draw_box,box,3
PLATFORM read_video_byte,read,1
PLATFORM write_video_byte,write,2
PLATFORM reset_attribute,reset_attribute,0
PLATFORM clear_home,clear,0
global aspect_screen_set_cursor
aspect_screen_set_cursor:
 push dx
 push ax
 call _runtime_screen_locate
 add sp,4
 ret
%endif
%ifndef SCREEN_BANK_OVERLAY_ONLY
SEGMENT _DATA public class=DATA use16
global _runtime_screen_values
global aspect_screen_normal,aspect_screen_configured_wide,aspect_screen_physical_rows
global aspect_screen_physical_last_row,aspect_screen_physical_last_column,aspect_screen_physical_stride
_runtime_screen_values:
aspect_screen_normal: dw 0
aspect_screen_configured_wide: dw 0
aspect_screen_physical_rows: dw 0
aspect_screen_physical_last_row: dw 0
aspect_screen_physical_last_column: dw 0
aspect_screen_physical_stride: dw 0
%endif
