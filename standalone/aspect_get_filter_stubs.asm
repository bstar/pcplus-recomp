; Diagnostic only: linked GET filter runs; other GET service stubs never run.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _get_filter_word
extern aspect_get_numeric_filter
_get_filter_word:
 push bp
 mov bp,sp
 lea ax,[bp+4]
 push ax
 call aspect_get_numeric_filter
 add sp,2
 pop bp
 ret
global aspect_get_bell
aspect_get_bell:
 inc word [_get_filter_bells]
 ret
%macro service 1
global %1
%1:
%endmacro
service aspect_dispatch_read
service aspect_get_read_position
service aspect_get_read_attribute
service aspect_get_read_width
service aspect_get_string_destination
service aspect_get_integer_destination
service aspect_get_long_destination
service aspect_get_float_destination
service aspect_get_optional
service aspect_get_integer_text
service aspect_get_long_text
service aspect_get_float_text
service aspect_get_field
service aspect_get_cursor
service aspect_get_set_cursor
service aspect_get_cancel_pending
service aspect_get_cancel_dispatch
service aspect_get_commit_string
service aspect_get_parse_integer
service aspect_get_parse_long
service aspect_get_parse_float
service aspect_get_copy
service aspect_get_string_filter
 ret
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
%macro variable 1
global %1
%1: dw 0
%endmacro
variable _get_filter_bells
variable aspect_get_destination_kind
variable aspect_get_scratch
variable aspect_get_row
variable aspect_get_column
variable aspect_get_attribute
variable aspect_get_wrap
variable aspect_get_rows
variable aspect_get_columns
variable aspect_get_cursor_origin
variable aspect_get_failure
variable aspect_get_keys_disabled
variable aspect_get_float_text_pointer
variable aspect_get_float_result
