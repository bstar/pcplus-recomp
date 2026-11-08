; Real recovered final abort and ten-byte dispatcher environment; only the
; optional position-reporting services remain explicit unused diagnostics.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern session_setjmp,aspect_dispatch_argument,_owner_unexpected
global _owner_dispatch_checkpoint
; Tail call is essential: the saved IP must be the C caller's continuation,
; not an adapter continuation whose second return address can be overwritten.
_owner_dispatch_checkpoint: jmp session_setjmp
global aspect_abort_tell,aspect_abort_format,aspect_abort_print
aspect_abort_tell:
aspect_abort_format:
aspect_abort_print: jmp _owner_unexpected
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_dispatch_argument,aspect_abort_display_position,aspect_abort_format_string
global _owner_dispatch_context
aspect_dispatch_argument:
_owner_dispatch_context: times 10 db 0
aspect_abort_display_position: dw 0
aspect_abort_format_string: db 0
