; Exact overlay16 FROMDDIR and MONO WORD getters. The parent supplies live
; retained origin and physical display state; the child supplies owned replies.
BITS 16
CPU 8086
%ifdef ASPECT_STATE_FLAT
%define state_fromddir 0x4afe
%define state_mono 0x7a86
%elifdef ASPECT_STATE_PARENT
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern _aspect_fromddir,_display_rows_mono
%define state_fromddir _aspect_fromddir
%define state_mono _display_rows_mono
%else
SEGMENT _TEXT public class=CODE use16
extern _runtime_terminal_values
%define state_fromddir (_runtime_terminal_values+18)
%define state_mono (_runtime_terminal_values+20)
%endif
%macro GETTER 4
%ifdef ASPECT_STATE_FLAT
%if ASPECT_STATE_UNIT=%1
ORG %2
%else
%define OMIT_GETTER
%endif
%else
global aspect_state_%3
%endif
%ifndef OMIT_GETTER
aspect_state_%3:
 mov ax,[%4]
 ret
%endif
%undef OMIT_GETTER
%endmacro
GETTER 0,0xda18,fromddir,state_fromddir
GETTER 1,0xda24,mono,state_mono
