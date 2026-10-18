; One owner invocation: native entry establishes its own frame/context and
; loops across blocks. The selected IO adapter owns hardware/file boundaries.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern session_receive,composite_io_reset,composite_test_filename
extern composite_owner_result,composite_prepare_dos,composite_dos_assert
GLOBAL _transfer_composite_run,_transfer_composite_dos_test
_transfer_composite_run:
 push bp
 push bx
 push si
 push di
 push es
 call composite_io_reset
 mov ax,composite_test_filename
 push ax
 call session_receive
 add sp,2
 mov [composite_owner_result],ax
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_transfer_composite_dos_test:
 call composite_prepare_dos
 call _transfer_composite_run
 call composite_dos_assert
 ret
SEGMENT _DATA public class=DATA use16
%include "composite_state.inc"
